import pandas as pd
import streamlit as st

from app.services.usuario_service import UsuarioService

ROLES_DISPONIBLES = ["admin", "usuario"]

PERMISOS_ROLES = [
    ("Ver dashboard", "Sí", "Sí"),
    ("Subir archivos", "Sí", "No"),
    ("Ver archivos importados", "Sí", "Sí"),
    ("Ver movimientos", "Sí", "Sí"),
    ("Filtrar movimientos", "Sí", "Sí"),
    ("Exportar Excel", "Sí", "Sí"),
    ("Editar categoría/observación", "Sí", "No"),
    ("Administrar categorías y reglas", "Sí", "No"),
    ("Administrar usuarios", "Sí", "No"),
    ("Resolver duplicados", "Sí", "No"),
]


def _render_usuarios(actor: dict) -> None:
    service = UsuarioService()
    mostrar_inactivos = st.checkbox("Mostrar usuarios inactivos", value=True, key="usr_mostrar_inactivos")

    usuarios = service.listar_usuarios(incluir_inactivos=mostrar_inactivos)
    if usuarios:
        df = pd.DataFrame(usuarios)
        df["activo"] = df["activo"].astype(bool)
        df_display = df.rename(
            columns={
                "id": "ID",
                "email": "Email",
                "nombre": "Nombre",
                "rol": "Rol",
                "activo": "Activo",
                "fecha_creacion": "Creado",
                "fecha_ultimo_login": "Último login",
            }
        )
        st.dataframe(
            df_display[["ID", "Email", "Nombre", "Rol", "Activo", "Creado", "Último login"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No hay usuarios registrados.")

    st.divider()
    st.markdown("#### Crear usuario")
    with st.form("form_nuevo_usuario", clear_on_submit=True):
        email = st.text_input("Email *")
        nombre = st.text_input("Nombre *")
        password = st.text_input("Contraseña *", type="password")
        password2 = st.text_input("Confirmar contraseña *", type="password")
        rol = st.selectbox("Rol *", ROLES_DISPONIBLES)
        if st.form_submit_button("Crear usuario"):
            if password != password2:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    service.crear(email, nombre, password, rol, actor["id"])
                    st.success(f"Usuario '{email.strip()}' creado.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.divider()
    st.markdown("#### Editar usuario")
    editables = service.listar_usuarios(incluir_inactivos=True)
    if editables:
        opciones = {f"{u['id']} — {u['email']} ({u['rol']})": u["id"] for u in editables}
        seleccion = st.selectbox("Seleccionar usuario", list(opciones.keys()), key="usr_edit_sel")
        usuario_id = opciones[seleccion]
        actual = next(u for u in editables if u["id"] == usuario_id)

        with st.form("form_editar_usuario"):
            nuevo_email = st.text_input("Email *", value=actual["email"])
            nuevo_nombre = st.text_input("Nombre *", value=actual["nombre"])
            idx_rol = ROLES_DISPONIBLES.index(actual["rol"]) if actual["rol"] in ROLES_DISPONIBLES else 0
            nuevo_rol = st.selectbox("Rol *", ROLES_DISPONIBLES, index=idx_rol)
            activo = st.checkbox("Activo", value=bool(actual["activo"]))
            guardar = st.form_submit_button("Guardar cambios")

        if guardar:
            try:
                actualizado = service.actualizar(
                    usuario_id=usuario_id,
                    email=nuevo_email,
                    nombre=nuevo_nombre,
                    rol_nombre=nuevo_rol,
                    activo=activo,
                    actor_id=actor["id"],
                )
                if usuario_id == actor["id"] and (
                    actualizado["email"] != actor["email"]
                    or actualizado["nombre"] != actor["nombre"]
                    or actualizado["rol"] != actor["rol"]
                ):
                    st.session_state["user"] = {
                        **actor,
                        "email": actualizado["email"],
                        "nombre": actualizado["nombre"],
                        "rol": actualizado["rol"],
                    }
                st.success("Usuario actualizado.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

        st.markdown("##### Restablecer contraseña")
        with st.form("form_reset_password"):
            pwd1 = st.text_input("Nueva contraseña", type="password", key="pwd_reset_1")
            pwd2 = st.text_input("Confirmar nueva contraseña", type="password", key="pwd_reset_2")
            if st.form_submit_button("Cambiar contraseña"):
                if pwd1 != pwd2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        service.cambiar_password(usuario_id, pwd1, actor["id"])
                        st.success("Contraseña actualizada.")
                    except ValueError as exc:
                        st.error(str(exc))

        auditoria = service.obtener_auditoria(usuario_id)
        if auditoria:
            with st.expander("Historial de cambios (auditoría)"):
                df_aud = pd.DataFrame(auditoria)
                st.dataframe(
                    df_aud[["fecha", "accion", "usuario_email", "antes_json", "despues_json"]],
                    use_container_width=True,
                    hide_index=True,
                )


def _render_roles() -> None:
    service = UsuarioService()
    roles = service.listar_roles()

    st.markdown("Roles definidos en V1. No editables desde la interfaz.")

    if roles:
        for rol in roles:
            st.markdown(f"**{rol['nombre']}** — {rol['descripcion'] or 'Sin descripción'}")

    st.divider()
    st.markdown("#### Matriz de permisos V1")
    df = pd.DataFrame(PERMISOS_ROLES, columns=["Función", "admin", "usuario"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_usuarios_roles(actor: dict) -> None:
    if actor["rol"] != "admin":
        st.error("No tiene permisos para administrar usuarios.")
        return

    st.subheader("Usuarios/Roles")
    tab_usuarios, tab_roles = st.tabs(["Usuarios", "Roles"])

    with tab_usuarios:
        _render_usuarios(actor)

    with tab_roles:
        _render_roles()
