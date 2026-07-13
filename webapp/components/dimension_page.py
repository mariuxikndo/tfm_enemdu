"""
webapp/components/dimension_page.py
────────────────────────────────────────────────────────────────────
Plantilla reutilizable para páginas de dimensión ambiental.
Evita duplicar código entre las 5 páginas de dimensión.
"""

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from webapp.components.charts import (
    kpi_card, barras_horizontal, barras_area, mapa_provincias, gauge_indice
)
from webapp.data_layer import (
    cargar_dimension, cargar_por_area, cargar_por_provincia,
    filtrar_dimension, obtener_valor, mostrar_error_sin_datos,
    mostrar_advertencia_filtro_vacio,
)

CSS_GLOBAL = """<style>
.stApp{background-color:#F4F7FB;}
[data-testid="stSidebar"]{background-color:#1A2332;}
[data-testid="stSidebar"] *{color:#E8EDF3!important;}
.kpi-card{background:#FFF;border-radius:10px;padding:18px 20px;
          border-left:4px solid #1A6F9C;box-shadow:0 1px 4px rgba(0,0,0,.06);}
.kpi-value{font-size:2rem;font-weight:600;color:#1A2332;line-height:1;}
.kpi-label{font-size:.78rem;color:#6B7280;margin-top:4px;line-height:1.4;}
.kpi-unit{font-size:.72rem;color:#9CA3AF;margin-top:2px;}
.dim-agua{border-left-color:#1A6F9C!important;}
.dim-residuos{border-left-color:#2D8C3F!important;}
.dim-energia{border-left-color:#D97706!important;}
.dim-movilidad{border-left-color:#7C3AED!important;}
.dim-conciencia{border-left-color:#C0392B!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.5rem;}
</style>"""


