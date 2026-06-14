import pandas as pd
import streamlit as st

from app.services.dashboard_service import DashboardService


def _format_monto(valor: float | int | None) -> str:
    if valor is None:
        return "$ 0"
    return f"$ {int(valor):,}".replace(",", ".")


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            .dash-hero {
                padding: 1.25rem 1.5rem;
                border-radius: 18px;
                background: linear-gradient(135deg, #102a43 0%, #16324f 42%, #1d4ed8 100%);
                color: #f8fafc;
                margin-bottom: 1rem;
            }
            .dash-hero h2 {
                margin: 0;
                font-size: 1.75rem;
            }
            .dash-hero p {
                margin: 0.4rem 0 0;
                color: rgba(248, 250, 252, 0.88);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(user: dict) -> None:
    _inject_styles()
    resumen = DashboardService.obtener_resumen()

    st.markdown(
        f"""
        <div class="dash-hero">
            <h2>Dashboard</h2>
            <p>Resumen de importaciones y categorización · {user['nombre']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if resumen.ultima_importacion:
        st.caption(f"Última importación: **{resumen.ultima_importacion}**")
    else:
        st.caption("Aún no hay importaciones registradas.")

    st.markdown("#### Archivos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total subidos", resumen.total_archivos)
    c2.metric("Procesados OK", resumen.archivos_procesados)
    c3.metric("Con error", resumen.archivos_con_error)

    st.markdown("#### Movimientos")
    c4, c5, c6, c7 = st.columns(4)
    c4.metric("Extraídos (staging)", resumen.movimientos_extraidos)
    c5.metric("Categorizados", resumen.movimientos_categorizados)
    c6.metric("Por revisar", resumen.movimientos_por_revisar)
    c7.metric("Duplicados", resumen.movimientos_duplicados)

    if resumen.movimientos_normalizados == 0 and resumen.movimientos_extraidos > 0:
        st.info(
            "Hay filas en staging (`movimiento_raw`) pendientes de normalización. "
            "Los montos por categoría y banco aparecerán cuando se implemente el normalizador."
        )

    st.divider()
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("#### Monto por categoría")
        if resumen.monto_por_categoria:
            df_cat = pd.DataFrame(resumen.monto_por_categoria)
            df_cat["monto_label"] = df_cat["monto_total"].apply(_format_monto)
            st.bar_chart(df_cat.set_index("categoria")["monto_total"])
            st.dataframe(
                df_cat[["categoria", "cantidad", "monto_label"]].rename(
                    columns={"categoria": "Categoría", "cantidad": "Movimientos", "monto_label": "Monto"}
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Sin movimientos normalizados con monto aún.")

    with col_der:
        st.markdown("#### Monto por banco")
        if resumen.monto_por_banco:
            df_banco = pd.DataFrame(resumen.monto_por_banco)
            df_banco["monto_label"] = df_banco["monto_total"].apply(_format_monto)
            st.bar_chart(df_banco.set_index("banco")["monto_total"])
            st.dataframe(
                df_banco[["banco", "cantidad", "monto_label"]].rename(
                    columns={"banco": "Banco", "cantidad": "Movimientos", "monto_label": "Monto"}
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Sin movimientos normalizados con monto aún.")

    st.divider()
    st.markdown("#### Últimas importaciones")
    if resumen.ultimos_archivos:
        df_arch = pd.DataFrame(resumen.ultimos_archivos)
        st.dataframe(
            df_arch.rename(
                columns={
                    "nombre_archivo": "Archivo",
                    "banco_inferido": "Banco",
                    "estado": "Estado",
                    "filas_leidas": "Filas",
                    "fecha_importacion": "Fecha",
                    "usuario_email": "Usuario",
                }
            )[["Fecha", "Archivo", "Banco", "Estado", "Filas", "Usuario"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No hay archivos importados todavía.")
