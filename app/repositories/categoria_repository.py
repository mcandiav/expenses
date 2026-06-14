from app.db.connection import get_connection


def list_categorias(incluir_inactivas: bool = True) -> list[dict]:
    query = """
        SELECT
            c.id,
            c.nombre,
            c.uso,
            c.activa,
            (SELECT COUNT(*) FROM regla_categoria r WHERE r.categoria_id = c.id) AS total_reglas,
            (SELECT COUNT(*) FROM movimiento_categorizado mc WHERE mc.categoria_id = c.id) AS total_movimientos
        FROM categoria c
    """
    if not incluir_inactivas:
        query += " WHERE c.activa = 1"
    query += " ORDER BY c.nombre COLLATE NOCASE"
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def get_categoria_by_id(categoria_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, nombre, uso, activa FROM categoria WHERE id = ?",
            (categoria_id,),
        ).fetchone()
    return dict(row) if row else None


def get_categoria_by_nombre(nombre: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, nombre, uso, activa FROM categoria WHERE nombre = ? COLLATE NOCASE",
            (nombre.strip(),),
        ).fetchone()
    return dict(row) if row else None


def create_categoria(nombre: str, uso: str | None = None) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO categoria (nombre, uso, activa) VALUES (?, ?, 1)",
            (nombre.strip(), uso.strip() if uso else None),
        )
        conn.commit()
        categoria_id = cursor.lastrowid
    return get_categoria_by_id(categoria_id)


def update_categoria(categoria_id: int, nombre: str, uso: str | None, activa: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE categoria
            SET nombre = ?, uso = ?, activa = ?
            WHERE id = ?
            """,
            (nombre.strip(), uso.strip() if uso else None, int(activa), categoria_id),
        )
        conn.commit()


def delete_categoria(categoria_id: int) -> None:
    with get_connection() as conn:
        total_reglas = conn.execute(
            "SELECT COUNT(*) FROM regla_categoria WHERE categoria_id = ?",
            (categoria_id,),
        ).fetchone()[0]
        total_mov = conn.execute(
            "SELECT COUNT(*) FROM movimiento_categorizado WHERE categoria_id = ?",
            (categoria_id,),
        ).fetchone()[0]
        if total_reglas or total_mov:
            raise ValueError(
                "No se puede eliminar: la categoría tiene reglas o movimientos asociados. Desactívela."
            )
        conn.execute("DELETE FROM categoria WHERE id = ?", (categoria_id,))
        conn.commit()
