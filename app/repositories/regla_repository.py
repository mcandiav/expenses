from app.db.connection import get_connection
from app.services.text_utils import normalizar_glosa


def list_reglas(incluir_inactivas: bool = True) -> list[dict]:
    query = """
        SELECT
            r.id,
            r.patron,
            r.categoria_id,
            c.nombre AS categoria_nombre,
            r.prioridad,
            r.banco_opcional,
            r.producto_opcional,
            r.subtipo_fuente_opcional,
            r.activa,
            r.comentario
        FROM regla_categoria r
        JOIN categoria c ON c.id = r.categoria_id
    """
    if not incluir_inactivas:
        query += " WHERE r.activa = 1"
    query += " ORDER BY r.prioridad DESC, r.id ASC"
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def find_regla_duplicada(
    patron: str,
    categoria_id: int,
    banco_opcional: str | None = None,
) -> dict | None:
    patron_norm = normalizar_glosa(patron)
    banco_norm = banco_opcional.strip().upper() if banco_opcional else None
    with get_connection() as conn:
        if banco_norm:
            row = conn.execute(
                """
                SELECT r.*, c.nombre AS categoria_nombre
                FROM regla_categoria r
                JOIN categoria c ON c.id = r.categoria_id
                WHERE r.patron = ? AND r.categoria_id = ? AND r.banco_opcional = ? AND r.activa = 1
                """,
                (patron_norm, categoria_id, banco_norm),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT r.*, c.nombre AS categoria_nombre
                FROM regla_categoria r
                JOIN categoria c ON c.id = r.categoria_id
                WHERE r.patron = ? AND r.categoria_id = ? AND r.banco_opcional IS NULL AND r.activa = 1
                """,
                (patron_norm, categoria_id),
            ).fetchone()
    return dict(row) if row else None


def get_regla_by_id(regla_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT r.*, c.nombre AS categoria_nombre
            FROM regla_categoria r
            JOIN categoria c ON c.id = r.categoria_id
            WHERE r.id = ?
            """,
            (regla_id,),
        ).fetchone()
    return dict(row) if row else None


def create_regla(
    patron: str,
    categoria_id: int,
    prioridad: int = 100,
    banco_opcional: str | None = None,
    producto_opcional: str | None = None,
    subtipo_fuente_opcional: str | None = None,
    comentario: str | None = None,
    usuario_id: int | None = None,
) -> dict:
    patron_norm = normalizar_glosa(patron)
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO regla_categoria
            (patron, categoria_id, prioridad, banco_opcional, producto_opcional,
             subtipo_fuente_opcional, activa, comentario, creado_por_usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                patron_norm,
                categoria_id,
                prioridad,
                banco_opcional.strip().upper() if banco_opcional else None,
                producto_opcional.strip() if producto_opcional else None,
                subtipo_fuente_opcional.strip() if subtipo_fuente_opcional else None,
                comentario.strip() if comentario else None,
                usuario_id,
            ),
        )
        conn.commit()
        regla_id = cursor.lastrowid
    return get_regla_by_id(regla_id)


def update_regla(
    regla_id: int,
    patron: str,
    categoria_id: int,
    prioridad: int,
    banco_opcional: str | None,
    producto_opcional: str | None,
    subtipo_fuente_opcional: str | None,
    activa: bool,
    comentario: str | None,
) -> None:
    patron_norm = normalizar_glosa(patron)
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE regla_categoria
            SET patron = ?, categoria_id = ?, prioridad = ?, banco_opcional = ?,
                producto_opcional = ?, subtipo_fuente_opcional = ?, activa = ?, comentario = ?
            WHERE id = ?
            """,
            (
                patron_norm,
                categoria_id,
                prioridad,
                banco_opcional.strip().upper() if banco_opcional else None,
                producto_opcional.strip() if producto_opcional else None,
                subtipo_fuente_opcional.strip() if subtipo_fuente_opcional else None,
                int(activa),
                comentario.strip() if comentario else None,
                regla_id,
            ),
        )
        conn.commit()


def delete_regla(regla_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM regla_categoria WHERE id = ?", (regla_id,))
        conn.commit()
