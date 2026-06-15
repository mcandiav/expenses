import pandas as pd
import streamlit as st

from app.services.categoria_service import CategoriaService, ReglaService
from app.services.categorization_service import clasificar_glosa


def _render_categorias() -> None:
    st.markdown("Catálogo maestro de categorías. Las reglas y movimientos referencian categorías por ID.")

    service = CategoriaService()
    mostrar_inactivas = st.checkbox("Mostrar categorías inactivas", value=True, key="cat_mostrar_inactivas")

    categorias = service.listar(incluir_inactivas=mostrar_inactivas)
    if categorias:
        df = pd.DataFrame(categorias)
        df["activa"] = df["activa"].astype(bool)
        df_display = df.rename(
            columns={
                "id": "ID",
                "nombre": "Nombre",
                "uso": "Uso",
                "activa": "Activa",
                "total_reglas": "Reglas",
                "total_movimientos": "Movimientos",
            }
        )
        st.dataframe(
            df_display[["ID", "Nombre", "Uso", "Activa", "Reglas", "Movimientos"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No hay categorías registradas.")

    st.divider()
    st.markdown("#### Agregar categoría")
    with st.form("form_nueva_categoria", clear_on_submit=True):
        nombre = st.text_input("Nombre *")
        uso = st.text_area("Uso / descripción")
        if st.form_submit_button("Agregar categoría"):
            try:
                service.crear(nombre, uso or None)
                st.success(f"Categoría '{nombre.strip()}' creada.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.markdown("#### Editar categoría")
    editables = service.listar(incluir_inactivas=True)
    if editables:
        opciones = {f"{c['id']} — {c['nombre']}": c["id"] for c in editables}
        seleccion = st.selectbox("Seleccionar categoría", list(opciones.keys()), key="cat_edit_sel")
        cat_id = opciones[seleccion]
        actual = next(c for c in editables if c["id"] == cat_id)

        with st.form("form_editar_categoria"):
            nuevo_nombre = st.text_input("Nombre *", value=actual["nombre"])
            nuevo_uso = st.text_area("Uso / descripción", value=actual["uso"] or "")
            activa = st.checkbox("Activa", value=bool(actual["activa"]))
            col1, col2 = st.columns(2)
            guardar = col1.form_submit_button("Guardar cambios")
            eliminar = col2.form_submit_button("Eliminar (solo sin uso)")

        if guardar:
            try:
                service.actualizar(cat_id, nuevo_nombre, nuevo_uso or None, activa)
                st.success("Categoría actualizada.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if eliminar:
            try:
                service.eliminar(cat_id)
                st.success("Categoría eliminada.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def _render_reglas(user_id: int | None) -> None:
    st.markdown(
        "Reglas de matching por glosa. El patrón se busca dentro de la glosa normalizada (contiene). "
        "Banco vacío = regla global."
    )

    regla_service = ReglaService()
    categoria_service = CategoriaService()
    mostrar_inactivas = st.checkbox("Mostrar reglas inactivas", value=True, key="reg_mostrar_inactivas")

    reglas = regla_service.listar(incluir_inactivas=mostrar_inactivas)
    if reglas:
        df = pd.DataFrame(reglas)
        df["activa"] = df["activa"].astype(bool)
        df_display = df.rename(
            columns={
                "id": "ID",
                "banco_opcional": "Banco",
                "patron": "Patrón glosa",
                "categoria_nombre": "Categoría",
                "prioridad": "Prioridad",
                "activa": "Activa",
                "comentario": "Comentario",
            }
        )
        st.dataframe(
            df_display[["ID", "Banco", "Patrón glosa", "Categoría", "Prioridad", "Activa", "Comentario"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No hay reglas registradas.")

    categorias_activas = [c for c in categoria_service.listar(incluir_inactivas=False)]
    cat_map = {c["nombre"]: c["id"] for c in categorias_activas}

    st.divider()
    st.markdown("#### Agregar regla")
    with st.form("form_nueva_regla", clear_on_submit=True):
        banco = st.text_input("Banco (opcional)", placeholder="ITAU, BCI...")
        patron = st.text_input("Patrón glosa *", placeholder="pepito")
        categoria_nombre = st.selectbox("Categoría *", list(cat_map.keys()) if cat_map else [])
        prioridad = st.number_input("Prioridad", min_value=1, max_value=9999, value=100)
        comentario = st.text_input("Comentario")
        if st.form_submit_button("Agregar regla"):
            if not cat_map:
                st.error("Debe existir al menos una categoría activa.")
            else:
                try:
                    resultado = regla_service.crear_y_aplicar(
                        patron=patron,
                        categoria_id=cat_map[categoria_nombre],
                        prioridad=int(prioridad),
                        banco_opcional=banco or None,
                        comentario=comentario or None,
                        usuario_id=user_id,
                    )
                    if resultado.duplicada:
                        st.warning(
                            f"Ya existía una regla igual (ID {resultado.regla['id']}). "
                            f"No se creó una duplicada."
                        )
                    if resultado.movimientos_actualizados:
                        st.success(
                            f"Regla aplicada a {resultado.movimientos_actualizados} movimiento(s)."
                        )
                    else:
                        st.success("Regla creada.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.divider()
    st.markdown("#### Editar regla")
    if reglas:
        opciones = {
            f"{r['id']} — {(r['banco_opcional'] or 'GLOBAL')} / {r['patron']} → {r['categoria_nombre']}": r["id"]
            for r in reglas
        }
        seleccion = st.selectbox("Seleccionar regla", list(opciones.keys()), key="reg_edit_sel")
        regla_id = opciones[seleccion]
        actual = next(r for r in reglas if r["id"] == regla_id)

        with st.form("form_editar_regla"):
            banco = st.text_input("Banco (opcional)", value=actual["banco_opcional"] or "")
            patron = st.text_input("Patrón glosa *", value=actual["patron"])
            idx_cat = list(cat_map.keys()).index(actual["categoria_nombre"]) if actual["categoria_nombre"] in cat_map else 0
            categoria_nombre = st.selectbox("Categoría *", list(cat_map.keys()), index=idx_cat if cat_map else 0)
            prioridad = st.number_input("Prioridad", min_value=1, max_value=9999, value=int(actual["prioridad"]))
            activa = st.checkbox("Activa", value=bool(actual["activa"]))
            comentario = st.text_input("Comentario", value=actual["comentario"] or "")
            col1, col2 = st.columns(2)
            guardar = col1.form_submit_button("Guardar cambios")
            eliminar = col2.form_submit_button("Eliminar regla")

        if guardar and cat_map:
            try:
                regla_service.actualizar(
                    regla_id=regla_id,
                    patron=patron,
                    categoria_id=cat_map[categoria_nombre],
                    prioridad=int(prioridad),
                    banco_opcional=banco or None,
                    producto_opcional=actual.get("producto_opcional"),
                    subtipo_fuente_opcional=actual.get("subtipo_fuente_opcional"),
                    activa=activa,
                    comentario=comentario or None,
                )
                st.success("Regla actualizada.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if eliminar:
            regla_service.eliminar(regla_id)
            st.success("Regla eliminada.")
            st.rerun()

    st.divider()
    st.markdown("#### Probar regla")
    with st.form("form_probar_regla"):
        glosa_prueba = st.text_input("Glosa de ejemplo", placeholder="COMPRA PEPITO SPA")
        banco_prueba = st.text_input("Banco (opcional)", placeholder="ITAU")
        if st.form_submit_button("Probar"):
            resultado = clasificar_glosa(glosa_prueba, banco=banco_prueba or None)
            if resultado.categoria_nombre:
                st.success(
                    f"**Categoría:** {resultado.categoria_nombre}  \n"
                    f"**Método:** {resultado.metodo}  \n"
                    f"**Regla ID:** {resultado.regla_id or '—'}  \n"
                    f"**Patrón:** {resultado.patron or '—'}"
                )
            else:
                st.warning("Sin categoría asignada.")


def render_reglas_categorias(user: dict) -> None:
    if user["rol"] != "admin":
        st.error("No tiene permisos para administrar categorías y reglas.")
        return

    st.subheader("Reglas y categorías")
    tab_categorias, tab_reglas = st.tabs(["Categorías", "Reglas"])

    with tab_categorias:
        _render_categorias()

    with tab_reglas:
        _render_reglas(user.get("id"))
