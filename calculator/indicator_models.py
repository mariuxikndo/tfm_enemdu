"""
calculator/indicator_models.py
────────────────────────────────────────────────────────────────────
Modelos de indicadores ambientales MIAH-ENEMDU 2025.

Este módulo define:
  1. La clase base Indicador con sus atributos y método calcular()
  2. Tres subclases según el tipo de cálculo:
       IndicadorProporcion  → % de hogares/personas con práctica positiva
       IndicadorMedia       → media ponderada de una variable continua
       IndicadorIndice      → media ponderada de un índice compuesto
  3. El catálogo CATALOGO_INDICADORES con todas las instancias
  4. La función load_catalog() que construye el catálogo desde indicators.yaml

Uso:
  from calculator.indicator_models import load_catalog
  catalogo = load_catalog()
  ind = catalogo["IND_AGUA_01"]
  resultado = ind.calcular(df, desagregacion="area")
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  Clase base
# ══════════════════════════════════════════════════════════════════

@dataclass
class Indicador(ABC):
    """
    Clase base para todos los indicadores ambientales.

    Atributos
    ---------
    id           : código único (ej. "IND_AGUA_01")
    nombre       : etiqueta corta para la interfaz
    descripcion  : descripción completa para fichas técnicas
    dimension    : agua | residuos | energia | movilidad | conciencia
    archivo      : ambiental_ago | ambiental_oct | persona_ago
    tipo         : proporcion | media | indice
    variable     : nombre de la columna en el Parquet
    valor_pos    : valor(es) que representan la práctica positiva
    excluir_vals : valores que excluyen un registro del denominador
    unidad       : unidad de medida del resultado
    formula      : descripción de la fórmula en texto
    desagregable : lista de dimensiones de desagregación disponibles
    ods          : Objetivo de Desarrollo Sostenible relacionado
    nota         : aclaraciones adicionales (opcional)
    """
    id:           str
    nombre:       str
    descripcion:  str
    dimension:    str
    archivo:      str
    tipo:         str
    variable:     str
    valor_pos:    Optional[list]
    excluir_vals: list
    unidad:       str
    formula:      str
    desagregable: list
    ods:          str
    nota:         str = ""

    @abstractmethod
    def calcular(
        self,
        df: pd.DataFrame,
        col_fexp: str = "fexp",
        desagregacion: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Calcula el indicador sobre el DataFrame.

        Parámetros
        ----------
        df            : DataFrame procesado (del Saver)
        col_fexp      : nombre de la columna del factor de expansión
        desagregacion : None (nacional) | "area" | "prov" | "area_prov"

        Retorna
        -------
        DataFrame con columnas: [dimensiones_desagregacion, 'valor', 'n_muestra', 'pob_estimada']
        """

    def _preparar_df(
        self,
        df: pd.DataFrame,
        col_fexp: str,
    ) -> pd.DataFrame:
        """Filtra registros con fexp válido y variable no nula."""
        df_v = df.dropna(subset=[self.variable, col_fexp]).copy()
        df_v = df_v[df_v[col_fexp] > 0]
        if df_v.empty:
            logger.warning(f"[{self.id}] DataFrame vacío después de filtrar nulos.")
        return df_v

    def _cols_desagregacion(self, desagregacion: Optional[str]) -> list[str]:
        """Retorna las columnas de agrupación según la desagregación solicitada."""
        if desagregacion is None:
            return []
        if desagregacion == "area":
            return ["area", "area_nombre"] if "area_nombre" in [] else ["area"]
        if desagregacion == "prov":
            return ["prov", "prov_nombre"] if "prov_nombre" in [] else ["prov"]
        if desagregacion == "area_prov":
            return ["area", "prov"]
        return []

    def _cols_desagregacion_df(
        self, df: pd.DataFrame, desagregacion: Optional[str]
    ) -> list[str]:
        """Igual que _cols_desagregacion pero verifica que las columnas existan."""
        candidatas = {
            None:        [],
            "area":      ["area", "area_nombre"],
            "prov":      ["prov", "prov_nombre"],
            "area_prov": ["area", "area_nombre", "prov", "prov_nombre"],
        }.get(desagregacion, [])
        return [c for c in candidatas if c in df.columns]


# ══════════════════════════════════════════════════════════════════
#  Subclase 1: Proporción ponderada
# ══════════════════════════════════════════════════════════════════

