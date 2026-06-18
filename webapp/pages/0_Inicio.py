"""webapp/pages/0_Inicio.py — Resumen ejecutivo con KPIs nacionales."""
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from webapp.components.sidebar_filters import render_sidebar
from webapp.components.charts import kpi_card, barras_horizontal
from webapp.data_layer import (
    cargar_nacionales, cargar_dimension,
    filtrar_dimension, obtener_valor, mostrar_error_sin_datos,
)

st.set_page_config(page_title="Inicio · MIAH-ENEMDU", page_icon="🌿", layout="wide")

# CSS global (reutilizado del app.py)
st.markdown("""<style>
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
</style>""", unsafe_allow_html=True)

filtros = render_sidebar()

# ── Encabezado ────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:24px;">
    <h1 style="font-size:1.5rem;font-weight:600;color:#1A2332;margin:0;">
        🌿 Indicadores Ambientales de Hogares
    </h1>
    <p style="color:#6B7280;margin:4px 0 0;font-size:.9rem;">
        MIAH · ENEMDU 2025 · Ecuador · <strong>{filtros['descripcion']}</strong>
    </p>
</div>""", unsafe_allow_html=True)

# ── Cargar datos ──────────────────────────────────────────────────
with st.spinner("Calculando indicadores..."):
    try:
        df_nac = cargar_dimension(
            "agua", area=filtros["area"], prov=filtros["prov"]
        )
        df_res = cargar_dimension("residuos", area=filtros["area"], prov=filtros["prov"])
        df_ene = cargar_dimension("energia",  area=filtros["area"], prov=filtros["prov"])
        df_mov = cargar_dimension("movilidad", area=filtros["area"], prov=filtros["prov"])
        df_ca  = cargar_dimension("conciencia",area=filtros["area"], prov=filtros["prov"])
        datos_ok = True
    except Exception as e:
        datos_ok = False
        st.error(f"Error al cargar datos: {e}")

if not datos_ok:
    mostrar_error_sin_datos()
    st.stop()

# ── KPIs por dimensión ────────────────────────────────────────────
st.markdown("### Indicadores clave por dimensión")
st.markdown("---")

dimensiones = [
    ("💧 Agua",              "agua",       df_nac, "IND_AGUA_01", "Hogares que reusan el agua"),
    ("♻️ Residuos",          "residuos",   df_res, "IND_RES_01",  "Clasificaron residuos orgánicos"),
    ("⚡ Energía",            "energia",    df_ene, "IND_ENE_01",  "Desconectan aparatos eléctricos"),
    ("🚌 Movilidad",         "movilidad",  df_mov, "IND_MOV_01",  "Usan transporte público colectivo"),
    ("🌍 Conciencia Ambiental","conciencia",df_ca,  "IND_CA_02",  "Muy preocupados por el ambiente"),
]

cols = st.columns(5)
for col, (titulo, dim, df, ind_id, etiqueta) in zip(cols, dimensiones):
    with col:
        valor = obtener_valor(df, ind_id) if not df.empty else None
        n     = int(df[df["indicador_id"] == ind_id]["n_muestra"].iloc[0]) \
                if not df.empty and len(df[df["indicador_id"] == ind_id]) > 0 else None
        st.markdown(f"**{titulo}**")
        kpi_card(valor, etiqueta, dimension=dim, n_muestra=n)

st.markdown("---")

# ── Gráfico resumen: un indicador por dimensión ───────────────────
st.markdown("### Visión comparativa entre dimensiones")

resumen_rows = []
for titulo, dim, df, ind_id, etiqueta in dimensiones:
    v = obtener_valor(df, ind_id) if not df.empty else None
    if v is not None:
        resumen_rows.append({"Dimensión": titulo, "Indicador": etiqueta, "Valor": v})

if resumen_rows:
    import pandas as pd
    df_resumen = pd.DataFrame(resumen_rows)
    from webapp.components.charts import barras_horizontal
    fig = barras_horizontal(
        df_resumen, col_y="Dimensión", col_x="Valor",
        titulo="Indicador representativo por dimensión (%)",
        color="#1A6F9C",
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Navegación rápida ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### Explorar por dimensión")
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.page_link("pages/1_Agua.py",      label="💧 Agua",             use_container_width=True)
with c2: st.page_link("pages/2_Residuos.py",  label="♻️ Residuos",         use_container_width=True)
with c3: st.page_link("pages/3_Energia.py",   label="⚡ Energía",           use_container_width=True)
with c4: st.page_link("pages/4_Movilidad.py", label="🚌 Movilidad",         use_container_width=True)
with c5: st.page_link("pages/5_Conciencia.py",label="🌍 Conciencia",        use_container_width=True)

st.markdown("""
<p style="text-align:center;color:#9CA3AF;font-size:.75rem;margin-top:24px;">
Fuente: INEC Ecuador · MIAH-ENEMDU agosto y octubre 2025 · 
Resultados ponderados con factor de expansión muestral (fexp)
</p>""", unsafe_allow_html=True)
