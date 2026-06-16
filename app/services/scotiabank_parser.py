"""Parser para estados de cuenta Scotiabank (.xls binario, hoja estado_cta_trj)."""

from __future__ import annotations

import io
import re
import unicodedata
from datetime import datetime
from typing import Any

SCOTIABANK_SHEET = "estado_cta_trj"

FILAS_IGNORAR_GLOSA = {
    "total pagos",
    "total compras",
    "comisiones, otros cargos  y abonos a la",
    "descripcion operacion o cobro",
    "descripción operación o cobro",
    "lugar de operación",
    "lugar de operacion",
}


def _sin_acentos(texto: str) -> str:
    norm = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in norm if not unicodedata.combining(c))


def _normalizar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    texto = str(valor).replace("\n", " ").strip()
    return " ".join(texto.split())


def _texto_celda(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return _normalizar_texto(valor)


def _leer_filas_xls(content: bytes) -> list[list[str]]:
    import xlrd

    libro = xlrd.open_workbook(file_contents=content)
    if SCOTIABANK_SHEET not in libro.sheet_names():
        return []
    hoja = libro.sheet_by_name(SCOTIABANK_SHEET)
    return [[_texto_celda(hoja.cell_value(r, c)) for c in range(hoja.ncols)] for r in range(hoja.nrows)]


def es_estado_cuenta_scotiabank(content: bytes, nombre_archivo: str = "") -> bool:
    nombre = nombre_archivo.lower()
    if "scotiabank" in nombre or "scotia" in nombre:
        return True
    filas = _leer_filas_xls(content)
    if not filas:
        return False
    muestra = " ".join(" ".join(fila) for fila in filas[:15]).lower()
    return "scotiabank" in muestra or (
        "estado de cuenta" in muestra
        and "tarjeta" in muestra
        and ("nacional" in muestra or "internacional" in muestra)
    )


def _detectar_tipo_cuenta(filas: list[list[str]]) -> tuple[str, str]:
    muestra = _sin_acentos(" ".join(" ".join(f) for f in filas[:12])).lower()
    if "internacional" in muestra:
        return "Tarjeta de crédito", "Internacionales"
    if "nacional" in muestra:
        return "Tarjeta de crédito", "Nacionales"
    return "Tarjeta de crédito", None


def _extraer_fecha_referencia(filas: list[list[str]]) -> str | None:
    for fila in filas[:8]:
        for celda in fila:
            match = re.search(r"(\d{2})/(\d{2})/(\d{4})", celda)
            if match:
                d, m, y = match.groups()
                try:
                    datetime(int(y), int(m), int(d))
                    return f"{y}-{m}-{d}"
                except ValueError:
                    continue
    return None


def _es_fila_encabezado(fila: list[str]) -> bool:
    texto = _sin_acentos(" ".join(fila)).lower()
    return "fecha oper" in texto and ("descrip" in texto or "operacion o cobro" in texto)


def _mapear_columnas(fila: list[str]) -> dict[str, int]:
    columnas: dict[str, int] = {}
    for idx, celda in enumerate(fila):
        if not celda:
            continue
        norm = _sin_acentos(celda).lower()
        if "fecha oper" in norm:
            columnas["fecha"] = idx
        elif "descrip" in norm and "oper" in norm:
            columnas["glosa"] = idx
        elif "monto us" in norm:
            columnas["monto"] = idx
        elif "monto oper" in norm and "cobro" in norm:
            columnas["monto"] = idx
        elif "monto total a pagar" in norm and "monto" not in columnas:
            columnas["monto"] = idx
        elif "referencia" in norm or "codigo referencia" in norm:
            columnas["referencia"] = idx
        elif norm == "pais" or norm == "país":
            columnas["pais"] = idx
        elif norm == "ciudad":
            columnas["ciudad"] = idx
        elif "lugar de oper" in norm:
            columnas["lugar"] = idx
    return columnas


def _completar_fecha(fecha: str, fecha_referencia: str | None) -> str | None:
    fecha = fecha.strip()
    if not fecha or fecha in {"00/00", "0/0"}:
        return None

    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", fecha)
    if match:
        d, m, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    match = re.match(r"^(\d{1,2})/(\d{1,2})$", fecha)
    if not match:
        return None

    d, m = match.groups()
    dia, mes = int(d), int(m)
    if not fecha_referencia:
        anio = datetime.now().year
    else:
        anio = int(fecha_referencia[:4])
        mes_ref = int(fecha_referencia[5:7])
        if mes > mes_ref + 6:
            anio -= 1
        elif mes < mes_ref - 6:
            anio += 1

    try:
        datetime(anio, mes, dia)
    except ValueError:
        return None
    return f"{anio}-{mes:02d}-{dia:02d}"


def _es_fila_movimiento(fila: list[str], columnas: dict[str, int]) -> bool:
    glosa = fila[columnas["glosa"]] if "glosa" in columnas and columnas["glosa"] < len(fila) else ""
    fecha = fila[columnas["fecha"]] if "fecha" in columnas and columnas["fecha"] < len(fila) else ""
    monto = fila[columnas["monto"]] if "monto" in columnas and columnas["monto"] < len(fila) else ""

    if not glosa or not fecha or not monto:
        return False

    glosa_l = _sin_acentos(glosa).lower()
    if glosa_l in FILAS_IGNORAR_GLOSA or glosa_l.startswith("total "):
        return False
    if fecha in {"00/00", "0/0"}:
        return False
    if not re.search(r"\d", monto):
        return False
    return True


def _fila_a_registro(
    fila: list[str],
    columnas: dict[str, int],
    fila_origen: int,
    subtipo: str | None,
    fecha_referencia: str | None,
) -> dict[str, str]:
    def valor(clave: str) -> str:
        idx = columnas.get(clave)
        if idx is None or idx >= len(fila):
            return ""
        return fila[idx]

    glosa = valor("glosa")
    fecha_raw = valor("fecha")
    monto_raw = valor("monto")
    fecha_iso = _completar_fecha(fecha_raw, fecha_referencia)

    registro: dict[str, str] = {
        "Descripción Operación o Cobro": glosa,
        "_hoja_origen": SCOTIABANK_SHEET,
        "_fila_origen": str(fila_origen),
    }

    if fecha_iso:
        registro["fecha"] = fecha_iso
        registro["Fecha Operación"] = fecha_iso
    elif fecha_raw:
        registro["Fecha Operación"] = fecha_raw

    if subtipo == "Internacionales":
        registro["Monto US$"] = monto_raw
        if valor("ciudad"):
            registro["Ciudad"] = valor("ciudad")
        if valor("pais"):
            registro["País"] = valor("pais")
        if valor("referencia"):
            registro["Número Referencia Internacional"] = valor("referencia")
    else:
        registro["Monto Operación o Cobro"] = monto_raw
        if valor("lugar"):
            registro["Lugar de Operación"] = valor("lugar")
        if valor("referencia"):
            registro["Código Referencia"] = valor("referencia")

    return registro


def parsear_estado_cuenta_scotiabank(content: bytes) -> tuple[dict[str, str | None], list[dict[str, str]]]:
    filas = _leer_filas_xls(content)
    if not filas:
        return {}, []

    producto, subtipo = _detectar_tipo_cuenta(filas)
    fecha_referencia = _extraer_fecha_referencia(filas)
    metadata = {
        "banco_inferido": "SCOTIABANK",
        "tipo_fuente_inferido": producto,
        "subtipo_movimiento": subtipo,
        "fecha_referencial": fecha_referencia,
    }

    movimientos: list[dict[str, str]] = []
    columnas: dict[str, int] = {}

    for idx, fila in enumerate(filas, start=1):
        if _es_fila_encabezado(fila):
            columnas = _mapear_columnas(fila)
            if "fecha" in columnas and "glosa" in columnas and "monto" in columnas:
                continue
            columnas = {}
            continue

        if not columnas:
            continue
        if not _es_fila_movimiento(fila, columnas):
            continue

        registro = _fila_a_registro(fila, columnas, idx, subtipo, fecha_referencia)
        if registro.get("fecha") and registro.get("Descripción Operación o Cobro"):
            movimientos.append(registro)

    return metadata, movimientos


def construir_hoja_inspeccion(movimientos: list[dict[str, str]]) -> dict:
    columnas = []
    if movimientos:
        columnas = [k for k in movimientos[0].keys() if not k.startswith("_")]
    return {
        "nombre": SCOTIABANK_SHEET,
        "filas_totales": len(movimientos),
        "columnas_totales": len(columnas),
        "rango_usado": f"A1:Z{max(len(movimientos), 1)}",
        "fila_encabezado_probable": 1,
        "columnas_detectadas": columnas,
        "filas_ejemplo": [{k: v for k, v in m.items() if not k.startswith("_")} for m in movimientos[:5]],
    }
