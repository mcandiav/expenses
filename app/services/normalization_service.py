import hashlib
import json
import re
from typing import Any

from app.db.connection import get_connection
from app.services.categorization_service import clasificar_glosa
from app.services.text_utils import normalizar_glosa

FECHA_KEYS = ("fecha", "date", "fec", "periodo", "transaction")
GLOSA_KEYS = ("glosa", "descripcion", "descripción", "concepto", "detalle", "merchant", "comercio", "nombre")
MONTO_KEYS = ("monto", "importe", "cargo", "abono", "amount", "valor", "total", "clp", "pesos")
MONEDA_KEYS = ("moneda", "currency", "divisa")


def normalizar_archivo(archivo_id: int) -> int:
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
        for raw in raw_rows:
            if conn.execute(
                "SELECT 1 FROM movimiento WHERE archivo_id = ? AND fila_origen = ?",
                (archivo_id, raw["fila_origen"]),
            ).fetchone():
                continue

            data = json.loads(raw["raw_json"])
            mov = _mapear_raw_a_movimiento(dict(archivo), raw["fila_origen"], data)
            hash_mov = _hash_movimiento(mov)
            if conn.execute(
                "SELECT id FROM movimiento WHERE hash_movimiento = ?", (hash_mov,)
            ).fetchone():
                mov["estado_duplicado"] = "duplicado_exacto"

            cursor = conn.execute(
                """
                INSERT INTO movimiento (
                    archivo_id, fila_origen, banco, producto, subtipo_fuente,
                    fecha_movimiento, glosa_original, glosa_normalizada,
                    monto, moneda, hash_movimiento, estado_normalizacion,
                    estado_duplicado, activo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
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
                    hash_mov,
                    mov["estado_normalizacion"],
                    mov.get("estado_duplicado", "unico"),
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


def _mapear_raw_a_movimiento(archivo: dict, fila_origen: int, data: dict[str, Any]) -> dict:
    fecha = _buscar_valor(data, FECHA_KEYS)
    glosa = _buscar_valor(data, GLOSA_KEYS) or _primer_texto_largo(data)
    monto = _parse_monto(_buscar_valor(data, MONTO_KEYS))
    moneda = _buscar_valor(data, MONEDA_KEYS) or "CLP"

    banco = archivo.get("banco_inferido")
    tipo_fuente = archivo.get("tipo_fuente_inferido") or ""
    subtipo = None
    if "—" in tipo_fuente:
        partes = tipo_fuente.split("—", 1)
        tipo_fuente = partes[0].strip()
        subtipo = partes[1].strip()

    return {
        "fila_origen": fila_origen,
        "banco": banco,
        "producto": tipo_fuente or None,
        "subtipo_fuente": subtipo,
        "fecha_movimiento": _normalizar_fecha(fecha),
        "glosa_original": glosa,
        "glosa_normalizada": normalizar_glosa(glosa or ""),
        "monto": monto,
        "moneda": str(moneda).upper() if moneda else "CLP",
        "estado_normalizacion": "ok" if glosa and monto is not None else "parcial",
    }


def _buscar_valor(data: dict, keywords: tuple[str, ...]) -> str | None:
    for clave, valor in data.items():
        clave_l = clave.lower()
        if any(k in clave_l for k in keywords):
            texto = str(valor).strip() if valor is not None else ""
            if texto:
                return texto
    return None


def _primer_texto_largo(data: dict) -> str | None:
    candidatos = []
    for clave, valor in data.items():
        texto = str(valor).strip() if valor is not None else ""
        if len(texto) >= 4 and not _parece_numero(texto):
            candidatos.append((len(texto), texto))
    if candidatos:
        return sorted(candidatos, reverse=True)[0][1]
    return None


def _parse_monto(valor: str | None) -> float | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    negativo = texto.startswith("-") or texto.startswith("(")
    limpio = re.sub(r"[^\d,.\-]", "", texto)
    if "," in limpio and "." in limpio:
        if limpio.rfind(",") > limpio.rfind("."):
            limpio = limpio.replace(".", "").replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    elif "," in limpio:
        partes = limpio.split(",")
        limpio = limpio.replace(",", ".") if len(partes[-1]) <= 2 else limpio.replace(",", "")
    try:
        monto = float(limpio)
        return -abs(monto) if negativo else monto
    except ValueError:
        return None


def _normalizar_fecha(valor: str | None) -> str | None:
    if not valor:
        return None
    texto = str(valor).strip()
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
    return texto[:10] if texto else None


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
            str(mov.get("fila_origen") or ""),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
