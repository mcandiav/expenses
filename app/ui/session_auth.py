from datetime import datetime, timedelta

import extra_streamlit_components as stx
import streamlit as st

from app.config import SESSION_MAX_AGE_SECONDS
from app.services.auth_service import COOKIE_NAME, create_session_token, verify_session_token


@st.cache_resource
def _cookie_manager() -> stx.CookieManager:
    return stx.CookieManager(key="expensas_cookie_manager")


def init_session() -> None:
    """Restaura la sesión desde cookie si el usuario refrescó la página."""
    if "user" in st.session_state:
        return

    manager = _cookie_manager()
    token = manager.get(COOKIE_NAME)

    if token is None and not st.session_state.get("_session_cookie_checked"):
        st.session_state["_session_cookie_checked"] = True
        st.rerun()

    if not token:
        return

    user = verify_session_token(token)
    if user:
        st.session_state["user"] = user
        st.session_state.pop("_session_cookie_checked", None)
        return

    manager.delete(COOKIE_NAME)


def persist_session(user: dict) -> None:
    token = create_session_token(user)
    expires = datetime.now() + timedelta(seconds=SESSION_MAX_AGE_SECONDS)
    _cookie_manager().set(
        COOKIE_NAME,
        token,
        expires_at=expires,
        key="expensas_set_session_cookie",
    )


def clear_session() -> None:
    _cookie_manager().delete(COOKIE_NAME)
    st.session_state.pop("user", None)
    st.session_state.pop("_session_cookie_checked", None)
