"""
webapp/components/sidebar_filters.py
────────────────────────────────────────────────────────────────────
Panel lateral de filtros compartido entre todas las páginas.

Uso:
  from webapp.components.sidebar_filters import render_sidebar
  filtros = render_sidebar()
  # filtros = {"area": 1, "prov": None, "area_label": "Urbano", ...}
"""

from typing import Optional
import streamlit as st

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


def render_sidebar() -> dict:
    """
    Renderiza el panel lateral de filtros y retorna los valores
    seleccionados como diccionario.

    Retorna
    -------
    {
        "area":        int | None,
        "prov":        int | None,
        "area_label":  str,
        "prov_label":  str,
        "descripcion": str,
    }
    """
    with st.sidebar:
        # ── Logo / título ─────────────────────────────────────────
        st.markdown("""
        <div style="padding: 16px 0 24px;">
            <div style="font-size:1.6rem; text-align:center;">🌿</div>
            <div style="text-align:center; font-size:0.75rem;
                        color:#9BAFC7; letter-spacing:0.08em;
                        text-transform:uppercase; margin-top:4px;">
                MIAH · ENEMDU 2025
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            "<p style='font-size:0.7rem; color:#9BAFC7; "
            "letter-spacing:0.08em; text-transform:uppercase;'>"
            "Filtros</p>",
            unsafe_allow_html=True,
        )

        # ── Filtro de área ────────────────────────────────────────
        area_opciones = {
            "🗺️  Nacional (urbano + rural)": None,
            "🏙️  Urbano": 1,
            "🌾  Rural":  2,
        }
        area_sel = st.selectbox(
            "Área",
            options=list(area_opciones.keys()),
            index=0,
            key="sb_area",
        )
        area_val   = area_opciones[area_sel]
        area_label = area_sel.split("  ", 1)[-1].strip()

        st.markdown("<hr style='border-color:#2A3A52; margin:12px 0;'>",
                    unsafe_allow_html=True)

        # ── Filtro de provincia ───────────────────────────────────
        prov_opciones = {"Todas las provincias": None}
        for cod, nombre in sorted(PROVINCIAS_ORDENADAS.items(),
                                   key=lambda x: x[1]):
            prov_opciones[nombre] = cod

        prov_sel = st.selectbox(
            "Provincia",
            options=list(prov_opciones.keys()),
            index=0,
            key="sb_prov",
        )
        prov_val   = prov_opciones[prov_sel]
        prov_label = prov_sel

        st.markdown("<hr style='border-color:#2A3A52; margin:12px 0;'>",
                    unsafe_allow_html=True)

        # ── Resumen del filtro activo ─────────────────────────────
        partes = []
        if area_val is not None:
            partes.append(area_label)
        if prov_val is not None:
            partes.append(prov_label)
        descripcion = " · ".join(partes) if partes else "Nacional"

        st.markdown(
            f"<div style='background:#0F1A2A; border-radius:6px; "
            f"padding:10px 12px; font-size:0.78rem; color:#7AA3C7;'>"
            f"<span style='color:#9BAFC7;'>Mostrando:</span><br>"
            f"<strong style='color:#E8EDF3;'>{descripcion}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Información fuente ────────────────────────────────────
        st.markdown("""
        <div style="margin-top:auto; padding-top:32px;">
            <p style="font-size:0.68rem; color:#4A5F78; line-height:1.5;">
                Fuente: INEC Ecuador · MIAH-ENEMDU 2025<br>
                Agosto y Octubre 2025<br>
                Resultados ponderados con fexp
            </p>
        </div>
        """, unsafe_allow_html=True)

    return {
        "area":        area_val,
        "prov":        prov_val,
        "area_label":  area_label,
        "prov_label":  prov_label,
        "descripcion": descripcion,
    }


def render_sidebar_comparativo() -> tuple[dict, dict]:
    """
    Renderiza el sidebar para el módulo comparativo con dos paneles
    de filtros (A y B).

    Retorna
    -------
    (filtros_a, filtros_b) — dos diccionarios de filtros
    """
    with st.sidebar:
        st.markdown("""
        <div style="padding: 16px 0 20px; text-align:center;">
            <div style="font-size:1.4rem;">⚖️</div>
            <div style="font-size:0.75rem; color:#9BAFC7;
                        letter-spacing:0.08em; text-transform:uppercase; margin-top:4px;">
                Comparativo
            </div>
        </div>
        """, unsafe_allow_html=True)

        area_opts = {"Nacional": None, "Urbano": 1, "Rural": 2}
        prov_opts = {"Todas": None, **{v: k for k, v in sorted(
            PROVINCIAS_ORDENADAS.items(), key=lambda x: x[1])}}

        # ── Grupo A ───────────────────────────────────────────────
        st.markdown(
            "<p style='color:#7AA3C7; font-size:0.78rem; font-weight:600;'>"
            "🔵 Grupo A</p>",
            unsafe_allow_html=True,
        )
        area_a = st.selectbox("Área A", list(area_opts.keys()), key="cmp_area_a")
        prov_a = st.selectbox("Provincia A", list(prov_opts.keys()), key="cmp_prov_a")

        st.markdown("<hr style='border-color:#2A3A52;'>", unsafe_allow_html=True)

        # ── Grupo B ───────────────────────────────────────────────
        st.markdown(
            "<p style='color:#E8A87C; font-size:0.78rem; font-weight:600;'>"
            "🟠 Grupo B</p>",
            unsafe_allow_html=True,
        )
        area_b = st.selectbox("Área B", list(area_opts.keys()),
                               index=1, key="cmp_area_b")
        prov_b = st.selectbox("Provincia B", list(prov_opts.keys()), key="cmp_prov_b")

    fa = {"area": area_opts[area_a], "prov": prov_opts.get(prov_a),
          "label": f"{area_a}" + (f" · {prov_a}" if prov_opts.get(prov_a) else "")}
    fb = {"area": area_opts[area_b], "prov": prov_opts.get(prov_b),
          "label": f"{area_b}" + (f" · {prov_b}" if prov_opts.get(prov_b) else "")}
    return fa, fb
