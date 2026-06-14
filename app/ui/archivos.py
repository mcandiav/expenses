import json

import pandas as pd
import streamlit as st

from app.repositories import archivo_repository
from app.ui.inspector_report import render_reporte_inspeccion


def render_archivos_importados() -> None:
    st.subheader("Archivos importados")
    archivos = archivo_repository.list_archivos()

    if not archivos:
        st.info("Aún no hay archivos importados.")
        return

    df = pd.DataFrame(archivos)
    df_display = df.rename(
        columns={
            "id": "ID",
            "fecha_importacion": "Fecha carga",
            "nombre_archivo": "Archivo",
            "banco_inferido": "Banco",
            "tipo_fuente_inferido": "Tipo fuente",
            "estado": "Estado",
            "filas_leidas": "Filas staging",
            "filas_staging": "Filas DB",
            "usuario_email": "Usuario",
        }
    )
    st.dataframe(
        df_display[
            ["ID", "Fecha carga", "Archivo", "Banco", "Tipo fuente", "Estado", "Filas staging", "Usuario"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.markdown("#### Detalle y reporte de inspección")
    opciones = {f"{a['id']} — {a['nombre_archivo']} ({a['estado']})": a["id"] for a in archivos}
    seleccion = st.selectbox("Seleccionar archivo", list(opciones.keys()))
    archivo_id = opciones[seleccion]
    detalle = archivo_repository.get_by_id(archivo_id)

    if not detalle:
        return

    col1, col2, col3 = st.columns(3)
    col1.write(f"**Hash:** `{detalle['hash_archivo'][:16]}…`")
    col2.write(f"**Fecha referencial:** {detalle.get('fecha_referencial') or '—'}")
    col3.write(f"**Observación:** {detalle.get('observacion') or '—'}")

    if detalle.get("mensaje_error"):
        st.error(detalle["mensaje_error"])

    if detalle.get("reporte_inspeccion_json"):
        render_reporte_inspeccion(json.loads(detalle["reporte_inspeccion_json"]))
    else:
        reporte = archivo_repository.get_reporte_inspeccion(archivo_id)
        if reporte:
            render_reporte_inspeccion(reporte)
        else:
            st.warning("Sin reporte de inspección almacenado.")
