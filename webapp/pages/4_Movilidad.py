"""webapp/pages/4_Movilidad.py — Dashboard de movilidad y transporte."""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Movilidad · MIAH-ENEMDU", page_icon="🚌", layout="wide")

from webapp.components.sidebar_filters import render_sidebar
from webapp.components.charts import kpi_card, barras_horizontal, barras_area, mapa_provincias
from webapp.data_layer import (
    cargar_dimension, cargar_por_area, cargar_por_provincia,
    filtrar_dimension, obtener_valor, mostrar_error_sin_datos,
)

CSS = """<style>
.stApp{background-color:#F4F7FB;}
[data-testid="stSidebar"]{background-color:#1A2332;}
[data-testid="stSidebar"] *{color:#E8EDF3!important;}
.kpi-card{background:#FFF;border-radius:10px;padding:18px 20px;
          border-left:4px solid #7C3AED;box-shadow:0 1px 4px rgba(0,0,0,.06);}
.kpi-value{font-size:2rem;font-weight:600;color:#1A2332;line-height:1;}
.kpi-label{font-size:.78rem;color:#6B7280;margin-top:4px;}
.kpi-unit{font-size:.72rem;color:#9CA3AF;margin-top:2px;}
.dim-movilidad{border-left-color:#7C3AED!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.5rem;}
</style>"""

filtros = render_sidebar()
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(f"""
<div style="margin-bottom:20px;">
    <h1 style="font-size:1.4rem;font-weight:600;color:#1A2332;margin:0;">
        🚌 Movilidad y Transporte
    </h1>
    <p style="color:#6B7280;font-size:.88rem;margin:4px 0 0;">
        MIAH · ENEMDU Agosto 2025 · <strong>{filtros.get('descripcion','Nacional')}</strong>
    </p>
</div>""", unsafe_allow_html=True)

with st.spinner("Calculando indicadores de movilidad..."):
    try:
        df = cargar_dimension("movilidad", area=filtros["area"], prov=filtros["prov"])
    except Exception as e:
        mostrar_error_sin_datos()
        st.stop()

if df.empty:
    st.warning("Sin datos para los filtros seleccionados.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    v = obtener_valor(df, "IND_MOV_01")
    n = int(df[df["indicador_id"]=="IND_MOV_01"]["n_muestra"].iloc[0]) \
        if not df[df["indicador_id"]=="IND_MOV_01"].empty else None
    kpi_card(v, "Usan transporte público colectivo", dimension="movilidad", n_muestra=n)
with c2:
    v = obtener_valor(df, "IND_MOV_02")
    n = int(df[df["indicador_id"]=="IND_MOV_02"]["n_muestra"].iloc[0]) \
        if not df[df["indicador_id"]=="IND_MOV_02"].empty else None
    kpi_card(v, "Movilidad sostenible (público + no motorizado)", dimension="movilidad", n_muestra=n)
with c3:
    v = obtener_valor(df, "IND_MOV_03")
    kpi_card(v or 0, "Tiempo promedio de traslado", unidad=" min", dimension="movilidad")

st.markdown("---")

# ── Gráfico de indicadores de proporción ─────────────────────────
col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("**Indicadores de movilidad**")
    df_prop = df[df["indicador_id"].isin(["IND_MOV_01","IND_MOV_02"])]
    if not df_prop.empty:
        fig = barras_horizontal(
            df_prop, col_y="indicador", col_x="valor",
            color="#7C3AED", titulo="",
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**Nota metodológica**")
    st.info(
        "**Transporte público colectivo** incluye: autobús (cod. 1), "
        "Metrovía/Tranvía/Trolebús (cod. 4) y Metro (cod. 5).\n\n"
        "**Movilidad sostenible** incluye además bicicleta (cod. 8) y "
        "desplazamiento a pie (cod. 9).\n\n"
        "Aplica a personas de 12 años y más con destino habitual. "
        "Datos de agosto 2025."
    )

# ── Por área ──────────────────────────────────────────────────────
if filtros.get("area") is None:
    st.markdown("---")
    st.markdown("**Comparativa urbano · rural**")
    try:
        df_a = filtrar_dimension(cargar_por_area(), "movilidad")
        fig_a = barras_area(df_a, col_y="indicador", color_urb="#7C3AED", color_rur="#B39DDB")
        st.plotly_chart(fig_a, use_container_width=True)
    except Exception:
        st.info("Desglose por área no disponible.")

# ── Por provincia ─────────────────────────────────────────────────
if filtros.get("prov") is None:
    st.markdown("---")
    st.markdown("**Distribución provincial — transporte público colectivo**")
    try:
        df_p = filtrar_dimension(cargar_por_provincia(), "movilidad")
        df_p_mov = df_p[df_p["indicador_id"] == "IND_MOV_01"]
        fig_p = mapa_provincias(df_p_mov, titulo="Uso de transporte público colectivo (%)", color="#7C3AED")
        st.plotly_chart(fig_p, use_container_width=True)
    except Exception:
        st.info("Desglose provincial no disponible.")

# ── Tabla ─────────────────────────────────────────────────────────
with st.expander("📋 Ver tabla de datos"):
    cols_m = [c for c in ["indicador_id","indicador","valor","unidad","n_muestra"] if c in df.columns]
    st.dataframe(df[cols_m], use_container_width=True, hide_index=True)
    csv = df[cols_m].to_csv(index=False, encoding="utf-8-sig")
    st.download_button("⬇️ Descargar CSV", csv,
                       file_name=f"movilidad_{filtros.get('descripcion','nac')}.csv",
                       mime="text/csv")
