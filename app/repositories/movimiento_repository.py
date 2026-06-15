from dataclasses import dataclass
import sqlite3
from typing import Any

from app.db.connection import get_connection

COLUMNAS_ORDENABLES = {
    "fecha": "m.fecha_movimiento",
    "banco": "banco",
    "tipo_fuente": "tipo_fuente",
    "archivo_origen": "archivo_origen",
    "glosa_original": "m.glosa_original",
    "glosa_normalizada": "m.glosa_normalizada",
    "monto": "monto",
    "moneda": "m.moneda",
    "monto_moneda_origen": "m.monto_moneda_origen",
    "categoria": "categoria",
    "estado": "m.estado_normalizacion",
    "duplicado": "m.estado_duplicado",
    "revisado": "revisado",
    "regla_aplicada": "regla_aplicada",
    "observacion": "mc.observacion",
    "fila_origen": "m.fila_origen",
}

SELECT_BASE = """
    SELECT
        m.id,
        m.fecha_movimiento AS fecha,
        COALESCE(NULLIF(m.banco, ''), a.banco_inferido, 'Sin banco') AS banco,
        COALESCE(m.producto, a.tipo_fuente_inferido, '') AS tipo_fuente,
        a.nombre_archivo AS archivo_origen,
        a.id AS archivo_id,
        m.glosa_original,
        m.glosa_normalizada,
        COALESCE(m.monto_corregido, m.monto) AS monto,
        m.moneda,
        m.monto_moneda_origen,
        COALESCE(c.nombre, 'Por revisar') AS categoria,
        m.estado_normalizacion AS estado,
        m.estado_duplicado AS duplicado,
        COALESCE(mc.revisado, 0) AS revisado,
        COALESCE(rc.patron, '') AS regla_aplicada,
        COALESCE(mc.observacion, '') AS observacion,
        m.fila_origen
    FROM movimiento m
    JOIN archivo_importado a ON a.id = m.archivo_id
    LEFT JOIN movimiento_categorizado mc ON mc.movimiento_id = m.id
    LEFT JOIN categoria c ON c.id = COALESCE(mc.categoria_manual_id, mc.categoria_id)
    LEFT JOIN regla_categoria rc ON rc.id = mc.regla_id
    WHERE m.activo = 1
"""


@dataclass
class FiltrosMovimiento:
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    banco: str | None = None
    archivo_id: int | None = None
    categoria: str | None = None
    glosa_contiene: str | None = None
    monto_min: float | None = None
    monto_max: float | None = None
    moneda: str | None = None
    estado: str | None = None
    duplicado: str | None = None
    revisado: bool | None = None
    por_revisar: bool | None = None


def listar_movimientos(
    filtros: FiltrosMovimiento,
    orden_columna: str = "fecha",
    orden_desc: bool = True,
    pagina: int = 1,
    por_pagina: int = 50,
) -> tuple[list[dict], int]:
    where_suffix, params = _build_where(filtros)
    order_col = COLUMNAS_ORDENABLES.get(orden_columna, "m.fecha_movimiento")
    direction = "DESC" if orden_desc else "ASC"
    offset = max(pagina - 1, 0) * por_pagina

    where_suffix, params = _build_where(filtros)
    query = f"{SELECT_BASE}{where_suffix} ORDER BY {order_col} {direction}, m.id DESC LIMIT ? OFFSET ?"

    count_sql = """
        SELECT COUNT(*)
        FROM movimiento m
        JOIN archivo_importado a ON a.id = m.archivo_id
        LEFT JOIN movimiento_categorizado mc ON mc.movimiento_id = m.id
        LEFT JOIN categoria c ON c.id = COALESCE(mc.categoria_manual_id, mc.categoria_id)
        WHERE m.activo = 1
    """
    count_where, count_params = _build_where_clauses(filtros)
    if count_where:
        count_sql += " AND " + " AND ".join(count_where)

    with get_connection() as conn:
        total = conn.execute(count_sql, count_params).fetchone()[0]
        rows = conn.execute(query, params + [por_pagina, offset]).fetchall()

    return [dict(row) for row in rows], total


def _build_where(filtros: FiltrosMovimiento) -> tuple[str, list[Any]]:
    clauses, params = _build_where_clauses(filtros)
    if clauses:
        return " AND " + " AND ".join(clauses), params
    return "", params


