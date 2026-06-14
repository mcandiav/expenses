import streamlit as st

from app.services.import_service import importar_archivo, inspeccionar_solo
from app.ui.inspector_report import render_reporte_inspeccion


BANCOS_SUGERIDOS = ["", "BCI", "ITAU", "SANTANDER", "BANCO DE CHILE", "SCOTIABANK", "BICE"]
TIPOS_FUENTE_SUGERIDOS = [
    "",
    "Tarjeta / movimientos facturados",
    "Cartola",
    "Cuenta corriente",
    "Tarjeta",
]


def render_subir_archivos(user: dict) -> None:
    st.subheader("Subir archivos")
    st.markdown(
        "Importe archivos **.xls**, **.xlsx** o **.csv**. "
        "El sistema detecta el formato real del contenido (incluye `.xls` con estructura OOXML/ZIP tipo BCI). "
        "**PDF no soportado en V1.**"
    )

    archivos = st.file_uploader(
        "Seleccionar archivos",
        type=["xls", "xlsx", "csv"],
        accept_multiple_files=True,
        key="upload_files",
    )

    col1, col2 = st.columns(2)
    with col1:
        banco = st.selectbox("Banco (opcional, sobreescribe inferencia)", BANCOS_SUGERIDOS)
    with col2:
        tipo_fuente = st.selectbox("Tipo de fuente (opcional)", TIPOS_FUENTE_SUGERIDOS)
    observacion = st.text_input("Observación (opcional)")

    col_ins, col_imp = st.columns(2)
    inspeccionar = col_ins.button("Inspeccionar sin guardar", use_container_width=True)
    importar = col_imp.button("Subir e importar", type="primary", use_container_width=True)

    if not archivos:
        if inspeccionar or importar:
            st.warning("Seleccione al menos un archivo.")
        return

    if inspeccionar:
        st.divider()
        st.markdown("### Reporte de inspección (vista previa)")
        for uploaded in archivos:
            content = uploaded.getvalue()
            reporte = inspeccionar_solo(content, uploaded.name)
            with st.expander(f"📄 {uploaded.name}", expanded=True):
                render_reporte_inspeccion(reporte)

    if importar:
        st.divider()
        st.markdown("### Resultado de importación")
        for uploaded in archivos:
            content = uploaded.getvalue()
            resultado = importar_archivo(
                content=content,
                nombre_archivo=uploaded.name,
                usuario_id=user["id"],
                banco=banco or None,
                tipo_fuente=tipo_fuente or None,
                observacion=observacion or None,
            )
            with st.expander(f"📄 {uploaded.name}", expanded=True):
                if resultado.duplicado:
                    st.warning(resultado.mensaje)
                elif resultado.exito:
                    st.success(resultado.mensaje)
                else:
                    st.error(resultado.mensaje)

                if resultado.reporte:
                    render_reporte_inspeccion(resultado.reporte)

                if resultado.archivo_id:
                    st.caption(f"ID archivo importado: {resultado.archivo_id}")
