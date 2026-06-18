"""webapp/pages/5_Conciencia.py — Dashboard de conciencia ambiental."""
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Conciencia · MIAH-ENEMDU", page_icon="🌍", layout="wide")

from webapp.components.sidebar_filters import render_sidebar
from webapp.components.dimension_page import render_dimension_page

filtros = render_sidebar()

render_dimension_page(
    dimension   = "conciencia",
    titulo      = "Conciencia y Responsabilidad Ambiental",
    icono       = "🌍",
    color       = "#C0392B",
    kpis=[
        {"id": "IND_CA_01", "etiqueta": "Perciben problemas ambientales"},
        {"id": "IND_CA_02", "etiqueta": "Muy preocupados por el ambiente"},
        {"id": "IND_CA_03", "etiqueta": "Participaron en actividad ambiental"},
        {"id": "IND_CA_04", "etiqueta": "Usan bolsa reutilizable"},
    ],
    ind_barras  = None,
    ind_indice  = "IND_CA_05",
    indice_max  = 3.0,
    filtros     = filtros,
)
