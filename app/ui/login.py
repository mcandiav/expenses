import streamlit as st

from app.repositories.usuario_repository import authenticate
from app.ui.session_auth import persist_session


def render_login() -> bool:
    st.title("Categorización de Expensas")
    st.caption("Ingrese con su usuario para continuar.")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        user = authenticate(email, password)
        if user:
            st.session_state["user"] = user
            persist_session(user)
            st.rerun()
        else:
            st.error("Credenciales inválidas o usuario inactivo.")
    return False
