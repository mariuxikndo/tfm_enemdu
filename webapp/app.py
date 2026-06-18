"""
webapp/app.py
────────────────────────────────────────────────────────────────────
Punto de entrada de la Plataforma MIAH-ENEMDU 2025.

Ejecutar desde la raíz del proyecto:
  streamlit run webapp/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# ── Path del proyecto ─────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Configuración de página ───────────────────────────────────────
st.set_page_config(
    page_title="Indicadores Ambientales · MIAH-ENEMDU 2025",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**Plataforma de Indicadores Ambientales de Hogares**\n\n"
            "Basada en los microdatos del Módulo de Información Ambiental "
            "en Hogares (MIAH) de la ENEMDU 2025 — INEC Ecuador.\n\n"
            "Desarrollada como Trabajo de Fin de Máster · "
            "Máster Universitario en Análisis y Visualización de Datos Masivos."
        )
    },
)

# ── CSS global ────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Tipografía y base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Fondo general ── */
.stApp { background-color: #F4F7FB; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #1A2332;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E8EDF3 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label { color: #9BAFC7 !important; font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #FFFFFF !important; }

/* ── Tarjetas de KPI ── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 18px 20px;
    border-left: 4px solid #1A6F9C;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.kpi-value { font-size: 2rem; font-weight: 600; color: #1A2332; line-height: 1; }
.kpi-label { font-size: 0.78rem; color: #6B7280; margin-top: 4px; line-height: 1.4; }
.kpi-unit  { font-size: 0.72rem; color: #9CA3AF; margin-top: 2px; }

/* ── Colores por dimensión ── */
.dim-agua       { border-left-color: #1A6F9C !important; }
.dim-residuos   { border-left-color: #2D8C3F !important; }
.dim-energia    { border-left-color: #D97706 !important; }
.dim-movilidad  { border-left-color: #7C3AED !important; }
.dim-conciencia { border-left-color: #C0392B !important; }

/* ── Encabezados de sección ── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    border-bottom: 2px solid #E5E9F0;
    padding-bottom: 8px; margin-bottom: 20px;
}
.section-header h2 { font-size: 1.1rem; font-weight: 600; color: #1A2332; margin: 0; }
.dim-badge {
    font-size: 0.7rem; font-weight: 500; padding: 3px 10px;
    border-radius: 20px; letter-spacing: 0.04em;
}

/* ── Tablas de datos ── */
[data-testid="stDataFrame"] { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; }

/* ── Ocultar decoraciones de Streamlit ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── Contenido de la página principal (antes de navegar) ──────────
st.markdown("""
<div style="text-align:center; padding: 60px 0 40px;">
    <div style="font-size:3rem; margin-bottom:12px;">🌿</div>
    <h1 style="font-size:1.8rem; font-weight:600; color:#1A2332; margin:0;">
        Indicadores Ambientales de Hogares
    </h1>
    <p style="color:#6B7280; margin-top:8px; font-size:0.95rem;">
        MIAH · ENEMDU 2025 · Ecuador
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.info("👈 **Usa el menú lateral** para navegar entre dimensiones.")
with col2:
    st.success("📊 Datos del MIAH-ENEMDU agosto y octubre 2025.")
with col3:
    st.warning("🔬 Resultados ponderados con factor de expansión muestral.")

st.markdown("---")
st.markdown("""
<p style="text-align:center; color:#9CA3AF; font-size:0.8rem;">
Plataforma desarrollada como Trabajo de Fin de Máster · 
Máster Universitario en Análisis y Visualización de Datos Masivos · UNIR
</p>
""", unsafe_allow_html=True)
