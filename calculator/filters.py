"""
calculator/filters.py
────────────────────────────────────────────────────────────────────
Módulo de filtros dinámicos para el motor de cálculo MIAH-ENEMDU.

Define la clase Filtros que encapsula los criterios de selección
aplicables a cualquier DataFrame procesado del pipeline.

Filtros disponibles:
  - periodo    : "2025-08" | "2025-10" | None (ambos periodos)
  - area       : 1=Urbano | 2=Rural | None (urbano + rural)
  - prov       : código INEC de provincia | None (todas)
  - edad_min   : edad mínima (solo para persona_ago)
  - edad_max   : edad máxima (solo para persona_ago)

Uso:
  from calculator.filters import Filtros
  f = Filtros(area=1, prov=17)            # Urbano, Pichincha
  df_filtrado = f.aplicar(df)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ── Mapas de referencia ───────────────────────────────────────────
ETIQUETAS_AREA = {1: "Urbano", 2: "Rural"}

ETIQUETAS_PERIODO = {
    "2025-08": "Agosto 2025",
    "2025-10": "Octubre 2025",
}

PERIODOS_POR_ARCHIVO = {
    "ambiental_ago": ["2025-08"],
    "ambiental_oct": ["2025-10"],
    "persona_ago":   ["2025-08"],
}


@dataclass
class Filtros:
    """
    Encapsula los criterios de filtrado para el motor de cálculo.

    Parámetros
    ----------
    periodo  : "2025-08" | "2025-10" | None (sin filtro de periodo)
    area     : 1 (Urbano) | 2 (Rural) | None (todos)
    prov     : código INEC de provincia (1-24, 90) | None (todas)
    edad_min : edad mínima (aplica solo a persona_ago)
    edad_max : edad máxima (aplica solo a persona_ago)
    """
    periodo:  Optional[str] = None
    area:     Optional[int] = None
    prov:     Optional[int] = None
    edad_min: Optional[int] = None
    edad_max: Optional[int] = None

    def aplicar(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica todos los filtros definidos al DataFrame.

        Parámetros
        ----------
        df : DataFrame procesado (del Saver)

        Retorna
        -------
        DataFrame filtrado (copia, no modifica el original)
        """
        df_f = df.copy()
        n_orig = len(df_f)

        df_f = self._filtrar_periodo(df_f)
        df_f = self._filtrar_area(df_f)
        df_f = self._filtrar_provincia(df_f)
        df_f = self._filtrar_edad(df_f)

        n_final = len(df_f)
        if n_orig != n_final:
            logger.debug(
                f"[Filtros] {n_orig:,} → {n_final:,} filas "
                f"({n_orig - n_final:,} excluidas) | {self.descripcion()}"
            )
        return df_f

    def descripcion(self) -> str:
        """Retorna una descripción legible del filtro activo."""
        partes = []
        if self.periodo:
            partes.append(ETIQUETAS_PERIODO.get(self.periodo, self.periodo))
        if self.area is not None:
            partes.append(ETIQUETAS_AREA.get(self.area, f"Área {self.area}"))
        if self.prov is not None:
            partes.append(f"Provincia {self.prov}")
        if self.edad_min is not None or self.edad_max is not None:
            edad_str = f"Edad {self.edad_min or ''}–{self.edad_max or ''}"
            partes.append(edad_str)
        return ", ".join(partes) if partes else "Nacional (sin filtros)"

    def es_compatible(self, archivo: str) -> bool:
        """
        Verifica si el filtro de periodo es compatible con el archivo fuente.

        Un filtro de periodo "2025-10" no aplica a ambiental_ago (que es "2025-08").
        """
        if self.periodo is None:
            return True
        periodos_validos = PERIODOS_POR_ARCHIVO.get(archivo, [])
        return self.periodo in periodos_validos

    # ── Filtros internos ─────────────────────────────────────────

    def _filtrar_periodo(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.periodo is None or "periodo" not in df.columns:
            return df
        return df[df["periodo"] == self.periodo].copy()

    def _filtrar_area(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.area is None or "area" not in df.columns:
            return df
        return df[df["area"] == self.area].copy()

    def _filtrar_provincia(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.prov is None:
            return df
        col = "prov" if "prov" in df.columns else None
        if col is None:
            return df
        return df[df[col] == self.prov].copy()

    def _filtrar_edad(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.edad_min is None and self.edad_max is None:
            return df
        if "p03" not in df.columns:
            return df
        edad = pd.to_numeric(df["p03"], errors="coerce")
        mascara = pd.Series(True, index=df.index)
        if self.edad_min is not None:
            mascara &= edad >= self.edad_min
        if self.edad_max is not None:
            mascara &= edad <= self.edad_max
        return df[mascara].copy()

    # ── Constructores de conveniencia ────────────────────────────

    @classmethod
    def nacional(cls) -> "Filtros":
        """Sin filtros — nivel nacional, ambos periodos."""
        return cls()

    @classmethod
    def urbano(cls) -> "Filtros":
        return cls(area=1)

    @classmethod
    def rural(cls) -> "Filtros":
        return cls(area=2)

    @classmethod
    def provincia(cls, codigo: int) -> "Filtros":
        return cls(prov=codigo)

    @classmethod
    def urbano_provincia(cls, codigo: int) -> "Filtros":
        return cls(area=1, prov=codigo)
