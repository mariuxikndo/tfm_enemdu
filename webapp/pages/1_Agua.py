"""webapp/pages/1_Agua.py — Dashboard de prácticas de uso del agua."""
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Agua · MIAH-ENEMDU", page_icon="💧", layout="wide")

from webapp.components.sidebar_filters import render_sidebar
from webapp.components.dimension_page import render_dimension_page

filtros = render_sidebar()

render_dimension_page(
    dimension   = "agua",
    titulo      = "Prácticas de Uso del Agua",
    icono       = "💧",
    color       = "#1A6F9C",
    kpis=[
        {"id": "IND_AGUA_01", "etiqueta": "Reusan el agua"},
        {"id": "IND_AGUA_03", "etiqueta": "Cierran llaves al jabonarse"},
        {"id": "IND_AGUA_04", "etiqueta": "Ducha < 10 min"},
        {"id": "IND_AGUA_06", "etiqueta": "Con economizadores de chorro"},
    ],
    ind_barras  = None,
    ind_indice  = "IND_AGUA_08",
    indice_max  = 7.0,
    filtros     = filtros,
)
