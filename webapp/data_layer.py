"""
webapp/data_layer.py  — versión corregida
────────────────────────────────────────────────────────────────────
Correcciones aplicadas:
1. _db_disponible(tabla) verifica la tabla específica, no solo la nacional.
   Esto evita que cargar_por_provincia() use SQLite cuando la tabla
   provincial no existe, saltándose el fallback al engine dinámico.
2. cargar_por_area() y cargar_por_provincia() verifican su propia tabla.
3. cargar_por_provincia() añade columnas prov_nombre y dimension si faltan,
   garantizando que el gráfico de provincias siempre funcione.
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

# Prefijo de indicador_id → dimensión
_PREFIJO_DIMENSION = {
    "IND_AGUA": "agua",
    "IND_RES":  "residuos",
    "IND_ENE":  "energia",
    "IND_MOV":  "movilidad",
    "IND_CA":   "conciencia",
}


# ── Carga del motor (singleton) ───────────────────────────────────
@st.cache_resource
def _get_engine():
    from calculator.engine   import Engine
    from calculator.exporter import Exporter
    return Engine(), Exporter()


def _db_disponible(tabla: str = "indicadores_nacionales") -> bool:
    """
    Verifica si una tabla ESPECÍFICA del SQLite existe y tiene datos.
    Cada función de carga verifica su propia tabla.
    Antes solo se verificaba 'indicadores_nacionales', lo que causaba
    que cargar_por_provincia() devolviera vacío sin ejecutar el fallback.
    """
    from calculator.exporter import Exporter
    exp = Exporter()
    return tabla in exp.tablas_disponibles()


def _enriquecer_provincia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade prov_nombre y dimension al DataFrame de provincias si faltan.
    Garantiza que el gráfico de barras provinciales funcione siempre.
    """
    if df.empty:
        return df
    # Añadir nombre de provincia
    if "prov_nombre" not in df.columns and "prov" in df.columns:
        df = df.copy()
        df["prov_nombre"] = (
            pd.to_numeric(df["prov"], errors="coerce")
            .map(PROVINCIAS)
        )
    # Añadir columna dimension derivada del indicador_id
    if "dimension" not in df.columns and "indicador_id" in df.columns:
        df = df.copy()
        def _dim(iid):
            for prefijo, dim in _PREFIJO_DIMENSION.items():
                if str(iid).startswith(prefijo):
                    return dim
            return None
        df["dimension"] = df["indicador_id"].apply(_dim)
    return df


# ── Funciones de carga con caché ──────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Cargando indicadores...")
def cargar_nacionales() -> pd.DataFrame:
    if _db_disponible("indicadores_nacionales"):
        engine, exporter = _get_engine()
        df = exporter.cargar_nacionales()
        if not df.empty:
            return df
    engine, _ = _get_engine()
    return engine.calcular_kpis_nacionales()


@st.cache_data(ttl=3600, show_spinner="Cargando datos por área...")
def cargar_por_area() -> pd.DataFrame:
    """Carga indicadores por área — verifica su propia tabla SQLite."""
    if _db_disponible("indicadores_por_area"):
        engine, exporter = _get_engine()
        df = exporter.cargar_por_area()
        if not df.empty:
            return df
    # Fallback dinámico
    from calculator.filters import Filtros
    engine, _ = _get_engine()
    return engine.calcular_todos(desagregacion="area")


@st.cache_data(ttl=3600, show_spinner="Cargando datos por provincia...")
def cargar_por_provincia() -> pd.DataFrame:
    """
    Carga indicadores por provincia.
    Verifica 'indicadores_por_provincia' específicamente.
    Si no existe o está vacía, calcula dinámicamente con el engine.
    Añade prov_nombre y dimension para garantizar compatibilidad con gráficos.
    """
    df = pd.DataFrame()

    if _db_disponible("indicadores_por_provincia"):
        engine, exporter = _get_engine()
        df = exporter.cargar_por_provincia()

    if df.empty:
        # Fallback: calcular dinámicamente
        from calculator.filters import Filtros
        engine, _ = _get_engine()
        df = engine.calcular_todos(desagregacion="prov")

    return _enriquecer_provincia(df)


@st.cache_data(ttl=3600, show_spinner="Calculando indicadores...")
def cargar_dimension(
    dimension: str,
    area: Optional[int] = None,
    prov: Optional[int] = None,
) -> pd.DataFrame:
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
    from calculator.filters import Filtros
    engine, _ = _get_engine()
    fa = Filtros(area=area_a, prov=prov_a)
    fb = Filtros(area=area_b, prov=prov_b)
    return engine.calcular_comparativa(dimension, fa, fb)


# ── Funciones auxiliares ──────────────────────────────────────────

def filtrar_dimension(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """
    Filtra por dimensión.
    Primero intenta la columna 'dimension'; si no existe,
    filtra por prefijo del indicador_id.
    """
    if df.empty:
        return pd.DataFrame()

    if "dimension" in df.columns:
        return df[df["dimension"] == dimension].copy()

    # Fallback: filtrar por prefijo del indicador_id
    if "indicador_id" in df.columns:
        prefijos = {
            "agua":       "IND_AGUA",
            "residuos":   "IND_RES",
            "energia":    "IND_ENE",
            "movilidad":  "IND_MOV",
            "conciencia": "IND_CA",
        }
        prefijo = prefijos.get(dimension, "")
        if prefijo:
            return df[df["indicador_id"].str.startswith(prefijo)].copy()

    return pd.DataFrame()


def obtener_valor(
    df: pd.DataFrame,
    indicador_id: str,
    col: str = "valor",
) -> Optional[float]:
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
    if area is None and prov is None:
        return "area"
    return None


def mostrar_error_sin_datos() -> None:
    st.error(
        "**No hay datos disponibles.**\n\n"
        "Ejecuta primero el pipeline y el motor de cálculo:\n\n"
        "```bash\n"
        "python pipeline/orchestrator.py\n"
        "python calculator/run_calculator.py\n"
        "```"
    )


def mostrar_advertencia_filtro_vacio() -> None:
    st.warning(
        "No hay registros para la combinación de filtros seleccionada. "
        "Prueba con un área o provincia diferente."
    )