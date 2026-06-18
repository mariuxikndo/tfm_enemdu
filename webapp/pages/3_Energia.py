"""webapp/pages/3_Energia.py — Dashboard de eficiencia energética."""
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Energía · MIAH-ENEMDU", page_icon="⚡", layout="wide")

from webapp.components.sidebar_filters import render_sidebar
from webapp.components.dimension_page import render_dimension_page

filtros = render_sidebar()

render_dimension_page(
    dimension   = "energia",
    titulo      = "Eficiencia Energética del Hogar",
    icono       = "⚡",
    color       = "#D97706",
    kpis=[
        {"id": "IND_ENE_01", "etiqueta": "Desconectan aparatos"},
        {"id": "IND_ENE_02", "etiqueta": "Apagan focos al salir"},
        {"id": "IND_ENE_05", "etiqueta": "Aprovechan luz solar"},
        {"id": "IND_ENE_06", "etiqueta": "Con electrodomésticos ahorradores"},
    ],
    ind_barras  = None,
    ind_indice  = "IND_ENE_08",
    indice_max  = 7.0,
    filtros     = filtros,
)