@dataclass
class IndicadorProporcion(Indicador):
    """
    Calcula el porcentaje ponderado de hogares/personas
    que presentan el valor positivo en la variable.

    Fórmula:
        valor = sum(fexp donde variable en valor_pos)
                / sum(fexp donde variable no en excluir_vals y no es NaN)
                × 100
    """

    def calcular(
        self,
        df: pd.DataFrame,
        col_fexp: str = "fexp",
        desagregacion: Optional[str] = None,
    ) -> pd.DataFrame:

        df_v = self._preparar_df(df, col_fexp)
        if df_v.empty:
            return pd.DataFrame()

        # Convertir variable a numérico
        df_v[self.variable] = pd.to_numeric(df_v[self.variable], errors="coerce")

        # Excluir valores que no deben entrar en el denominador
        if self.excluir_vals:
            df_v = df_v[~df_v[self.variable].isin(self.excluir_vals)].copy()

        # Marcar registros positivos
        df_v["_positivo"] = df_v[self.variable].isin(self.valor_pos).astype(float)

        cols_grupo = self._cols_desagregacion_df(df_v, desagregacion)

        def _calcular_grupo(grupo: pd.DataFrame) -> pd.Series:
            fexp        = grupo[col_fexp]
            positivo    = grupo["_positivo"]
            pob_total   = fexp.sum()
            pob_pos     = (fexp * positivo).sum()
            valor       = (pob_pos / pob_total * 100) if pob_total > 0 else np.nan
            return pd.Series({
                "valor":         round(valor, 2),
                "n_muestra":     int(len(grupo)),
                "pob_estimada":  round(pob_total, 0),
            })

        if cols_grupo:
            resultado = (
                df_v.groupby(cols_grupo, observed=True)
                .apply(_calcular_grupo)
                .reset_index()
            )
        else:
            # Nivel nacional
            res = _calcular_grupo(df_v)
            resultado = pd.DataFrame([res])
            resultado.insert(0, "desagregacion", "Nacional")

        resultado["indicador_id"]  = self.id
        resultado["indicador"]     = self.nombre
        resultado["unidad"]        = self.unidad
        resultado["dimension"]     = self.dimension
        return resultado


# ══════════════════════════════════════════════════════════════════
#  Subclase 2: Media ponderada
# ══════════════════════════════════════════════════════════════════

@dataclass
class IndicadorMedia(Indicador):
    """
    Calcula la media ponderada de una variable continua.

    Fórmula:
        valor = sum(fexp × variable) / sum(fexp)
    """

    def calcular(
        self,
        df: pd.DataFrame,
        col_fexp: str = "fexp",
        desagregacion: Optional[str] = None,
    ) -> pd.DataFrame:

        df_v = self._preparar_df(df, col_fexp)
        if df_v.empty:
            return pd.DataFrame()

        df_v[self.variable] = pd.to_numeric(df_v[self.variable], errors="coerce")
        df_v = df_v.dropna(subset=[self.variable]).copy()

        cols_grupo = self._cols_desagregacion_df(df_v, desagregacion)

        def _calcular_grupo(grupo: pd.DataFrame) -> pd.Series:
            fexp      = grupo[col_fexp]
            valores   = grupo[self.variable]
            pob_total = fexp.sum()
            media_p   = (fexp * valores).sum() / pob_total if pob_total > 0 else np.nan
            return pd.Series({
                "valor":        round(media_p, 2),
                "n_muestra":    int(len(grupo)),
                "pob_estimada": round(pob_total, 0),
            })

        if cols_grupo:
            resultado = (
                df_v.groupby(cols_grupo, observed=True)
                .apply(_calcular_grupo)
                .reset_index()
            )
        else:
            res = _calcular_grupo(df_v)
            resultado = pd.DataFrame([res])
            resultado.insert(0, "desagregacion", "Nacional")

        resultado["indicador_id"] = self.id
        resultado["indicador"]    = self.nombre
        resultado["unidad"]       = self.unidad
        resultado["dimension"]    = self.dimension
        return resultado


# ══════════════════════════════════════════════════════════════════
#  Subclase 3: Índice compuesto ponderado
# ══════════════════════════════════════════════════════════════════

