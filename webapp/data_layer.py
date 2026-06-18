"""
webapp/data_layer.py
────────────────────────────────────────────────────────────────────
Capa de acceso a datos para la webapp Streamlit.

Conecta la interfaz con el motor de cálculo mediante:
  1. Modo rápido   : lee resultados precalculados desde SQLite
  2. Modo dinámico : calcula directamente con Engine (si no hay SQLite)

Todas las funciones usan @st.cache_data para evitar recálculos
en cada interacción del usuario.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Constantes ───────────────────────────────────────────────────
COLORES_DIMENSION = {
    "agua":       "#1A6F9C",
    "residuos":   "#2D8C3F",
    "energia":    "#D97706",
    "movilidad":  "#7C3AED",
    "conciencia": "#C0392B",
}

NOMBRES_DIMENSION = {
    "agua":       "💧 Uso del Agua",
    "residuos":   "♻️ Gestión de Residuos",
    "energia":    "⚡ Eficiencia Energética",
    "movilidad":  "🚌 Movilidad",
    "conciencia": "🌍 Conciencia Ambiental",
}

PROVINCIAS = {
    1: "Azuay",        2: "Bolívar",       3: "Cañar",
    4: "Carchi",       5: "Cotopaxi",      6: "Chimborazo",
    7: "El Oro",       8: "Esmeraldas",    9: "Guayas",
    10: "Imbabura",    11: "Loja",         12: "Los Ríos",
    13: "Manabí",      14: "Morona Santiago", 15: "Napo",
    16: "Pastaza",     17: "Pichincha",    18: "Tungurahua",
    19: "Zamora Chinchipe", 20: "Galápagos", 21: "Sucumbíos",
    22: "Orellana",    23: "Santo Domingo", 24: "Santa Elena",
    90: "Zonas No Delimitadas",
}


# ── Carga del motor (singleton) ───────────────────────────────────
@st.cache_resource
def _get_engine():
    """Inicializa el Engine una sola vez por sesión."""
    from calculator.engine   import Engine
    from calculator.exporter import Exporter
    return Engine(), Exporter()


def _db_disponible() -> bool:
    """Verifica si el SQLite de indicadores está disponible."""
    from calculator.exporter import Exporter
    exp = Exporter()
    tablas = exp.tablas_disponibles()
    return "indicadores_nacionales" in tablas


# ── Funciones de carga con caché ──────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Cargando indicadores...")
def cargar_nacionales() -> pd.DataFrame:
    """
    Carga todos los indicadores a nivel nacional.
    Modo rápido: SQLite. Modo dinámico: Engine.
    """
    if _db_disponible():
        engine, exporter = _get_engine()
        return exporter.cargar_nacionales()
    else:
        engine, _ = _get_engine()
        return engine.calcular_kpis_nacionales()


@st.cache_data(ttl=3600, show_spinner="Cargando datos por área...")
def cargar_por_area() -> pd.DataFrame:
    """Carga indicadores desagregados por área (urbano/rural)."""
    if _db_disponible():
        engine, exporter = _get_engine()
        return exporter.cargar_por_area()
    else:
        from calculator.filters import Filtros
        engine, _ = _get_engine()
        return engine.calcular_todos(desagregacion="area")


@st.cache_data(ttl=3600, show_spinner="Cargando datos por provincia...")
def cargar_por_provincia() -> pd.DataFrame:
    """Carga indicadores desagregados por provincia."""
    if _db_disponible():
        engine, exporter = _get_engine()
        return exporter.cargar_por_provincia()
    else:
        from calculator.filters import Filtros
        engine, _ = _get_engine()
        return engine.calcular_todos(desagregacion="prov")


@st.cache_data(ttl=3600, show_spinner="Calculando indicadores...")
def cargar_dimension(
    dimension: str,
    area: Optional[int] = None,
    prov: Optional[int] = None,
) -> pd.DataFrame:
    """
    Carga indicadores de una dimensión con filtros opcionales.

    Parámetros
    ----------
    dimension : "agua" | "residuos" | "energia" | "movilidad" | "conciencia"
    area      : 1=Urbano | 2=Rural | None (todos)
    prov      : código de provincia | None (todas)
    """
    from calculator.filters import Filtros
    engine, _ = _get_engine()
    filtros = Filtros(area=area, prov=prov)
    desag = _inferir_desagregacion(area, prov)
    return engine.calcular_dimension(dimension, filtros=filtros, desagregacion=desag)


@st.cache_data(ttl=3600, show_spinner="Preparando comparativa...")
def cargar_comparativa(
    dimension: str,
    area_a: Optional[int], prov_a: Optional[int],
    area_b: Optional[int], prov_b: Optional[int],
) -> pd.DataFrame:
    """
    Carga una comparativa entre dos conjuntos de filtros.
    """
    from calculator.filters import Filtros
    engine, _ = _get_engine()
    fa = Filtros(area=area_a, prov=prov_a)
    fb = Filtros(area=area_b, prov=prov_b)
    return engine.calcular_comparativa(dimension, fa, fb)


# ── Funciones auxiliares ──────────────────────────────────────────

def filtrar_dimension(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Filtra un DataFrame de resultados por dimensión."""
    if df.empty or "dimension" not in df.columns:
        return pd.DataFrame()
    return df[df["dimension"] == dimension].copy()


def obtener_valor(
    df: pd.DataFrame,
    indicador_id: str,
    col: str = "valor",
) -> Optional[float]:
    """Extrae el valor de un indicador específico."""
    if df.empty or "indicador_id" not in df.columns:
        return None
    fila = df[df["indicador_id"] == indicador_id]
    if fila.empty or col not in fila.columns:
        return None
    return float(fila[col].iloc[0])


def _inferir_desagregacion(
    area: Optional[int],
    prov: Optional[int],
) -> Optional[str]:
    """Infiere el nivel de desagregación según los filtros activos."""
    if area is None and prov is None:
        return "area"
    return None


def mostrar_error_sin_datos() -> None:
    """Muestra un mensaje de error cuando no hay datos disponibles."""
    st.error(
        "**No hay datos disponibles.**\n\n"
        "Ejecuta primero el pipeline y el motor de cálculo:\n\n"
        "```bash\n"
        "python pipeline/orchestrator.py\n"
        "python calculator/run_calculator.py\n"
        "```"
    )


def mostrar_advertencia_filtro_vacio() -> None:
    """Muestra advertencia cuando un filtro deja el dataset vacío."""
    st.warning(
        "No hay registros para la combinación de filtros seleccionada. "
        "Prueba con un área o provincia diferente."
    )
