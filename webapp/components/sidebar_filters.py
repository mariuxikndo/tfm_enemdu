"""
webapp/components/sidebar_filters.py — Rediseño visual 2025
────────────────────────────────────────────────────────────────────
Panel lateral con nueva identidad visual:
  · Tema oscuro profundo (#0D1B2A)
  · Navegación rápida por dimensión (botones de color)
  · Radio buttons para área (más visual que selectbox)
  · Badge activo con filtro seleccionado
  · Chips de volumen de datos
  · Footer con indicador de fexp
"""

import sys
from pathlib import Path
from typing import Optional

import streamlit as st

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVINCIAS_ORDENADAS = {
    1: "Azuay",           2: "Bolívar",          3: "Cañar",
    4: "Carchi",          5: "Cotopaxi",          6: "Chimborazo",
    7: "El Oro",          8: "Esmeraldas",         9: "Guayas",
    10: "Imbabura",       11: "Loja",             12: "Los Ríos",
    13: "Manabí",         14: "Morona Santiago",  15: "Napo",
    16: "Pastaza",        17: "Pichincha",         18: "Tungurahua",
    19: "Zamora Chinchipe", 20: "Galápagos",      21: "Sucumbíos",
    22: "Orellana",       23: "Santo Domingo",    24: "Santa Elena",
}

# ── CSS global del sidebar ────────────────────────────────────────
_CSS = """
<style>
/* ── Fondo y contenedor ── */
[data-testid="stSidebar"] {
    background-color: #0D1B2A !important;
    border-right: 0.5px solid #1E3347 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}
[data-testid="stSidebar"] section > div {
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-top: 0 !important;
}

/* ── Texto base ── */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #9BAFC7 !important;
    font-size: 12px !important;
}

/* ── Ocultar label de radio y selectbox (usamos labels propios en HTML) ── */
[data-testid="stSidebar"] [data-testid="stRadio"] > label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] > label {
    display: none !important;
}

/* ── Radio buttons ── */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 2px !important;
    background: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent !important;
    border-radius: 6px !important;
    padding: 6px 10px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: background .12s !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #162232 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-selected="true"],
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: #0F3A2E !important;
    border: 0.5px solid #1A5A44 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p,
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) span {
    color: #E8F4F2 !important;
}
/* Círculo del radio */
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    accent-color: #2DD4A0 !important;
}

/* ── Selectbox ── */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background-color: #0F1923 !important;
    border-color: #1E3347 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] span {
    color: #9BAFC7 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
    fill: #4A7A8A !important;
}

/* ── Page links (botones de dimensión) ── */
[data-testid="stSidebar"] [data-testid="stPageLink"] {
    padding: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    border-radius: 6px !important;
    padding: 7px 10px !important;
    font-size: 11px !important;
    text-decoration: none !important;
    display: flex !important;
    align-items: center !important;
    transition: opacity .15s !important;
    border: 0.5px solid transparent !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    opacity: 0.85 !important;
}

/* Botón Inicio */
[data-testid="stSidebar"] [data-testid="stPageLink"]:nth-of-type(1) a {
    background: #162232 !important; color: #E8F4F2 !important;
    border-color: #2A3F52 !important; font-weight: 500 !important;
}
/* Dimensión agua — ahora es la 2ª page_link */
[data-testid="stSidebar"] [data-testid="stPageLink"]:nth-of-type(2) a {
    background: #0C2231 !important; color: #6BB8DC !important;
    border-color: #1A4860 !important;
}
/* Dimensión residuos */
[data-testid="stSidebar"] [data-testid="stPageLink"]:nth-of-type(3) a {
    background: #0A2318 !important; color: #5DBF8A !important;
    border-color: #0F4028 !important;
}
/* Dimensión energía */
[data-testid="stSidebar"] [data-testid="stPageLink"]:nth-of-type(4) a {
    background: #2A1C06 !important; color: #DFA83C !important;
    border-color: #4A3010 !important;
}
/* Dimensión movilidad */
[data-testid="stSidebar"] [data-testid="stPageLink"]:nth-of-type(5) a {
    background: #1A102A !important; color: #9D82DD !important;
    border-color: #2E1C4A !important;
}
/* Dimensión conciencia */
[data-testid="stSidebar"] [data-testid="stPageLink"]:nth-of-type(6) a {
    background: #2A0E0E !important; color: #DD7575 !important;
    border-color: #4A1A1A !important;
}

/* ── Columnas internas del sidebar ── */
[data-testid="stSidebar"] [data-testid="column"] {
    padding: 0 3px !important;
}

/* ── Ocultar navegación automática de Streamlit (usamos la nuestra) ── */
[data-testid="stSidebarNavItems"] { display: none !important; }
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* ── Scrollbar del sidebar ── */
[data-testid="stSidebar"] ::-webkit-scrollbar { width: 4px; }
[data-testid="stSidebar"] ::-webkit-scrollbar-track { background: #0D1B2A; }
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb { background: #1E3347; border-radius: 2px; }
</style>
"""

