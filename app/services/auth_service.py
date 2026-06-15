import base64
import hashlib
import hmac
import json
import time

from app.config import SESSION_MAX_AGE_SECONDS, SESSION_SECRET

COOKIE_NAME = "expensas_session"


def _sign(payload_b64: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()


def create_session_token(user: dict) -> str:
    payload = {
        "uid": user["id"],
        "email": user["email"],
        "nombre": user["nombre"],
        "rol": user["rol"],
        "exp": time.time() + SESSION_MAX_AGE_SECONDS,
    }
    data = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"{data}.{_sign(data)}"


def verify_session_token(token: str) -> dict | None:
    if not token or "." not in token:
        return None
    try:
        data, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(_sign(data), sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(data.encode()))
        if payload.get("exp", 0) < time.time():
            return None

        from app.repositories.usuario_repository import get_usuario_activo_por_id

        user = get_usuario_activo_por_id(int(payload["uid"]))
        if not user:
            return None
        return user
    except (ValueError, KeyError, json.JSONDecodeError):
        return None
