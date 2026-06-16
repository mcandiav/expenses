import hashlib
import json
import re
from typing import Any

from app.db.connection import get_connection
from app.services.categorization_service import clasificar_glosa
from app.services.currency_utils import extraer_monto_y_moneda, parse_monto
from app.services.text_utils import normalizar_glosa

FECHA_KEYS = ("fecha", "date", "fec", "periodo", "transaction")
GLOSA_KEYS = (
    "glosa",
    "descripcion",
    "descripción",
    "concepto",
    "detalle",
    "merchant",
    "comercio",
    "nombre",
)
FILAS_IGNORAR_GLOSA = {
    "descripción",
    "descripcion",
    "glosa",
    "movimiento",
    "movimientos",
    "fecha",
    "monto",
    "ciudad",
    "código referencia",
    "codigo referencia",
    "tipo de tarjeta",
}
FILAS_IGNORAR_FECHA = {"fecha", "movimiento", "movimientos", "none", ""}


def normalizar_archivo(archivo_id: int, forzar: bool = False) -> int:
    if forzar:
        reprocesar_archivo(archivo_id)

    with get_connection() as conn:
        archivo = conn.execute(
            "SELECT * FROM archivo_importado WHERE id = ?", (archivo_id,)
        ).fetchone()
        if not archivo:
            return 0

        raw_rows = conn.execute(
            "SELECT id, fila_origen, hoja_origen, raw_json FROM movimiento_raw WHERE archivo_id = ?",
            (archivo_id,),
        ).fetchall()

        creados = 0
        archivo_dict = dict(archivo)
        for raw in raw_rows:
            if conn.execute(
                "SELECT 1 FROM movimiento WHERE archivo_id = ? AND fila_origen = ?",
                (archivo_id, raw["fila_origen"]),
            ).fetchone():
                continue

            data = json.loads(raw["raw_json"])
            mov = _mapear_raw_a_movimiento(archivo_dict, raw["fila_origen"], data)
            if not _es_fila_movimiento_valida(mov):
                continue

            hash_mov = _hash_movimiento(mov)
            estado_dup = "unico"
            if conn.execute(
                "SELECT id FROM movimiento WHERE hash_movimiento = ?", (hash_mov,)
            ).fetchone():
                estado_dup = "duplicado_exacto"

            cursor = conn.execute(
                """
                INSERT INTO movimiento (
                    archivo_id, fila_origen, banco, producto, subtipo_fuente,
                    fecha_movimiento, glosa_original, glosa_normalizada,
                    monto, moneda, monto_moneda_origen, hash_movimiento,
                    estado_normalizacion, estado_duplicado, activo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    archivo_id,
                    mov["fila_origen"],
                    mov["banco"],
                    mov["producto"],
                    mov["subtipo_fuente"],
                    mov["fecha_movimiento"],
                    mov["glosa_original"],
                    mov["glosa_normalizada"],
                    mov["monto"],
                    mov["moneda"],
                    mov["monto_moneda_origen"],
                    hash_mov,
                    mov["estado_normalizacion"],
                    estado_dup,
                ),
            )
            movimiento_id = cursor.lastrowid

            resultado = clasificar_glosa(
                mov["glosa_original"] or "",
                banco=mov["banco"],
                producto=mov["producto"],
                subtipo_fuente=mov["subtipo_fuente"],
            )
            conn.execute(
                """
                INSERT INTO movimiento_categorizado (
                    movimiento_id, categoria_id, metodo_clasificacion, regla_id, revisado
                ) VALUES (?, ?, ?, ?, 0)
                """,
                (
                    movimiento_id,
                    resultado.categoria_id,
                    resultado.metodo,
                    resultado.regla_id,
                ),
            )
            creados += 1

        conn.commit()
    return creados


def reprocesar_archivo(archivo_id: int) -> None:
    with get_connection() as conn:
        mov_ids = [
            r[0]
            for r in conn.execute(
                "SELECT id FROM movimiento WHERE archivo_id = ?", (archivo_id,)
            ).fetchall()
        ]
        for mov_id in mov_ids:
            conn.execute(
                "DELETE FROM movimiento_categorizado WHERE movimiento_id = ?", (mov_id,)
            )
        conn.execute("DELETE FROM movimiento WHERE archivo_id = ?", (archivo_id,))
        conn.commit()


def normalizar_pendientes() -> int:
    with get_connection() as conn:
        archivos = conn.execute(
            """
            SELECT DISTINCT mr.archivo_id
            FROM movimiento_raw mr
            LEFT JOIN movimiento m ON m.archivo_id = mr.archivo_id AND m.fila_origen = mr.fila_origen
            WHERE m.id IS NULL
            """
        ).fetchall()
    total = 0
    for row in archivos:
        total += normalizar_archivo(row["archivo_id"])
    return total


def reprocesar_archivos_multimoneda() -> int:
    """Reprocesa archivos internacionales que quedaron con moneda CLP por error."""
    with get_connection() as conn:
        archivos = conn.execute(
            """
            SELECT DISTINCT a.id
            FROM archivo_importado a
            JOIN movimiento m ON m.archivo_id = a.id
            WHERE (
                LOWER(a.nombre_archivo) LIKE '%internacional%'
                OR LOWER(COALESCE(a.tipo_fuente_inferido, '')) LIKE '%internacional%'
            )
            AND UPPER(m.moneda) = 'CLP'
            """
        ).fetchall()
    total = 0
    for row in archivos:
        reprocesar_archivo(row["id"])
        total += normalizar_archivo(row["id"])
    return total


def _mapear_raw_a_movimiento(archivo: dict, fila_origen: int, data: dict[str, Any]) -> dict:
    banco = archivo.get("banco_inferido")
    tipo_fuente = archivo.get("tipo_fuente_inferido") or ""
    subtipo = _extraer_subtipo(tipo_fuente, archivo.get("nombre_archivo", ""))
    if "—" in tipo_fuente:
        tipo_fuente = tipo_fuente.split("—", 1)[0].strip()

    fecha = _buscar_valor(data, FECHA_KEYS) or data.get("fecha")
    glosa = _buscar_valor(data, GLOSA_KEYS) or _primer_texto_largo(data)
    monto, moneda, _col = extraer_monto_y_moneda(
        data,
        nombre_archivo=archivo.get("nombre_archivo", ""),
        subtipo_fuente=subtipo,
    )

    return {
        "fila_origen": fila_origen,
        "banco": banco,
        "producto": tipo_fuente or None,
        "subtipo_fuente": subtipo,
        "fecha_movimiento": _normalizar_fecha(fecha),
        "glosa_original": glosa,
        "glosa_normalizada": normalizar_glosa(glosa or ""),
        "monto": monto,
        "moneda": moneda,
        "monto_moneda_origen": monto if moneda != "CLP" else None,
        "estado_normalizacion": "ok" if glosa and monto is not None else "parcial",
    }


def _extraer_subtipo(tipo_fuente: str, nombre_archivo: str) -> str | None:
    if "—" in tipo_fuente:
        return tipo_fuente.split("—", 1)[1].strip()
    nombre = nombre_archivo.lower()
    if "scotiabank" in nombre or "scotia" in nombre:
        if "internacional" in nombre or " inter" in nombre:
            return "Internacionales"
        return "Nacionales"
    if "internacional" in nombre:
        return "Internacionales"
    if "nacional" in nombre:
        return "Nacionales"
    return None


def _es_fila_movimiento_valida(mov: dict) -> bool:
    if mov.get("monto") is None:
        return False

    fecha = (mov.get("fecha_movimiento") or "").strip()
    if not fecha or fecha.lower() in FILAS_IGNORAR_FECHA:
        return False
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
        return False

    glosa = (mov.get("glosa_original") or "").strip().lower()
    if not glosa or glosa in FILAS_IGNORAR_GLOSA:
        return False

    return True


def _buscar_valor(data: dict, keywords: tuple[str, ...]) -> str | None:
    for clave, valor in data.items():
        clave_l = clave.lower()
        if any(k in clave_l for k in keywords):
            if any(x in clave_l for x in ("monto", "importe", "amount", "cargo", "abono")):
                continue
            texto = str(valor).strip() if valor is not None else ""
            if texto and texto.lower() not in FILAS_IGNORAR_GLOSA:
                return texto
    return None


def _primer_texto_largo(data: dict) -> str | None:
    candidatos = []
    for clave, valor in data.items():
        clave_l = clave.lower()
        if any(x in clave_l for x in ("monto", "importe", "fecha", "codigo", "código", "tipo")):
            continue
        texto = str(valor).strip() if valor is not None else ""
        if len(texto) >= 4 and not _parece_numero(texto):
            candidatos.append((len(texto), texto))
    if candidatos:
        return sorted(candidatos, reverse=True)[0][1]
    return None


def _parse_monto(valor: str | None) -> float | None:
    return parse_monto(valor)


def _normalizar_fecha(valor: str | None) -> str | None:
    if not valor:
        return None
    texto = str(valor).strip()
    if texto.lower() in FILAS_IGNORAR_FECHA:
        return None
    match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", texto)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})", texto)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            y = f"20{y}"
        return f"{y}-{int(m):02d}-{int(d):02d}"
    return None


def _parece_numero(texto: str) -> bool:
    try:
        float(texto.replace(",", ".").replace("$", "").strip())
        return True
    except ValueError:
        return False


def _hash_movimiento(mov: dict) -> str:
    base = "|".join(
        [
            str(mov.get("banco") or ""),
            str(mov.get("fecha_movimiento") or ""),
            str(mov.get("glosa_original") or ""),
            str(mov.get("monto") or ""),
            str(mov.get("moneda") or ""),
            str(mov.get("fila_origen") or ""),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
