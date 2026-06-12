from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Categorizacion de Expensas",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_TITLE = "Categorizacion de Expensas"
APP_SUBTITLE = "Dashboard inicial para importacion, revision y categorizacion de movimientos."


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 2rem;
            }
            .app-hero {
                padding: 1.25rem 1.5rem;
                border-radius: 22px;
                background: linear-gradient(135deg, #102a43 0%, #16324f 42%, #1d4ed8 100%);
                color: #f8fafc;
                box-shadow: 0 16px 45px rgba(16, 42, 67, 0.22);
                margin-bottom: 1rem;
            }
            .app-hero h1 {
                margin: 0;
                font-size: 2rem;
                line-height: 1.05;
            }
            .app-hero p {
                margin: 0.5rem 0 0;
                color: rgba(248, 250, 252, 0.88);
                font-size: 0.98rem;
            }
            .metric-card {
                background: white;
                border: 1px solid rgba(15, 23, 42, 0.08);
                border-radius: 18px;
                padding: 1rem 1rem 0.9rem;
                box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
                min-height: 108px;
            }
            .metric-label {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #64748b;
                margin-bottom: 0.35rem;
            }
            .metric-value {
                font-size: 2rem;
                font-weight: 700;
                color: #0f172a;
                line-height: 1.05;
            }
            .metric-note {
                margin-top: 0.4rem;
                color: #475569;
                font-size: 0.9rem;
            }
            .section-card {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(15, 23, 42, 0.08);
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
            }
            .muted {
                color: #64748b;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sample_kpis() -> dict[str, str]:
    return {
        "archivos": "2",
        "movimientos": "118",
        "por_revisar": "37",
        "duplicados": "4",
        "categorizados": "81",
        "monto_total": "$ 4.82M",
    }


def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["BCI", "Nacionales", "JUMBO KENNEDY", 42890, "CLP", "Supermercado / hogar", "regla"],
            ["BCI", "Nacionales", "META ADS", 155000, "CLP", "Marketing / publicidad", "regla"],
            ["BCI", "Internacionales", "SHOPIFY *STORE", 29900, "USD", "Software / tecnolog\u00eda", "regla"],
            ["BCI", "Nacionales", "PAGO TARJETA", 210000, "CLP", "Por revisar", "pendiente"],
        ],
        columns=["Banco", "Tipo", "Glosa", "Monto", "Moneda", "Categoria", "Estado"],
    )


def render_dashboard() -> None:
    kpi = sample_kpis()

    st.markdown(
        f"""
        <div class="app-hero">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Archivos importados", kpi["archivos"], "BCI nacionales e internacionales cargados.")
    with c2:
        metric_card("Movimientos totales", kpi["movimientos"], "Incluye filas normalizadas y listas para revisar.")
    with c3:
        metric_card("Por revisar", kpi["por_revisar"], "Casos sin regla o con baja confianza.")

    c4, c5, c6 = st.columns(3)
    with c4:
        metric_card("Duplicados detectados", kpi["duplicados"], "Proteccion contra reprocesos accidentales.")
    with c5:
        metric_card("Categorizados", kpi["categorizados"], "Movimientos ya resueltos por regla o revision.")
    with c6:
        metric_card("Monto total", kpi["monto_total"], "Vista consolidada del periodo cargado.")

    st.write("")

    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Actividad reciente")
        st.caption("Borrador visual para el dashboard inicial.")
        st.line_chart(
            pd.DataFrame(
                {
                    "Importaciones": [0, 2, 3, 5, 7, 7, 9],
                    "Revisiones": [0, 0, 1, 2, 4, 6, 8],
                }
            )
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Ultimas importaciones")
        st.dataframe(
            pd.DataFrame(
                [
                    ["BCI_MovimientosFacturadosNacionales_25-03-2026.xls", "BCI", "Procesado", "91 filas"],
                    ["BCI_MovimientosFacturadosInternacionales_23-04-2026.xls", "BCI", "Procesado", "27 filas"],
                ],
                columns=["Archivo", "Banco", "Estado", "Filas"],
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Vista preliminar de movimientos")
    st.caption("Esquema inicial de la grilla que luego tendra filtros y edicion controlada.")
    st.dataframe(sample_dataframe(), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_tabs() -> None:
    tabs = st.tabs(
        [
            "Dashboard",
            "Subir archivos",
            "Archivos importados",
            "Movimientos",
            "Por revisar",
            "Reglas",
            "Usuarios/Roles",
            "Exportar",
        ]
    )

    with tabs[0]:
        render_dashboard()

    placeholder_sections = [
        ("Subir archivos", "Zona de carga y deteccion de formato real."),
        ("Archivos importados", "Listado con hash, estado y detalle de importacion."),
        ("Movimientos", "Grilla principal con filtros y edicion controlada."),
        ("Por revisar", "Casos sin regla para revision manual."),
        ("Reglas", "Administracion de patrones por glosa."),
        ("Usuarios/Roles", "Alta de usuarios y permisos iniciales."),
        ("Exportar", "Exportacion a Excel o CSV segun vista filtrada."),
    ]

    for idx, (title, description) in enumerate(placeholder_sections, start=1):
        with tabs[idx]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader(title)
            st.write(description)
            st.info("Este modulo queda preparado como siguiente paso del desarrollo.")
            st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> None:
    st.sidebar.title(APP_TITLE)
    st.sidebar.caption("Skeleton inicial")
    st.sidebar.markdown(
        """
        **Estado**
        - Login: pendiente
        - Importacion: pendiente
        - Reglas: pendiente
        - Exportacion: pendiente
        """
    )
    st.sidebar.divider()
    st.sidebar.write("Ultima actualizacion")
    st.sidebar.code(datetime.now().strftime("%Y-%m-%d %H:%M"))


def main() -> None:
    inject_styles()
    render_sidebar()
    render_tabs()


if __name__ == "__main__":
    main()
