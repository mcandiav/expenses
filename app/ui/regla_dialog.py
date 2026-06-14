import streamlit as st

from app.services.categoria_service import CategoriaService, ReglaService
from app.services.categorization_service import clasificar_glosa
from app.services.movimiento_service import MovimientoService


def sugerir_patron(glosa_normalizada: str, glosa_original: str) -> str:
    base = (glosa_normalizada or glosa_original or "").strip()
    if not base:
        return ""
    palabras = [p for p in base.split() if len(p) > 2]
    if len(palabras) >= 2:
        return " ".join(palabras[:2])
    return palabras[0] if palabras else base[:40]


def _render_contenido_dialog(mov: dict, user: dict) -> None:
    st.markdown("Asigne una categoría creando una regla de matching. Quedará disponible en **Reglas y categorías**.")
    st.info(
        f"**Glosa:** {mov.get('glosa_original') or '—'}  \n"
        f"**Banco:** {mov.get('banco') or '—'} · **Monto:** {mov.get('monto')} {mov.get('moneda') or ''}"
    )

    regla_service = ReglaService()
    categoria_service = CategoriaService()
    categorias_activas = categoria_service.listar(incluir_inactivas=False)
    cat_map = {c["nombre"]: c["id"] for c in categorias_activas if c["nombre"] != "Por revisar"}

    patron_default = sugerir_patron(
        mov.get("glosa_normalizada") or "",
        mov.get("glosa_original") or "",
    )
    banco_default = mov.get("banco") if mov.get("banco") not in (None, "", "Sin banco") else ""

    tab_regla, tab_categoria = st.tabs(["Nueva regla", "Nueva categoría"])

    with tab_categoria:
        with st.form("dialog_nueva_categoria"):
            nombre_cat = st.text_input("Nombre categoría *")
            uso_cat = st.text_input("Uso / descripción")
            if st.form_submit_button("Crear categoría"):
                try:
                    categoria_service.crear(nombre_cat, uso_cat or None)
                    st.success(f"Categoría '{nombre_cat.strip()}' creada. Vaya a la pestaña Nueva regla.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with tab_regla:
        if not cat_map:
            st.warning("Debe existir al menos una categoría activa (distinta de Por revisar).")
            return

        with st.form("dialog_nueva_regla"):
            banco = st.text_input("Banco (opcional)", value=banco_default, placeholder="BCI, ITAU...")
            patron = st.text_input("Patrón glosa *", value=patron_default)
            categoria_nombre = st.selectbox("Categoría *", list(cat_map.keys()))
            prioridad = st.number_input("Prioridad", min_value=1, max_value=9999, value=100)
            comentario = st.text_input(
                "Comentario",
                value=f"Creada desde movimiento #{mov.get('id')}",
            )
            aplicar_ahora = st.checkbox("Aplicar al movimiento actual", value=True)

            if st.form_submit_button("Guardar regla", type="primary"):
                if not patron.strip():
                    st.error("El patrón es obligatorio.")
                    return
                try:
                    regla = regla_service.crear(
                        patron=patron,
                        categoria_id=cat_map[categoria_nombre],
                        prioridad=int(prioridad),
                        banco_opcional=banco or None,
                        comentario=comentario or None,
                        usuario_id=user.get("id"),
                    )
                    if aplicar_ahora and mov.get("id"):
                        MovimientoService.reclasificar_movimiento(int(mov["id"]))

                    st.success(
                        f"Regla creada (ID {regla['id']}). "
                        f"Patrón `{regla['patron']}` → {categoria_nombre}."
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        st.divider()
        st.caption("Vista previa con la regla actual")
        preview_patron = st.text_input("Probar patrón", value=patron_default, key="dialog_preview_patron")
        preview_banco = st.text_input("Probar banco", value=banco_default, key="dialog_preview_banco")
        resultado = clasificar_glosa(
            mov.get("glosa_original") or preview_patron,
            banco=preview_banco or None,
        )
        st.write(f"Resultado: **{resultado.categoria_nombre or 'Sin match'}**")


if hasattr(st, "dialog"):

    @st.dialog("Crear regla desde movimiento", width="large")
    def abrir_dialog_regla(mov: dict, user: dict) -> None:
        _render_contenido_dialog(mov, user)

else:

    def abrir_dialog_regla(mov: dict, user: dict) -> None:
        with st.expander("Crear regla desde movimiento", expanded=True):
            _render_contenido_dialog(mov, user)
