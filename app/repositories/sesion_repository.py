import secrets
from datetime import datetime, timedelta, timezone

from app.config import SESSION_MAX_AGE_SECONDS
from app.db.connection import get_connection


def crear_sesion(usuario_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expira = datetime.now(timezone.utc) + timedelta(seconds=SESSION_MAX_AGE_SECONDS)
    expira_sql = expira.strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sesion_usuario (token, usuario_id, expira_en)
            VALUES (?, ?, ?)
            """,
            (token, usuario_id, expira_sql),
        )
        conn.commit()
    return token


def obtener_usuario_por_token(token: str) -> dict | None:
    if not token:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.email, u.nombre, r.nombre AS rol, s.expira_en
            FROM sesion_usuario s
            JOIN usuario u ON u.id = s.usuario_id
            JOIN rol r ON r.id = u.rol_id
            WHERE s.token = ?
              AND u.activo = 1
              AND s.expira_en > datetime('now')
            """,
            (token,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "nombre": row["nombre"],
        "rol": row["rol"],
    }


def revocar_sesion(token: str) -> None:
    if not token:
        return
    with get_connection() as conn:
        conn.execute("DELETE FROM sesion_usuario WHERE token = ?", (token,))
        conn.commit()


def limpiar_sesiones_expiradas() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sesion_usuario WHERE expira_en <= datetime('now')")
        conn.commit()