def render_dimension_page(
    dimension:    str,
    titulo:       str,
    icono:        str,
    color:        str,
    kpis:         list[dict],    # [{"id": "IND_...", "etiqueta": "..."}]
    ind_barras:   Optional[str], # ID del indicador para el gráfico principal
    ind_indice:   Optional[str], # ID del índice compuesto (si existe)
    indice_max:   float = 8.0,
    filtros:      dict  = None,
) -> None:
    """
    Renderiza una página completa de dimensión ambiental.

    Parámetros
    ----------
    dimension    : nombre de la dimensión
    titulo       : título de la página
    icono        : emoji del icono
    color        : color hex de la dimensión
    kpis         : lista de dicts con id y etiqueta de los KPIs a mostrar
    ind_barras   : indicador a usar en el gráfico de barras principal (None=todos)
    ind_indice   : indicador de índice compuesto (None=no mostrar gauge)
    indice_max   : valor máximo del índice
    filtros      : dict de filtros del sidebar
    """
    if filtros is None:
        filtros = {"area": None, "prov": None, "descripcion": "Nacional"}

    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin-bottom:20px;">
        <h1 style="font-size:1.4rem;font-weight:600;color:#1A2332;margin:0;">
            {icono} {titulo}
        </h1>
        <p style="color:#6B7280;font-size:.88rem;margin:4px 0 0;">
            MIAH · ENEMDU 2025 · <strong>{filtros.get('descripcion','Nacional')}</strong>
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Cargar datos ──────────────────────────────────────────────
    with st.spinner(f"Calculando indicadores de {dimension}..."):
        try:
            df = cargar_dimension(
                dimension,
                area=filtros.get("area"),
                prov=filtros.get("prov"),
            )
        except Exception as e:
            mostrar_error_sin_datos()
            st.error(str(e))
            return

    if df.empty:
        mostrar_advertencia_filtro_vacio()
        return

    # Separar indicadores de proporción del índice
    df_prop = df[df["tipo"] != "indice"].copy() if "tipo" in df.columns else df.copy()

    # ── KPIs ─────────────────────────────────────────────────────
    n_cols = min(len(kpis), 4)
    cols = st.columns(n_cols)
    for col, kpi_def in zip(cols, kpis[:n_cols]):
        with col:
            v = obtener_valor(df, kpi_def["id"])
            n = _get_n(df, kpi_def["id"])
            kpi_card(v, kpi_def["etiqueta"], dimension=dimension, n_muestra=n)

    if len(kpis) > 4:
        cols2 = st.columns(min(len(kpis) - 4, 4))
        for col, kpi_def in zip(cols2, kpis[4:]):
            with col:
                v = obtener_valor(df, kpi_def["id"])
                n = _get_n(df, kpi_def["id"])
                kpi_card(v, kpi_def["etiqueta"], dimension=dimension, n_muestra=n)

    st.markdown("---")

    # ── Gráfico principal: todos los indicadores de proporción ───
    col_izq, col_der = st.columns([3, 1] if ind_indice else [1], gap="large") \
        if ind_indice else (st.columns([1])[0], None)

    # Excluir solo el indicador de índice compuesto — no todos los que
    # terminan en "05" u "08", ya que IND_AGUA_05 es un indicador válido.
    excluir_ids = {ind_indice} if ind_indice else set()
    df_plot = df[~df["indicador_id"].isin(excluir_ids)].copy() \
        if not df.empty else df

    with col_izq if ind_indice else st.container():
        st.markdown(f"**Todos los indicadores de {titulo.lower()}**")
        if "indicador" in df_plot.columns and "valor" in df_plot.columns:
            fig = barras_horizontal(
                df_plot.dropna(subset=["valor"]),
                col_y="indicador", col_x="valor",
                color=color,
                titulo="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de indicadores de proporción.")

    if ind_indice and col_der is not None:
        with col_der:
            v_ind = obtener_valor(df, ind_indice)
            if v_ind is not None:
                st.markdown("**Índice compuesto**")
                fig_g = gauge_indice(
                    v_ind, indice_max,
                    titulo="Media ponderada",
                    color=color,
                    unidad=f"/{int(indice_max)} pts",
                )
                st.plotly_chart(fig_g, use_container_width=True)
                st.markdown(
                    f"<p style='text-align:center;font-size:.78rem;color:#9CA3AF;'>"
                    f"Promedio nacional: <strong>{v_ind:.2f}</strong> / {int(indice_max)} pts</p>",
                    unsafe_allow_html=True,
                )

    # ── Desglose por área (si no hay filtro de área activo) ───────
    if filtros.get("area") is None:
        st.markdown("---")
        st.markdown("**Comparativa urbano · rural**")
        with st.spinner("Cargando por área..."):
            try:
                df_area_all = cargar_por_area()
                df_area = filtrar_dimension(df_area_all, dimension)
                if filtros.get("prov"):
                    df_area = df_area[df_area.get("prov", pd.Series()) == filtros["prov"]] \
                        if "prov" in df_area.columns else df_area
                col_area = "area_nombre" if "area_nombre" in df_area.columns else "area"
                fig_area = barras_area(
                    df_area, col_y="indicador", col_area=col_area,
                    color_urb=color, color_rur=_lighten(color),
                )
                st.plotly_chart(fig_area, use_container_width=True)
            except Exception:
                st.info("Desglose por área no disponible.")

    # ── Desglose por provincia ────────────────────────────────────
    # Solo se muestra si el archivo fuente de la dimensión contiene la
    # columna prov. ambiental_oct (agua, residuos, conciencia) no la
    # incluye, por lo que esos dashboards no mostrarán esta sección.
    if filtros.get("prov") is None:
        kpi_prov = kpis[0]["id"] if kpis else None
        if kpi_prov:
            try:
                df_prov_all = cargar_por_provincia()
                df_prov = filtrar_dimension(df_prov_all, dimension)
                df_prov_ind = df_prov[
                    df_prov["indicador_id"] == kpi_prov
                ].copy() if not df_prov.empty else pd.DataFrame()

                # Mostrar SOLO si hay datos reales de varias provincias
                tiene_datos = (
                    not df_prov_ind.empty
                    and "valor" in df_prov_ind.columns
                    and df_prov_ind["valor"].notna().any()
                    and len(df_prov_ind) > 1
                )
                if tiene_datos:
                    st.markdown("---")
                    st.markdown("**Distribución provincial**")
                    etiqueta_prov = kpis[0]["etiqueta"] if kpis else kpi_prov
                    fig_prov = mapa_provincias(
                        df_prov_ind,
                        titulo=etiqueta_prov,
                        color=color,
                    )
                    st.plotly_chart(fig_prov, use_container_width=True)
                # Sin datos provinciales: sección invisible, sin error
            except Exception:
                pass

    # ── Tabla de datos ────────────────────────────────────────────
    with st.expander("📋 Ver tabla de datos completa"):
        cols_mostrar = [c for c in
            ["indicador_id", "indicador", "valor", "unidad", "n_muestra", "pob_estimada"]
            if c in df.columns]
        st.dataframe(
            df[cols_mostrar].sort_values("indicador_id"),
            use_container_width=True, hide_index=True,
        )
        csv = df[cols_mostrar].to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️ Descargar CSV", csv,
            file_name=f"indicadores_{dimension}_{filtros.get('descripcion','nacional')}.csv",
            mime="text/csv",
        )

    st.markdown(f"""<p style="text-align:center;color:#9CA3AF;font-size:.72rem;margin-top:20px;">
    Fuente: INEC Ecuador · MIAH-ENEMDU 2025 · Ponderado con fexp</p>""",
    unsafe_allow_html=True)


def _get_n(df: pd.DataFrame, ind_id: str) -> Optional[int]:
    if df.empty or "indicador_id" not in df.columns:
        return None
    f = df[df["indicador_id"] == ind_id]
    if f.empty or "n_muestra" not in f.columns:
        return None
    return int(f["n_muestra"].iloc[0])


def _lighten(hex_color: str, factor: float = 0.5) -> str:
    """Versión más clara de un color hex."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02X}{g:02X}{b:02X}"