@dataclass
class IndicadorIndice(Indicador):
    """
    Calcula la media ponderada de un índice compuesto ya precalculado
    en el transformer (idx_agua, idx_energia, idx_conciencia).

    Fórmula:
        valor = sum(fexp × indice) / sum(fexp)
    """

    def calcular(
        self,
        df: pd.DataFrame,
        col_fexp: str = "fexp",
        desagregacion: Optional[str] = None,
    ) -> pd.DataFrame:
        # Los índices son medias ponderadas — reutilizamos IndicadorMedia
        media = IndicadorMedia(
            id=self.id, nombre=self.nombre, descripcion=self.descripcion,
            dimension=self.dimension, archivo=self.archivo, tipo=self.tipo,
            variable=self.variable, valor_pos=None, excluir_vals=[],
            unidad=self.unidad, formula=self.formula,
            desagregable=self.desagregable, ods=self.ods, nota=self.nota,
        )
        return media.calcular(df, col_fexp, desagregacion)


# ══════════════════════════════════════════════════════════════════
#  Carga del catálogo desde indicators.yaml
# ══════════════════════════════════════════════════════════════════

_TIPO_A_CLASE = {
    "proporcion": IndicadorProporcion,
    "media":      IndicadorMedia,
    "indice":     IndicadorIndice,
}


def load_catalog(
    ruta_yaml: str = "config/indicators.yaml",
) -> dict[str, Indicador]:
    """
    Carga todos los indicadores desde indicators.yaml y retorna
    un diccionario {id: instancia_de_Indicador}.

    Parámetros
    ----------
    ruta_yaml : str
        Ruta al archivo de catálogo de indicadores

    Retorna
    -------
    dict[str, Indicador]
    """
    ruta = Path(ruta_yaml)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta_yaml}. "
            "Verifica que ejecutas desde la raíz del proyecto."
        )

    with open(ruta, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    catalogo: dict[str, Indicador] = {}
    errores = []

    for item in data.get("indicadores", []):
        tipo = item.get("tipo", "").lower()
        clase = _TIPO_A_CLASE.get(tipo)
        if clase is None:
            errores.append(f"Tipo '{tipo}' desconocido en indicador {item.get('id')}")
            continue

        try:
            ind = clase(
                id           = item["id"],
                nombre       = item["nombre"],
                descripcion  = item["descripcion"],
                dimension    = item["dimension"],
                archivo      = item["archivo"],
                tipo         = item["tipo"],
                variable     = item["variable"],
                valor_pos    = item.get("valor_pos"),
                excluir_vals = item.get("excluir_vals", []) or [],
                unidad       = item.get("unidad", ""),
                formula      = item.get("formula", ""),
                desagregable = item.get("desagregable", []) or [],
                ods          = item.get("ods", ""),
                nota         = item.get("nota", ""),
            )
            catalogo[ind.id] = ind
        except Exception as e:
            errores.append(f"Error construyendo {item.get('id')}: {e}")

    if errores:
        for err in errores:
            logger.error(f"[load_catalog] {err}")

    logger.info(
        f"[load_catalog] Catálogo cargado: {len(catalogo)} indicadores "
        f"en {len(set(i.dimension for i in catalogo.values()))} dimensiones"
    )
    return catalogo


def catalogo_por_dimension(
    catalogo: dict[str, Indicador],
) -> dict[str, list[Indicador]]:
    """
    Agrupa el catálogo por dimensión.

    Retorna
    -------
    dict[str, list[Indicador]]
    """
    grupos: dict[str, list] = {}
    for ind in catalogo.values():
        grupos.setdefault(ind.dimension, []).append(ind)
    return grupos


def resumen_catalogo(catalogo: dict[str, Indicador]) -> None:
    """Imprime un resumen del catálogo en consola."""
    grupos = catalogo_por_dimension(catalogo)
    print("\n" + "═" * 55)
    print("  CATÁLOGO DE INDICADORES MIAH-ENEMDU 2025")
    print("═" * 55)
    total = 0
    for dim, inds in sorted(grupos.items()):
        print(f"\n  {dim.upper()} ({len(inds)} indicadores)")
        for ind in inds:
            print(f"    {ind.id:<15} {ind.nombre[:45]}")
            total += 1
    print(f"\n  Total: {total} indicadores")
    print("═" * 55 + "\n")