def _build_where_clauses(filtros: FiltrosMovimiento) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if filtros.fecha_desde:
        clauses.append("m.fecha_movimiento >= ?")
        params.append(filtros.fecha_desde)
    if filtros.fecha_hasta:
        clauses.append("m.fecha_movimiento <= ?")
        params.append(filtros.fecha_hasta)
    if filtros.banco:
        clauses.append("(COALESCE(NULLIF(m.banco, ''), a.banco_inferido) = ?)")
        params.append(filtros.banco.upper())
    if filtros.archivo_id:
        clauses.append("a.id = ?")
        params.append(filtros.archivo_id)
    if filtros.categoria:
        clauses.append("c.nombre = ?")
        params.append(filtros.categoria)
    if filtros.glosa_contiene:
        clauses.append(
            "(m.glosa_original LIKE ? OR m.glosa_normalizada LIKE ?)"
        )
        like = f"%{filtros.glosa_contiene}%"
        params.extend([like, like])
    if filtros.monto_min is not None:
        clauses.append("COALESCE(m.monto_corregido, m.monto) >= ?")
        params.append(filtros.monto_min)
    if filtros.monto_max is not None:
        clauses.append("COALESCE(m.monto_corregido, m.monto) <= ?")
        params.append(filtros.monto_max)
    if filtros.moneda:
        clauses.append("UPPER(m.moneda) = ?")
        params.append(filtros.moneda.upper())
    if filtros.estado:
        clauses.append("m.estado_normalizacion = ?")
        params.append(filtros.estado)
    if filtros.duplicado:
        clauses.append("m.estado_duplicado = ?")
        params.append(filtros.duplicado)
    if filtros.revisado is not None:
        clauses.append("COALESCE(mc.revisado, 0) = ?")
        params.append(int(filtros.revisado))
    if filtros.por_revisar is True:
        clauses.append("(c.nombre = 'Por revisar' OR mc.metodo_clasificacion = 'sin_regla')")
    elif filtros.por_revisar is False:
        clauses.append("(c.nombre IS NULL OR c.nombre != 'Por revisar')")

    return clauses, params


def obtener_opciones_filtro() -> dict[str, list]:
    with get_connection() as conn:
        bancos = [
            r[0]
            for r in conn.execute(
                """
                SELECT DISTINCT COALESCE(NULLIF(m.banco, ''), a.banco_inferido)
                FROM movimiento m
                JOIN archivo_importado a ON a.id = m.archivo_id
                WHERE m.activo = 1 AND COALESCE(NULLIF(m.banco, ''), a.banco_inferido) IS NOT NULL
                ORDER BY 1
                """
            ).fetchall()
        ]
        categorias = [
            r[0]
            for r in conn.execute(
                """
                SELECT DISTINCT COALESCE(c.nombre, 'Por revisar')
                FROM movimiento m
                LEFT JOIN movimiento_categorizado mc ON mc.movimiento_id = m.id
                LEFT JOIN categoria c ON c.id = COALESCE(mc.categoria_manual_id, mc.categoria_id)
                WHERE m.activo = 1
                ORDER BY 1
                """
            ).fetchall()
        ]
        archivos = [
            dict(row)
            for row in conn.execute(
                """
                SELECT DISTINCT a.id, a.nombre_archivo
                FROM movimiento m
                JOIN archivo_importado a ON a.id = m.archivo_id
                WHERE m.activo = 1
                ORDER BY a.nombre_archivo
                """
            ).fetchall()
        ]
        monedas = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT UPPER(moneda) FROM movimiento WHERE activo = 1 AND moneda IS NOT NULL ORDER BY 1"
            ).fetchall()
        ]
        estados = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT estado_normalizacion FROM movimiento WHERE activo = 1 ORDER BY 1"
            ).fetchall()
        ]
        duplicados = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT estado_duplicado FROM movimiento WHERE activo = 1 ORDER BY 1"
            ).fetchall()
        ]
    return {
        "bancos": bancos,
        "categorias": categorias,
        "archivos": archivos,
        "monedas": monedas,
        "estados": estados,
        "duplicados": duplicados,
    }


def list_ids_por_revisar() -> list[int]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT m.id
            FROM movimiento m
            LEFT JOIN movimiento_categorizado mc ON mc.movimiento_id = m.id
            LEFT JOIN categoria c ON c.id = COALESCE(mc.categoria_manual_id, mc.categoria_id)
            WHERE m.activo = 1
              AND COALESCE(mc.revisado, 0) = 0
              AND (
                    c.nombre = 'Por revisar'
                    OR mc.movimiento_id IS NULL
                    OR mc.metodo_clasificacion = 'sin_regla'
                  )
            ORDER BY m.id
            """
        ).fetchall()
    return [int(row["id"]) for row in rows]


def get_by_id(movimiento_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            f"{SELECT_BASE} AND m.id = ?",
            (movimiento_id,),
        ).fetchone()
    return dict(row) if row else None


def actualizar_categorizacion(
    movimiento_id: int,
    categoria_id: int | None,
    metodo_clasificacion: str,
    regla_id: int | None,
    revisado: bool = False,
    conn: sqlite3.Connection | None = None,
) -> None:
    def _apply(connection: sqlite3.Connection) -> None:
        existe = connection.execute(
            "SELECT 1 FROM movimiento_categorizado WHERE movimiento_id = ?",
            (movimiento_id,),
        ).fetchone()
        if existe:
            connection.execute(
                """
                UPDATE movimiento_categorizado
                SET categoria_id = ?, metodo_clasificacion = ?, regla_id = ?,
                    revisado = ?, fecha_clasificacion = datetime('now')
                WHERE movimiento_id = ?
                """,
                (categoria_id, metodo_clasificacion, regla_id, int(revisado), movimiento_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO movimiento_categorizado (
                    movimiento_id, categoria_id, metodo_clasificacion, regla_id, revisado
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (movimiento_id, categoria_id, metodo_clasificacion, regla_id, int(revisado)),
            )

    if conn is not None:
        _apply(conn)
        return

    with get_connection() as connection:
        _apply(connection)
        connection.commit()
