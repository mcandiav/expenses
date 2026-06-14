from dataclasses import dataclass, field

from app.db.connection import get_connection

ESTADOS_ARCHIVO_OK = ("inspeccionado", "procesado")
ESTADOS_DUPLICADO = ("duplicado_exacto", "posible_duplicado")


@dataclass
class DashboardResumen:
    total_archivos: int = 0
    archivos_procesados: int = 0
    archivos_con_error: int = 0
    movimientos_extraidos: int = 0
    movimientos_normalizados: int = 0
    movimientos_categorizados: int = 0
    movimientos_por_revisar: int = 0
    movimientos_duplicados: int = 0
    ultima_importacion: str | None = None
    monto_por_categoria: list[dict] = field(default_factory=list)
    monto_por_banco: list[dict] = field(default_factory=list)
    ultimos_archivos: list[dict] = field(default_factory=list)


def obtener_resumen() -> DashboardResumen:
    resumen = DashboardResumen()

    with get_connection() as conn:
        resumen.total_archivos = conn.execute(
            "SELECT COUNT(*) FROM archivo_importado"
        ).fetchone()[0]

        resumen.archivos_procesados = conn.execute(
            f"""
            SELECT COUNT(*) FROM archivo_importado
            WHERE estado IN ({",".join("?" * len(ESTADOS_ARCHIVO_OK))})
            """,
            ESTADOS_ARCHIVO_OK,
        ).fetchone()[0]

        resumen.archivos_con_error = conn.execute(
            "SELECT COUNT(*) FROM archivo_importado WHERE estado = 'error'"
        ).fetchone()[0]

        resumen.movimientos_extraidos = conn.execute(
            "SELECT COUNT(*) FROM movimiento_raw"
        ).fetchone()[0]

        resumen.movimientos_normalizados = conn.execute(
            "SELECT COUNT(*) FROM movimiento WHERE activo = 1"
        ).fetchone()[0]

        resumen.movimientos_categorizados = conn.execute(
            """
            SELECT COUNT(*)
            FROM movimiento_categorizado mc
            JOIN categoria c ON c.id = mc.categoria_id
            WHERE c.nombre != 'Por revisar'
            """
        ).fetchone()[0]

        resumen.movimientos_por_revisar = conn.execute(
            """
            SELECT COUNT(*)
            FROM movimiento_categorizado mc
            JOIN categoria c ON c.id = mc.categoria_id
            WHERE c.nombre = 'Por revisar' OR mc.metodo_clasificacion = 'sin_regla'
            """
        ).fetchone()[0]

        if resumen.movimientos_normalizados == 0:
            resumen.movimientos_por_revisar = 0
            resumen.movimientos_categorizados = 0

        resumen.movimientos_duplicados = conn.execute(
            f"""
            SELECT COUNT(*) FROM movimiento
            WHERE activo = 1
              AND estado_duplicado IN ({",".join("?" * len(ESTADOS_DUPLICADO))})
            """,
            ESTADOS_DUPLICADO,
        ).fetchone()[0]

        ultima = conn.execute(
            "SELECT MAX(fecha_importacion) FROM archivo_importado"
        ).fetchone()[0]
        resumen.ultima_importacion = ultima

        resumen.monto_por_categoria = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    c.nombre AS categoria,
                    COUNT(m.id) AS cantidad,
                    SUM(COALESCE(m.monto_corregido, m.monto_clp, m.monto, 0)) AS monto_total
                FROM movimiento m
                JOIN movimiento_categorizado mc ON mc.movimiento_id = m.id
                JOIN categoria c ON c.id = mc.categoria_id
                WHERE m.activo = 1
                GROUP BY c.nombre
                ORDER BY monto_total DESC
                """
            ).fetchall()
        ]

        resumen.monto_por_banco = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    COALESCE(NULLIF(banco, ''), 'Sin banco') AS banco,
                    COUNT(*) AS cantidad,
                    SUM(COALESCE(monto_corregido, monto_clp, monto, 0)) AS monto_total
                FROM movimiento
                WHERE activo = 1
                GROUP BY COALESCE(NULLIF(banco, ''), 'Sin banco')
                ORDER BY monto_total DESC
                """
            ).fetchall()
        ]

        resumen.ultimos_archivos = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    a.id,
                    a.nombre_archivo,
                    a.banco_inferido,
                    a.estado,
                    a.filas_leidas,
                    a.fecha_importacion,
                    u.email AS usuario_email
                FROM archivo_importado a
                LEFT JOIN usuario u ON u.id = a.usuario_id
                ORDER BY a.fecha_importacion DESC
                LIMIT 8
                """
            ).fetchall()
        ]

    return resumen
