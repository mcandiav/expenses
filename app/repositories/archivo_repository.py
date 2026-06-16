import json

from app.db.connection import get_connection


def get_by_hash(hash_archivo: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM archivo_importado WHERE hash_archivo = ?",
            (hash_archivo,),
        ).fetchone()
    return dict(row) if row else None


def get_by_id(archivo_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT a.*, u.email AS usuario_email
            FROM archivo_importado a
            LEFT JOIN usuario u ON u.id = a.usuario_id
            WHERE a.id = ?
            """,
            (archivo_id,),
        ).fetchone()
    return dict(row) if row else None


def list_archivos(limit: int = 100) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.*,
                u.email AS usuario_email,
                (SELECT COUNT(*) FROM movimiento_raw mr WHERE mr.archivo_id = a.id) AS filas_staging
            FROM archivo_importado a
            LEFT JOIN usuario u ON u.id = a.usuario_id
            ORDER BY a.fecha_importacion DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def create(
    nombre_archivo: str,
    ruta_relativa: str,
    hash_archivo: str,
    banco_inferido: str | None,
    tipo_fuente_inferido: str | None,
    fecha_referencial: str | None,
    usuario_id: int,
    estado: str,
    mensaje_error: str | None = None,
    observacion: str | None = None,
    reporte_inspeccion_json: str | None = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO archivo_importado (
                nombre_archivo, ruta_relativa, hash_archivo, banco_inferido,
                tipo_fuente_inferido, fecha_referencial, usuario_id, estado,
                mensaje_error, observacion, reporte_inspeccion_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nombre_archivo,
                ruta_relativa,
                hash_archivo,
                banco_inferido,
                tipo_fuente_inferido,
                fecha_referencial,
                usuario_id,
                estado,
                mensaje_error,
                observacion,
                reporte_inspeccion_json,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_conteos(archivo_id: int, filas_leidas: int, estado: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE archivo_importado
            SET filas_leidas = ?, estado = ?
            WHERE id = ?
            """,
            (filas_leidas, estado, archivo_id),
        )
        conn.commit()


def insert_movimientos_raw(archivo_id: int, filas: list[dict]) -> int:
    if not filas:
        return 0
    with get_connection() as conn:
        for fila in filas:
            hoja = fila.pop("_hoja_origen", None)
            fila_origen = fila.pop("_fila_origen", None)
            conn.execute(
                """
                INSERT INTO movimiento_raw (archivo_id, fila_origen, hoja_origen, raw_json)
                VALUES (?, ?, ?, ?)
                """,
                (archivo_id, fila_origen, hoja, json.dumps(fila, ensure_ascii=False)),
            )
        conn.commit()
    return len(filas)


def get_reporte_inspeccion(archivo_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT reporte_inspeccion_json FROM archivo_importado WHERE id = ?",
            (archivo_id,),
        ).fetchone()
    if not row or not row["reporte_inspeccion_json"]:
        return None
    return json.loads(row["reporte_inspeccion_json"])


def contar_movimientos(archivo_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM movimiento WHERE archivo_id = ? AND activo = 1",
            (archivo_id,),
        ).fetchone()
    return int(row[0]) if row else 0


def eliminar_movimientos_de_archivo(archivo_id: int) -> int:
    """Elimina movimientos normalizados; conserva staging raw para reprocesar."""
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
        cursor = conn.execute("DELETE FROM movimiento WHERE archivo_id = ?", (archivo_id,))
        conn.commit()
    return cursor.rowcount


def eliminar_archivo_completo(archivo_id: int) -> dict:
    with get_connection() as conn:
        mov_count = conn.execute(
            "SELECT COUNT(*) FROM movimiento WHERE archivo_id = ?", (archivo_id,)
        ).fetchone()[0]
        raw_count = conn.execute(
            "SELECT COUNT(*) FROM movimiento_raw WHERE archivo_id = ?", (archivo_id,)
        ).fetchone()[0]
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
        conn.execute("DELETE FROM movimiento_raw WHERE archivo_id = ?", (archivo_id,))
        conn.execute("DELETE FROM archivo_importado WHERE id = ?", (archivo_id,))
        conn.commit()
    return {
        "movimientos_eliminados": mov_count,
        "filas_raw_eliminadas": raw_count,
    }
