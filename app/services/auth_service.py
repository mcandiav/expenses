from app.repositories.sesion_repository import (
    crear_sesion,
    limpiar_sesiones_expiradas,
    obtener_usuario_por_token,
    revocar_sesion,
)

COOKIE_NAME = "expensas_session"


def create_session_token(user: dict) -> str:
    limpiar_sesiones_expiradas()
    return crear_sesion(int(user["id"]))


def verify_session_token(token: str) -> dict | None:
    return obtener_usuario_por_token(token)


def revoke_session_token(token: str) -> None:
    revocar_sesion(token)
