import math

import pandas as pd
import streamlit as st

from app.repositories.movimiento_repository import FiltrosMovimiento
from app.services.movimiento_service import MovimientoService
from app.ui.regla_dialog import abrir_dialog_regla

COLUMNAS_DISPLAY = {
    "fecha": "Fecha",
    "banco": "Banco",
    "tipo_fuente": "Tipo fuente",
    "archivo_origen": "Archivo origen",
    "glosa_original": "Glosa original",
    "glosa_normalizada": "Glosa normalizada",
    "monto": "Monto",
    "moneda": "Moneda",
    "monto_moneda_origen": "Monto moneda origen",
    "categoria": "Categoría",
    "estado": "Estado",
    "duplicado": "Duplicado",
    "revisado": "Revisado",
    "regla_aplicada": "Regla aplicada",
    "observacion": "Observación",
    "fila_origen": "Fila origen",
}


def _init_session() -> None:
    defaults = {
        "mov_pagina": 1,
        "mov_por_pagina": 50,
        "mov_orden_col": "fecha",
        "mov_orden_desc": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _valor_fecha(key: str) -> str | None:
    valor = st.session_state.get(key)
    if valor is None:
        return None
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    texto = str(valor).strip()
    return texto or None


def _leer_filtros(opciones: dict) -> FiltrosMovimiento:
    archivos_map = {a["nombre_archivo"]: a["id"] for a in opciones.get("archivos", [])}
    archivo_sel = st.session_state.get("mov_f_archivo", "")
    archivo_id = archivos_map.get(archivo_sel) if archivo_sel else None

    revisado_sel = st.session_state.get("mov_f_revisado", "Todos")
    revisado = None if revisado_sel == "Todos" else revisado_sel == "Sí"

    por_rev_sel = st.session_state.get("mov_f_por_revisar", "Todos")
    por_revisar = None if por_rev_sel == "Todos" else por_rev_sel == "Sí"

    monto_min = st.session_state.get("mov_f_monto_min", 0.0) or 0.0
    monto_max = st.session_state.get("mov_f_monto_max", 0.0) or 0.0

    return FiltrosMovimiento(
        fecha_desde=_valor_fecha("mov_f_fecha_desde"),
        fecha_hasta=_valor_fecha("mov_f_fecha_hasta"),
        banco=st.session_state.get("mov_f_banco") or None,
        archivo_id=archivo_id,
        categoria=st.session_state.get("mov_f_categoria") or None,
        glosa_contiene=(st.session_state.get("mov_f_glosa") or "").strip() or None,
        monto_min=float(monto_min) if monto_min > 0 else None,
        monto_max=float(monto_max) if monto_max > 0 else None,
        moneda=st.session_state.get("mov_f_moneda") or None,
        estado=st.session_state.get("mov_f_estado") or None,
        duplicado=st.session_state.get("mov_f_duplicado") or None,
        revisado=revisado,
        por_revisar=por_revisar,
    )


def render_movimientos(user: dict) -> None:
    _init_session()
    service = MovimientoService()

    nuevos = service.sincronizar_desde_staging()
    if nuevos:
        st.toast(f"{nuevos} movimientos normalizados desde staging.", icon="✅")

    st.subheader("Movimientos")
    st.caption("Listado consolidado de todas las fuentes importadas.")

    opciones = service.opciones_filtro()

    toolbar1, toolbar2, toolbar3 = st.columns([1, 1.2, 1.2])
    with toolbar1:
        por_pagina = st.selectbox(
            "Registros por página",
            options=service.TAMANOS_PAGINA,
            index=service.TAMANOS_PAGINA.index(st.session_state["mov_por_pagina"]),
            key="mov_por_pagina_sel",
        )
        if por_pagina != st.session_state["mov_por_pagina"]:
            st.session_state["mov_por_pagina"] = por_pagina
            st.session_state["mov_pagina"] = 1

    with toolbar2:
        orden_col = st.selectbox(
            "Ordenar por",
            options=service.COLUMNAS,
            format_func=lambda c: COLUMNAS_DISPLAY.get(c, c),
            index=service.COLUMNAS.index(st.session_state["mov_orden_col"])
            if st.session_state["mov_orden_col"] in service.COLUMNAS
            else 0,
            key="mov_orden_col_sel",
        )
        st.session_state["mov_orden_col"] = orden_col

    with toolbar3:
        orden_dir = st.radio(
            "Dirección",
            options=["Descendente", "Ascendente"],
            horizontal=True,
            index=0 if st.session_state["mov_orden_desc"] else 1,
            key="mov_orden_dir",
        )
        st.session_state["mov_orden_desc"] = orden_dir == "Descendente"

    with st.expander("Filtros por columna", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            st.date_input("Fecha desde", key="mov_f_fecha_desde", value=None)
            st.date_input("Fecha hasta", key="mov_f_fecha_hasta", value=None)
            bancos = [""] + opciones.get("bancos", [])
            st.selectbox("Banco", bancos, key="mov_f_banco")
            archivos = [""] + [a["nombre_archivo"] for a in opciones.get("archivos", [])]
            st.selectbox("Archivo origen", archivos, key="mov_f_archivo")
        with f2:
            categorias = [""] + opciones.get("categorias", [])
            st.selectbox("Categoría", categorias, key="mov_f_categoria")
            st.text_input("Glosa contiene", key="mov_f_glosa")
            monedas = [""] + opciones.get("monedas", [])
            st.selectbox("Moneda", monedas, key="mov_f_moneda")
        with f3:
            st.number_input("Monto mínimo", min_value=0.0, value=0.0, step=1000.0, key="mov_f_monto_min")
            st.number_input("Monto máximo", min_value=0.0, value=0.0, step=1000.0, key="mov_f_monto_max")
            estados = [""] + opciones.get("estados", [])
            st.selectbox("Estado", estados, key="mov_f_estado")
            duplicados = [""] + opciones.get("duplicados", [])
            st.selectbox("Duplicado", duplicados, key="mov_f_duplicado")
            st.selectbox("Revisado", ["Todos", "Sí", "No"], key="mov_f_revisado")
            st.selectbox("Por revisar", ["Todos", "Sí", "No"], key="mov_f_por_revisar")

        c_apply, c_clear = st.columns(2)
        if c_clear.button("Limpiar filtros", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith("mov_f_"):
                    del st.session_state[key]
            st.session_state["mov_pagina"] = 1
            st.rerun()
        if c_apply.button("Aplicar filtros", type="primary", use_container_width=True):
            st.session_state["mov_pagina"] = 1
            st.rerun()

    filtros = _leer_filtros(opciones)
    movimientos, total = service.listar(
        filtros=filtros,
        orden_columna=st.session_state["mov_orden_col"],
        orden_desc=st.session_state["mov_orden_desc"],
        pagina=st.session_state["mov_pagina"],
        por_pagina=st.session_state["mov_por_pagina"],
    )

    total_paginas = max(1, math.ceil(total / st.session_state["mov_por_pagina"]))
    st.markdown(
        f"**{total}** movimientos encontrados · página **{st.session_state['mov_pagina']}** de **{total_paginas}**"
    )

    if movimientos:
        df = pd.DataFrame(movimientos)
        df["revisado"] = df["revisado"].astype(bool)
        columnas_show = [c for c in service.COLUMNAS if c in df.columns]
        df_show = df[columnas_show].rename(columns=COLUMNAS_DISPLAY)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        sin_categoria = [m for m in movimientos if MovimientoService.movimiento_sin_categoria(m)]
        if sin_categoria and user.get("rol") == "admin":
            st.markdown("#### Sin categoría — crear regla")
            st.caption(
                "Movimientos de esta página sin regla aplicada. Use **Crear regla** para abrir el formulario "
                "sin salir de Movimientos."
            )
            for mov in sin_categoria:
                col_a, col_b, col_c = st.columns([3, 2, 1])
                col_a.write(
                    f"**#{mov['id']}** · {mov.get('fecha')} · "
                    f"{mov.get('glosa_original') or '—'}"
                )
                col_b.write(f"{mov.get('monto')} {mov.get('moneda') or ''} · {mov.get('banco') or '—'}")
                if col_c.button("➕ Crear regla", key=f"btn_regla_mov_{mov['id']}"):
                    abrir_dialog_regla(mov, user)
        elif sin_categoria:
            st.caption(f"{len(sin_categoria)} movimiento(s) sin categoría en esta página.")
    else:
        st.info("No hay movimientos que coincidan con los filtros. Importe archivos desde **Subir archivos**.")

    pag_col1, pag_col2, pag_col3 = st.columns([1, 2, 1])
    with pag_col1:
        if st.button("← Anterior", disabled=st.session_state["mov_pagina"] <= 1):
            st.session_state["mov_pagina"] -= 1
            st.rerun()
    with pag_col2:
        ir_pag = st.number_input(
            "Ir a página",
            min_value=1,
            max_value=total_paginas,
            value=min(st.session_state["mov_pagina"], total_paginas),
            step=1,
            key="mov_pagina_input",
        )
        if st.button("Ir", key="mov_ir_pagina"):
            st.session_state["mov_pagina"] = int(ir_pag)
            st.rerun()
    with pag_col3:
        if st.button("Siguiente →", disabled=st.session_state["mov_pagina"] >= total_paginas):
            st.session_state["mov_pagina"] += 1
            st.rerun()
