import streamlit as st

from app.db.connection import bootstrap_database
from app.ui.archivos import render_archivos_importados
from app.ui.dashboard import render_dashboard
from app.ui.login import render_login
from app.ui.placeholders import render_placeholder
from app.ui.movimientos import render_movimientos
from app.ui.reglas_categorias import render_reglas_categorias
from app.ui.subir_archivos import render_subir_archivos
from app.ui.usuarios import render_usuarios_roles


def main() -> None:
    st.set_page_config(
        page_title="Categorización de Expensas",
        page_icon="📊",
        layout="wide",
    )

    db_info = bootstrap_database()

    if "user" not in st.session_state:
        render_login()
        return

    user = st.session_state["user"]

    with st.sidebar:
        st.markdown(f"**{user['nombre']}**")
        st.caption(f"{user['email']} · rol `{user['rol']}`")
        st.caption(
            f"📁 {db_info['total_movimientos']} mov. · {db_info['total_archivos']} archivos"
        )
        if st.button("Cerrar sesión"):
            del st.session_state["user"]
            st.rerun()

    tabs_admin = [
        "Dashboard",
        "Subir archivos",
        "Archivos importados",
        "Movimientos",
        "Por revisar",
        "Reglas y categorías",
        "Usuarios/Roles",
        "Exportar",
    ]
    tab_objects = st.tabs(tabs_admin)

    with tab_objects[0]:
        render_dashboard(user)

    with tab_objects[1]:
        if user["rol"] == "admin":
            render_subir_archivos(user)
        else:
            st.error("No tiene permisos para subir archivos.")

    with tab_objects[2]:
        render_archivos_importados()

    with tab_objects[3]:
        render_movimientos(user)

    with tab_objects[4]:
        render_placeholder("Por revisar", "Movimientos sin clasificar — próximamente.")

    with tab_objects[5]:
        render_reglas_categorias(user)

    with tab_objects[6]:
        render_usuarios_roles(user)

    with tab_objects[7]:
        render_placeholder("Exportar", "Exportación Excel/CSV — próximamente.")


if __name__ == "__main__":
    main()
