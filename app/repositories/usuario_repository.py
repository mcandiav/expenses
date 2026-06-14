import bcrypt

from app.db.connection import get_connection


def authenticate(email: str, password: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.email, u.nombre, u.password_hash, u.activo, r.nombre AS rol
            FROM usuario u
            JOIN rol r ON r.id = u.rol_id
            WHERE u.email = ? COLLATE NOCASE
            """,
            (email.strip(),),
        ).fetchone()
    if not row or not row["activo"]:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return None
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuario SET fecha_ultimo_login = datetime('now') WHERE id = ?",
            (row["id"],),
        )
        conn.commit()
    return {
        "id": row["id"],
        "email": row["email"],
        "nombre": row["nombre"],
        "rol": row["rol"],
    }
