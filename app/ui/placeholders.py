import streamlit as st


def render_placeholder(titulo: str, descripcion: str) -> None:
    st.subheader(titulo)
    st.info(descripcion)
