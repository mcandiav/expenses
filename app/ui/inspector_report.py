import json

import pandas as pd
import streamlit as st

from app.services.file_models import ReporteInspeccion


def render_reporte_inspeccion(reporte: ReporteInspeccion | dict) -> None:
    if isinstance(reporte, ReporteInspeccion):
        data = reporte.to_dict()
    else:
        data = reporte

    col1, col2, col3 = st.columns(3)
    col1.metric("Formato detectado", data.get("formato_detectado", "—"))
    col2.metric("Banco inferido", data.get("banco_inferido") or "—")
    col3.metric("Tipo fuente", data.get("tipo_fuente_inferido") or "—")

    if data.get("subtipo_movimiento"):
        st.caption(f"Subtipo: {data['subtipo_movimiento']} · Fecha ref.: {data.get('fecha_referencial') or '—'}")

    if data.get("errores_lectura"):
        for error in data["errores_lectura"]:
            st.error(error)

    hojas = data.get("hojas") or []
    if not hojas:
        st.warning("No se detectaron hojas o datos tabulares.")
        return

    st.markdown(f"**Hojas detectadas:** {', '.join(data.get('hojas_detectadas', []))}")

    for hoja in hojas:
        with st.expander(f"Hoja: {hoja['nombre']} — {hoja['filas_totales']} filas", expanded=len(hojas) == 1):
            st.write(f"Rango usado: `{hoja.get('rango_usado', '—')}`")
            st.write(f"Fila probable de encabezado: **{hoja.get('fila_encabezado_probable') or '—'}**")

            columnas = hoja.get("columnas_detectadas") or []
            if columnas:
                st.markdown("**Columnas detectadas:**")
                st.code(", ".join(columnas))

            ejemplos = hoja.get("filas_ejemplo") or []
            if ejemplos:
                st.markdown("**Primeras filas de ejemplo:**")
                st.dataframe(pd.DataFrame(ejemplos), use_container_width=True, hide_index=True)


def render_reporte_json(json_text: str) -> None:
    render_reporte_inspeccion(json.loads(json_text))
