from datetime import datetime, timedelta

import extra_streamlit_components as stx
import streamlit as st

from app.config import SESSION_MAX_AGE_SECONDS
from app.services.auth_service import (
    COOKIE_NAME,
    create_session_token,
    revoke_session_token,
    verify_session_token,
)

_COOKIE_MANAGER_REF = "_expensas_cookie_manager_ref"
_COOKIE_MANAGER_WIDGET_KEY = "expensas_cookies_widget"
_COOKIE_WAIT_KEY = "_session_cookie_wait"
_MAX_COOKIE_WAITS = 6


def ensure_cookie_manager() -> stx.CookieManager:
    """Instancia el componente de cookies en cada ejecución del script."""
    if _COOKIE_MANAGER_REF not in st.session_state:
        st.session_state[_COOKIE_MANAGER_REF] = stx.CookieManager(
            key=_COOKIE_MANAGER_WIDGET_KEY
        )
    return st.session_state[_COOKIE_MANAGER_REF]


def _read_session_token(manager: stx.CookieManager) -> str | None:
    token = manager.get(COOKIE_NAME)
    if token:
        return str(token)
    try:
        todas = manager.get_all()
        if isinstance(todas, dict):
            valor = todas.get(COOKIE_NAME)
            if valor:
                return str(valor)
    except Exception:
        pass
    return None


def init_session() -> None:
    """Restaura la sesión desde cookie si el usuario refrescó la página."""
    if "user" in st.session_state:
        return

    manager = ensure_cookie_manager()
    token = _read_session_token(manager)

    if not token:
        esperas = int(st.session_state.get(_COOKIE_WAIT_KEY, 0))
        if esperas < _MAX_COOKIE_WAITS:
            st.session_state[_COOKIE_WAIT_KEY] = esperas + 1
            st.rerun()
        return

    st.session_state.pop(_COOKIE_WAIT_KEY, None)
    user = verify_session_token(token)
    if user:
        st.session_state["user"] = user
        return

    revoke_session_token(token)
    manager.delete(COOKIE_NAME)


def persist_session(user: dict) -> None:
    token = create_session_token(user)
    expires = datetime.now() + timedelta(seconds=SESSION_MAX_AGE_SECONDS)
    ensure_cookie_manager().set(
        COOKIE_NAME,
        token,
        expires_at=expires,
        key="expensas_set_session_cookie",
    )
    st.session_state.pop(_COOKIE_WAIT_KEY, None)


def clear_session() -> None:
    manager = ensure_cookie_manager()
    token = _read_session_token(manager)
    if token:
        revoke_session_token(token)
    manager.delete(COOKIE_NAME)
    st.session_state.pop("user", None)
    st.session_state.pop(_COOKIE_WAIT_KEY, None)