# ── Componentes HTML del sidebar ──────────────────────────────────

_HEADER = """
<div style="padding:22px 20px 16px; border-bottom:0.5px solid #1E3347;">
  <div style="width:40px;height:40px;background:#0F3A2E;border-radius:10px;
              display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#2DD4A0" stroke-width="1.8" stroke-linecap="round"
         stroke-linejoin="round" aria-hidden="true">
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10"/>
      <path d="M12 2c2 4 3 8 2 13"/>
      <path d="M2 12c3-1 7-1.5 10 0"/>
      <path d="M12 7c3 2 6 2 9 0"/>
    </svg>
  </div>
  <div style="font-size:13px;font-weight:500;color:#E8F4F2;margin:0 0 2px;">
    Indicadores Ambientales
  </div>
  <div style="font-size:10px;color:#4A7A8A;letter-spacing:.1em;text-transform:uppercase;">
    MIAH · ENEMDU · Ecuador
  </div>
</div>
"""

def _label(texto: str) -> str:
    return f"""
    <div style="font-size:10px;color:#4A7A8A;letter-spacing:.1em;text-transform:uppercase;
                margin:16px 20px 6px;display:flex;align-items:center;gap:8px;">
        <span>{texto}</span>
        <div style="flex:1;height:0.5px;background:#1E3347;"></div>
    </div>
    """

def _badge_activo(descripcion: str) -> str:
    return f"""
    <div style="margin:14px 20px 0;background:#0A2318;border:0.5px solid #1A5A44;
                border-radius:8px;padding:10px 12px;">
        <div style="font-size:10px;color:#4A7A8A;text-transform:uppercase;
                    letter-spacing:.08em;margin-bottom:4px;">Mostrando</div>
        <div style="font-size:12px;color:#2DD4A0;font-weight:500;
                    display:flex;align-items:center;gap:5px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" aria-hidden="true">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
            </svg>
            {descripcion}
        </div>
    </div>
    """

_DATA_CHIPS = """
<div style="margin:14px 20px 0;">
    <div style="font-size:10px;color:#4A7A8A;text-transform:uppercase;
                letter-spacing:.08em;margin-bottom:7px;display:flex;align-items:center;gap:8px;">
        <span>Datos activos</span>
        <div style="flex:1;height:0.5px;background:#1E3347;"></div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:5px;">
        <span style="background:#0C2231;color:#6BB8DC;border:0.5px solid #1A4860;
                     font-size:10px;padding:3px 8px;border-radius:20px;">
            8.607 reg. (ago)
        </span>
        <span style="background:#0C2231;color:#6BB8DC;border:0.5px solid #1A4860;
                     font-size:10px;padding:3px 8px;border-radius:20px;">
            8.757 reg. (oct)
        </span>
        <span style="background:#0A2318;color:#5DBF8A;border:0.5px solid #0F4028;
                     font-size:10px;padding:3px 8px;border-radius:20px;">
            27.580 personas
        </span>
    </div>
</div>
"""

