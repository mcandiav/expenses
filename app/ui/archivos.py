import json

import pandas as pd
import streamlit as st

from app.repositories import archivo_repository
from app.services.archivo_service import ArchivoService
from app.ui.inspector_report import render_reporte_inspeccion


def render_archivos_importados(user: dict) -> None:
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

    mov_count = ArchivoService.contar_movimientos(archivo_id)

    col1, col2, col3 = st.columns(3)
    col1.write(f"**Hash:** `{detalle['hash_archivo'][:16]}…`")
    col2.write(f"**Fecha referencial:** {detalle.get('fecha_referencial') or '—'}")
    col3.write(f"**Movimientos:** {mov_count}")

    st.caption(f"**Observación:** {detalle.get('observacion') or '—'}")

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

    if user.get("rol") == "admin":
        st.divider()
        st.markdown("#### Acciones")
        col_rep, col_del = st.columns(2)
        with col_rep:
            if st.button("Reprocesar movimientos desde staging", key="arch_reprocesar"):
                from app.services.normalization_service import normalizar_archivo

                n = normalizar_archivo(archivo_id)
                st.success(f"Se normalizaron {n} movimiento(s).")
                st.rerun()
        with col_del:
            if st.button("Eliminar archivo completo", type="primary", key="arch_btn_del"):
                st.session_state["arch_confirm_del_id"] = archivo_id

        st.caption(
            "Eliminar archivo: borra registro, movimientos y staging (permite volver a subirlo). "
            "Para borrar solo movimientos normalizados, use **Movimientos** con filtro por archivo."
        )

        if st.session_state.get("arch_confirm_del_id") == archivo_id:
            st.error(
                f"¿Confirma eliminar **{detalle['nombre_archivo']}** "
                f"({mov_count} movimiento(s))? Esta acción no se puede deshacer."
            )
            c1, c2 = st.columns(2)
            if c1.button("Sí, eliminar", key="arch_ok_del"):
                try:
                    resumen = ArchivoService.eliminar_archivo_completo(
                        archivo_id, usuario_id=user.get("id")
                    )
                    st.session_state.pop("arch_confirm_del_id", None)
                    st.success(
                        f"Archivo eliminado: {resumen['movimientos_eliminados']} movimiento(s)."
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if c2.button("Cancelar", key="arch_cancel_del"):
                st.session_state.pop("arch_confirm_del_id", None)
                st.rerun()
