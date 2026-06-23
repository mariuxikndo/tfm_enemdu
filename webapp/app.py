"""
webapp/app.py — Página de inicio rediseñada
────────────────────────────────────────────────────────────────────
Punto de entrada de la Plataforma MIAH-ENEMDU 2025.
Incluye el sidebar rediseñado y una landing page con:
  · Métricas clave de la plataforma
  · Tarjetas de acceso por dimensión
  · Sección "Cómo funciona"
  · Footer institucional

Ejecutar desde la raíz del proyecto:
  python -m streamlit run webapp/app.py
"""

import sys
from pathlib import Path

import streamlit as st

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
            "Basada en los microdatos MIAH-ENEMDU 2025 — INEC Ecuador.\n\n"
            "Trabajo de Fin de Máster · UNIR · Análisis y Visualización de Datos Masivos."
        )
    },
)

# ── CSS global de la app ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background-color: #F4F7FB; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem; }

/* ── Tarjetas de dimensión ── */
.dim-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px;
    border-top: 4px solid #1A6F9C;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    height: 100%;
    transition: box-shadow .15s;
}
.dim-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.dim-icon {
    width: 44px; height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; margin-bottom: 12px;
}
.dim-title {
    font-size: 14px; font-weight: 600; color: #1A2332;
    margin: 0 0 6px;
}
.dim-desc {
    font-size: 12px; color: #6B7280; line-height: 1.55;
    margin: 0 0 12px;
}
.dim-count {
    font-size: 11px; color: #9CA3AF;
}
.dim-count strong { color: #374151; }

/* ── Stats ── */
.stat-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 18px 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.stat-num {
    font-size: 2rem; font-weight: 600; color: #1A2332;
    line-height: 1;
}
.stat-label {
    font-size: 12px; color: #6B7280; margin-top: 4px;
}

/* ── Paso "Cómo funciona" ── */
.step-card {
    background: #FFFFFF; border-radius: 10px;
    padding: 18px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.step-num {
    width: 30px; height: 30px; border-radius: 50%;
    background: #0D1B2A; color: #2DD4A0;
    font-size: 13px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 10px;
}
.step-title { font-size: 13px; font-weight: 600; color: #1A2332; margin-bottom: 4px; }
.step-desc  { font-size: 12px; color: #6B7280; line-height: 1.5; }

/* ── KPI card (para páginas de dimensión) ── */
.kpi-card {
    background: #FFF; border-radius: 10px; padding: 18px 20px;
    border-left: 4px solid #1A6F9C;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.kpi-value { font-size: 2rem; font-weight: 600; color: #1A2332; line-height: 1; }
.kpi-label { font-size: .78rem; color: #6B7280; margin-top: 4px; line-height: 1.4; }
.kpi-unit  { font-size: .72rem; color: #9CA3AF; margin-top: 2px; }
.dim-agua      { border-left-color: #1A6F9C !important; }
.dim-residuos  { border-left-color: #2D8C3F !important; }
.dim-energia   { border-left-color: #D97706 !important; }
.dim-movilidad { border-left-color: #7C3AED !important; }
.dim-conciencia{ border-left-color: #C0392B !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar rediseñado ────────────────────────────────────────────
from webapp.components.sidebar_filters import render_sidebar
render_sidebar()   # aplica el CSS del sidebar + renderiza los filtros

# ══════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════════

# ── Hero ──────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0D1B2A 0%,#162232 100%);
            border-radius:16px; padding:48px 40px; margin-bottom:28px;
            display:flex; flex-direction:column; align-items:center; text-align:center;">
    <div style="width:64px;height:64px;background:#0F3A2E;border-radius:16px;
                display:flex;align-items:center;justify-content:center;margin-bottom:18px;">
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none"
             stroke="#2DD4A0" stroke-width="1.6" stroke-linecap="round"
             stroke-linejoin="round" aria-hidden="true">
            <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10"/>
            <path d="M12 2c2 4 3 8 2 13"/>
            <path d="M2 12c3-1 7-1.5 10 0"/>
            <path d="M12 7c3 2 6 2 9 0"/>
        </svg>
    </div>
    <h1 style="font-size:1.9rem;font-weight:600;color:#E8F4F2;margin:0 0 10px;
               letter-spacing:-.02em;">
        Indicadores Ambientales de Hogares
    </h1>
    <p style="font-size:0.95rem;color:#7AA3C7;margin:0 0 6px;">
        MIAH · ENEMDU 2025 · Ecuador
    </p>
    <p style="font-size:0.82rem;color:#4A7A8A;max-width:560px;line-height:1.6;margin:0;">
        Plataforma web para el análisis y visualización de indicadores ambientales
        de hogares ecuatorianos, a partir de los microdatos del Módulo de Información
        Ambiental (MIAH) de la ENEMDU 2025.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Stats ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4, gap="small")
stats = [
    ("5",      "Dimensiones MDEA"),
    ("30",     "Indicadores ambientales"),
    ("44.944", "Registros procesados"),
    ("2025",   "Año de los datos"),
]
for col, (num, label) in zip([c1, c2, c3, c4], stats):
    with col:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{num}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

# ── Dimensiones ───────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:12px;">
    <h2 style="font-size:1.1rem;font-weight:600;color:#1A2332;margin:0 0 4px;">
        Explorar por dimensión ambiental
    </h2>
    <p style="font-size:0.83rem;color:#6B7280;margin:0;">
        Selecciona una dimensión para ver los indicadores con filtros por área y provincia.
    </p>
</div>
""", unsafe_allow_html=True)

DIMS = [
    {
        "color": "#1A6F9C", "bg": "#EBF4FB", "icon": "💧",
        "nombre": "Uso del Agua",
        "desc": "Hábitos de ahorro, dispositivos eficientes y prácticas de reúso del agua en el hogar.",
        "n_ind": 8, "page": "pages/1_Agua.py", "label": "Ver indicadores →",
    },
    {
        "color": "#2D8C3F", "bg": "#EBF5ED", "icon": "♻️",
        "nombre": "Gestión de Residuos",
        "desc": "Clasificación de residuos orgánicos e inorgánicos y disposición final adecuada.",
        "n_ind": 6, "page": "pages/2_Residuos.py", "label": "Ver indicadores →",
    },
    {
        "color": "#D97706", "bg": "#FDF3E3", "icon": "⚡",
        "nombre": "Eficiencia Energética",
        "desc": "Hábitos de consumo energético, electrodomésticos ahorradores y energía solar.",
        "n_ind": 8, "page": "pages/3_Energia.py", "label": "Ver indicadores →",
    },
    {
        "color": "#7C3AED", "bg": "#F3EFFE", "icon": "🚌",
        "nombre": "Movilidad",
        "desc": "Uso de transporte público colectivo, movilidad sostenible y tiempo de traslado.",
        "n_ind": 3, "page": "pages/4_Movilidad.py", "label": "Ver indicadores →",
    },
    {
        "color": "#C0392B", "bg": "#FBEAEA", "icon": "🌍",
        "nombre": "Conciencia Ambiental",
        "desc": "Preocupación, participación y actitudes de responsabilidad ambiental del hogar.",
        "n_ind": 5, "page": "pages/5_Conciencia.py", "label": "Ver indicadores →",
    },
]

cols_dim = st.columns(5, gap="small")
for col, dim in zip(cols_dim, DIMS):
    with col:
        st.markdown(f"""
        <div class="dim-card" style="border-top-color:{dim['color']};">
            <div class="dim-icon" style="background:{dim['bg']};">{dim['icon']}</div>
            <div class="dim-title">{dim['nombre']}</div>
            <div class="dim-desc">{dim['desc']}</div>
            <div class="dim-count">
                <strong>{dim['n_ind']}</strong> indicadores
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
        st.page_link(dim["page"], label=dim["label"], use_container_width=True)

st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

# ── Cómo funciona ─────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:12px;">
    <h2 style="font-size:1.1rem;font-weight:600;color:#1A2332;margin:0 0 4px;">
        Cómo funciona la plataforma
    </h2>
</div>
""", unsafe_allow_html=True)

pasos = [
    ("1", "Microdatos INEC",
     "Los archivos ODS del MIAH-ENEMDU se procesan mediante un pipeline ETL "
     "automatizado que limpia, transforma y almacena los datos en formato Parquet."),
    ("2", "Cálculo ponderado",
     "El motor calcula 30 indicadores en 5 dimensiones aplicando el factor de "
     "expansión muestral (fexp) para obtener resultados representativos de la "
     "población de hogares ecuatorianos."),
    ("3", "Exploración interactiva",
     "La plataforma web permite consultar, filtrar por área y provincia, comparar "
     "grupos y exportar los resultados sin necesidad de conocimientos de programación."),
]

c1, c2, c3 = st.columns(3, gap="small")
for col, (num, titulo, desc) in zip([c1, c2, c3], pasos):
    with col:
        st.markdown(f"""
        <div class="step-card">
            <div class="step-num">{num}</div>
            <div class="step-title">{titulo}</div>
            <div class="step-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

# ── Acceso directo al comparativo ────────────────────────────────
with st.container():
    st.markdown("""
    <div style="background:#0D1B2A;border-radius:12px;padding:22px 28px;
                display:flex;align-items:center;gap:20px;flex-wrap:wrap;">
        <div style="flex:1;min-width:200px;">
            <div style="font-size:13px;font-weight:600;color:#E8F4F2;margin-bottom:4px;">
                ⚖️ Módulo comparativo
            </div>
            <div style="font-size:12px;color:#7AA3C7;line-height:1.5;">
                Contrasta indicadores entre áreas geográficas, compara urbano vs rural
                o analiza diferencias entre provincias con un clic.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    st.page_link("pages/6_Comparativo.py",
                 label="Ir al módulo comparativo →",
                 use_container_width=False)

# ── Footer ────────────────────────────────────────────────────────
st.markdown("""
<hr style="border:none;border-top:0.5px solid #E5E9F0;margin:32px 0 16px;">
<div style="display:flex;justify-content:space-between;align-items:center;
            flex-wrap:wrap;gap:8px;">
    <p style="font-size:0.75rem;color:#9CA3AF;margin:0;">
        Fuente: <strong>INEC Ecuador</strong> · MIAH-ENEMDU agosto y octubre 2025 ·
        Resultados ponderados con factor de expansión muestral (fexp)
    </p>
    <p style="font-size:0.75rem;color:#9CA3AF;margin:0;">
        Trabajo de Fin de Máster · Máster en Análisis y Visualización de Datos Masivos · UNIR
    </p>
</div>
""", unsafe_allow_html=True)