_FOOTER = """
<div style="margin:20px 0 0;padding:14px 20px;border-top:0.5px solid #1E3347;">
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:5px;">
        <div style="width:7px;height:7px;border-radius:50%;background:#2DD4A0;flex-shrink:0;"></div>
        <span style="font-size:11px;color:#4A7A8A !important;">
            Ponderado con factor de expansión (fexp)
        </span>
    </div>
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:4px;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
             stroke="#4A7A8A" stroke-width="2" aria-hidden="true">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <path d="M3 9h18M9 21V9"/>
        </svg>
        <span style="font-size:11px;color:#4A7A8A !important;">Fuente: INEC Ecuador</span>
    </div>
    <div style="display:flex;align-items:center;gap:7px;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
             stroke="#4A7A8A" stroke-width="2" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span style="font-size:11px;color:#4A7A8A !important;">Agosto y Octubre 2025</span>
    </div>
</div>
"""

_SEPARADOR = '<div style="height:0.5px;background:#1E3347;margin:0 20px;"></div>'


# ── Función principal ─────────────────────────────────────────────

def render_sidebar() -> dict:
    """
    Renderiza el panel lateral rediseñado y retorna los filtros
    seleccionados como diccionario.
    """
    # CSS global (se inyecta en la página, no solo en el sidebar)
    st.markdown(_CSS, unsafe_allow_html=True)

    with st.sidebar:

        # ── Cabecera de marca ─────────────────────────────────────
        st.markdown(_HEADER, unsafe_allow_html=True)

        # ── Enlace a la página principal ─────────────────────────
        st.markdown('<div style="padding:0 20px 4px;">', unsafe_allow_html=True)
        st.page_link("app.py", label="🏠 Inicio", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(_SEPARADOR, unsafe_allow_html=True)

        # ── Navegación por dimensión ──────────────────────────────
        st.markdown(_label("Dimensiones"), unsafe_allow_html=True)
        st.markdown('<div style="padding:0 20px;">', unsafe_allow_html=True)

        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.page_link("pages/1_Agua.py",    label="💧 Agua",    use_container_width=True)
            st.page_link("pages/3_Energia.py", label="⚡ Energía", use_container_width=True)
        with c2:
            st.page_link("pages/2_Residuos.py",  label="♻️ Residuos",  use_container_width=True)
            st.page_link("pages/4_Movilidad.py", label="🚌 Movilidad", use_container_width=True)
        st.page_link("pages/5_Conciencia.py",
                     label="🌍 Conciencia ambiental", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(_SEPARADOR, unsafe_allow_html=True)

        # ── Filtro de área ────────────────────────────────────────
        st.markdown(_label("Área"), unsafe_allow_html=True)
        st.markdown('<div style="padding:0 12px;">', unsafe_allow_html=True)

        area_opciones = {
            "Nacional (urbano + rural)": None,
            "Urbano": 1,
            "Rural":  2,
        }
        area_sel = st.radio(
            "Área",
            list(area_opciones.keys()),
            label_visibility="collapsed",
            key="sb_area_v2",
        )
        area_val   = area_opciones[area_sel]
        area_label = area_sel.split("(")[0].strip()

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(_SEPARADOR, unsafe_allow_html=True)

        # ── Filtro de provincia ───────────────────────────────────
        st.markdown(_label("Provincia"), unsafe_allow_html=True)
        st.markdown('<div style="padding:0 20px 4px;">', unsafe_allow_html=True)

        prov_opciones = {"Todas las provincias": None}
        for cod, nombre in sorted(PROVINCIAS_ORDENADAS.items(), key=lambda x: x[1]):
            prov_opciones[nombre] = cod

        prov_sel = st.selectbox(
            "Provincia",
            list(prov_opciones.keys()),
            label_visibility="collapsed",
            key="sb_prov_v2",
        )
        prov_val   = prov_opciones[prov_sel]
        prov_label = prov_sel

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Badge de filtro activo ────────────────────────────────
        partes = []
        if area_val is not None:
            partes.append(area_label)
        if prov_val is not None:
            partes.append(prov_label)
        partes.append("2025")
        descripcion = " · ".join(partes)

        st.markdown(_badge_activo(descripcion), unsafe_allow_html=True)

        # ── Chips de datos ────────────────────────────────────────
        st.markdown(_DATA_CHIPS, unsafe_allow_html=True)

        # ── Footer ────────────────────────────────────────────────
        st.markdown(_FOOTER, unsafe_allow_html=True)

    desc_sin_año = " · ".join(
        p for p in [
            area_label if area_val is not None else None,
            prov_label if prov_val is not None else None,
        ] if p
    ) or "Nacional"

    return {
        "area":        area_val,
        "prov":        prov_val,
        "area_label":  area_label,
        "prov_label":  prov_label,
        "descripcion": desc_sin_año,
    }


# ── Variante para módulo comparativo ─────────────────────────────

def render_sidebar_comparativo() -> tuple[dict, dict]:
    """
    Sidebar del módulo comparativo con dos grupos de filtros.
    Mantiene el mismo estilo visual que el sidebar principal.
    """
    st.markdown(_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div style="padding:22px 20px 16px;border-bottom:0.5px solid #1E3347;">
          <div style="font-size:13px;font-weight:500;color:#E8F4F2;margin-bottom:2px;">
            Análisis comparativo
          </div>
          <div style="font-size:10px;color:#4A7A8A;letter-spacing:.1em;text-transform:uppercase;">
            MIAH · ENEMDU 2025
          </div>
        </div>
        """, unsafe_allow_html=True)

        area_opts = {"Nacional": None, "Urbano": 1, "Rural": 2}
        prov_opts = {"Todas": None, **{v: k for k, v in sorted(
            PROVINCIAS_ORDENADAS.items(), key=lambda x: x[1])}}

        # ── Grupo A ───────────────────────────────────────────────
        st.markdown("""
        <div style="margin:14px 20px 6px;display:flex;align-items:center;gap:8px;">
          <div style="width:8px;height:8px;border-radius:50%;background:#378ADD;"></div>
          <span style="font-size:11px;font-weight:500;color:#6BB8DC !important;
                       text-transform:uppercase;letter-spacing:.06em;">Grupo A</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="padding:0 12px;">', unsafe_allow_html=True)
        area_a = st.radio("Área A", list(area_opts.keys()),
                          label_visibility="collapsed", key="cmp_area_a_v2")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div style="padding:0 20px 4px;">', unsafe_allow_html=True)
        prov_a = st.selectbox("Provincia A", list(prov_opts.keys()),
                              label_visibility="collapsed", key="cmp_prov_a_v2")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(_SEPARADOR, unsafe_allow_html=True)

        # ── Grupo B ───────────────────────────────────────────────
        st.markdown("""
        <div style="margin:14px 20px 6px;display:flex;align-items:center;gap:8px;">
          <div style="width:8px;height:8px;border-radius:50%;background:#DFA83C;"></div>
          <span style="font-size:11px;font-weight:500;color:#DFA83C !important;
                       text-transform:uppercase;letter-spacing:.06em;">Grupo B</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="padding:0 12px;">', unsafe_allow_html=True)
        area_b = st.radio("Área B", list(area_opts.keys()),
                          index=1, label_visibility="collapsed", key="cmp_area_b_v2")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div style="padding:0 20px 4px;">', unsafe_allow_html=True)
        prov_b = st.selectbox("Provincia B", list(prov_opts.keys()),
                              label_visibility="collapsed", key="cmp_prov_b_v2")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(_FOOTER, unsafe_allow_html=True)

    fa = {
        "area":  area_opts[area_a], "prov": prov_opts.get(prov_a),
        "label": f"{area_a}" + (f" · {prov_a}" if prov_opts.get(prov_a) else ""),
    }
    fb = {
        "area":  area_opts[area_b], "prov": prov_opts.get(prov_b),
        "label": f"{area_b}" + (f" · {prov_b}" if prov_opts.get(prov_b) else ""),
    }
    return fa, fb
