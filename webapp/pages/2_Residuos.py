"""webapp/pages/2_Residuos.py — Dashboard de gestión de residuos."""
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Residuos · MIAH-ENEMDU", page_icon="♻️", layout="wide")

from webapp.components.sidebar_filters import render_sidebar
from webapp.components.dimension_page import render_dimension_page

filtros = render_sidebar()

render_dimension_page(
    dimension   = "residuos",
    titulo      = "Gestión y Clasificación de Residuos",
    icono       = "♻️",
    color       = "#2D8C3F",
    kpis=[
        {"id": "IND_RES_01", "etiqueta": "Clasificaron orgánicos"},
        {"id": "IND_RES_03", "etiqueta": "Clasificaron plástico"},
        {"id": "IND_RES_05", "etiqueta": "Al menos un inorgánico"},
        {"id": "IND_RES_06", "etiqueta": "Disposición adecuada orgánicos"},
    ],
    ind_barras  = None,
    ind_indice  = None,
    filtros     = filtros,
)
