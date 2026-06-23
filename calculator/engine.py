"""
calculator/engine.py
────────────────────────────────────────────────────────────────────
Motor de cálculo de indicadores ambientales MIAH-ENEMDU 2025.

Responsabilidades:
  - Cargar los DataFrames Parquet procesados
  - Aplicar filtros dinámicos (periodo, área, provincia)
  - Calcular cada indicador usando su modelo definido en indicator_models.py
  - Aplicar el factor de expansión muestral (fexp) en todos los cálculos
  - Retornar resultados en DataFrame estructurado

Uso básico:
  from calculator.engine import Engine
  engine = Engine()

  # Calcular todos los indicadores a nivel nacional
  resultados = engine.calcular_todos()

  # Calcular una dimensión con filtro geográfico
  from calculator.filters import Filtros
  resultados = engine.calcular_dimension(
      "agua",
      filtros=Filtros(area=1, prov=17),
      desagregacion="prov"
  )

  # Calcular un indicador específico
  resultado = engine.calcular_uno("IND_AGUA_01", desagregacion="area")
"""

import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from calculator.filters import Filtros
from calculator.indicator_models import (
    Indicador,
    load_catalog,
    catalogo_por_dimension,
    resumen_catalogo,
)
from pipeline.saver import Saver

logger = logging.getLogger(__name__)


class Engine:
    """
    Motor de cálculo de indicadores ambientales MIAH-ENEMDU.

    Parámetros
    ----------
    ruta_settings : str
        Ruta al archivo config/settings.yaml
    ruta_indicators : str
        Ruta al archivo config/indicators.yaml
    """

    def __init__(
        self,
        ruta_settings:   str = "config/settings.yaml",
        ruta_indicators: str = "config/indicators.yaml",
    ):
        self.saver    = Saver(ruta_settings)
        self.catalogo = load_catalog(ruta_indicators)
        self._cache:  dict[str, pd.DataFrame] = {}   # caché de Parquets cargados
        logger.info(
            f"[Engine] Iniciado con {len(self.catalogo)} indicadores "
            f"en {len(set(i.dimension for i in self.catalogo.values()))} dimensiones"
        )

    # ── API pública ───────────────────────────────────────────────

    def calcular_todos(
        self,
        filtros:      Optional[Filtros] = None,
        desagregacion: Optional[str]   = None,
    ) -> pd.DataFrame:
        """
        Calcula todos los indicadores del catálogo.

        Parámetros
        ----------
        filtros       : criterios de filtrado (None = nacional sin filtros)
        desagregacion : None | "area" | "prov"

        Retorna
        -------
        DataFrame con todos los resultados concatenados
        """
        filtros = filtros or Filtros()
        logger.info(
            f"[Engine] Calculando TODOS los indicadores | "
            f"Filtro: {filtros.descripcion()} | Desagregación: {desagregacion or 'Nacional'}"
        )
        return self._calcular_lista(
            list(self.catalogo.keys()), filtros, desagregacion
        )

    def calcular_dimension(
        self,
        dimension:    str,
        filtros:      Optional[Filtros] = None,
        desagregacion: Optional[str]   = None,
    ) -> pd.DataFrame:
        """
        Calcula todos los indicadores de una dimensión.

        Parámetros
        ----------
        dimension     : "agua" | "residuos" | "energia" | "movilidad" | "conciencia"
        filtros       : criterios de filtrado
        desagregacion : None | "area" | "prov"
        """
        filtros = filtros or Filtros()
        ids = [
            iid for iid, ind in self.catalogo.items()
            if ind.dimension == dimension
        ]
        if not ids:
            logger.warning(f"[Engine] Dimensión '{dimension}' no encontrada en el catálogo.")
            return pd.DataFrame()

        logger.info(
            f"[Engine] Calculando {len(ids)} indicadores de '{dimension}' | "
            f"Filtro: {filtros.descripcion()}"
        )
        return self._calcular_lista(ids, filtros, desagregacion)

    def calcular_uno(
        self,
        indicador_id: str,
        filtros:      Optional[Filtros] = None,
        desagregacion: Optional[str]   = None,
    ) -> pd.DataFrame:
        """
        Calcula un único indicador por su ID.

        Parámetros
        ----------
        indicador_id  : ej. "IND_AGUA_01"
        filtros       : criterios de filtrado
        desagregacion : None | "area" | "prov"
        """
        filtros = filtros or Filtros()
        if indicador_id not in self.catalogo:
            raise ValueError(
                f"Indicador '{indicador_id}' no encontrado. "
                f"IDs disponibles: {list(self.catalogo.keys())}"
            )
        return self._calcular_lista([indicador_id], filtros, desagregacion)

    def calcular_kpis_nacionales(self) -> pd.DataFrame:
        """
        Calcula todos los indicadores a nivel nacional sin desagregación.
        Útil para la página de inicio de la webapp.
        """
        return self.calcular_todos(filtros=Filtros(), desagregacion=None)

    def calcular_comparativa(
        self,
        dimension: str,
        filtros_a: Filtros,
        filtros_b: Filtros,
        desagregacion: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Calcula los indicadores de una dimensión para dos conjuntos de
        filtros distintos y los devuelve en un DataFrame comparativo.

        Útil para el módulo comparativo de la webapp.

        Parámetros
        ----------
        dimension     : dimensión a comparar
        filtros_a     : primer contexto (ej. Urbano)
        filtros_b     : segundo contexto (ej. Rural)

        Retorna
        -------
        DataFrame con columna 'grupo' ('A' | 'B') y metadatos de filtro
        """
        df_a = self.calcular_dimension(dimension, filtros_a, desagregacion)
        df_b = self.calcular_dimension(dimension, filtros_b, desagregacion)

        if not df_a.empty:
            df_a["grupo"]        = "A"
            df_a["filtro_desc"]  = filtros_a.descripcion()
        if not df_b.empty:
            df_b["grupo"]        = "B"
            df_b["filtro_desc"]  = filtros_b.descripcion()

        if df_a.empty and df_b.empty:
            return pd.DataFrame()

        return pd.concat([df_a, df_b], ignore_index=True)

    # ── Métodos privados ─────────────────────────────────────────

    def _calcular_lista(
        self,
        ids:          list[str],
        filtros:      Filtros,
        desagregacion: Optional[str],
    ) -> pd.DataFrame:
        """Calcula una lista de indicadores y concatena los resultados."""
        resultados = []
        errores    = []
        t_inicio   = time.time()

        # Agrupar por archivo fuente para cargar cada Parquet solo una vez
        por_archivo: dict[str, list[str]] = {}
        for iid in ids:
            archivo = self.catalogo[iid].archivo
            por_archivo.setdefault(archivo, []).append(iid)

        for archivo, iids_archivo in por_archivo.items():

            # Verificar compatibilidad de filtro de periodo con el archivo
            if not filtros.es_compatible(archivo) and filtros.periodo is not None:
                logger.info(
                    f"  [Engine] Saltando {archivo} — "
                    f"periodo '{filtros.periodo}' no corresponde a este archivo"
                )
                continue

            # Cargar Parquet (con caché)
            df = self._cargar_parquet(archivo)
            if df is None or df.empty:
                logger.warning(f"  [Engine] No se pudo cargar {archivo}")
                continue

            # Aplicar filtros
            df_f = filtros.aplicar(df)
            if df_f.empty:
                logger.warning(
                    f"  [Engine] {archivo}: DataFrame vacío después de filtrar "
                    f"({filtros.descripcion()})"
                )
                continue

            # Calcular cada indicador del archivo
            for iid in iids_archivo:
                ind = self.catalogo[iid]
                try:
                    t0  = time.time()
                    res = ind.calcular(df_f, desagregacion=desagregacion)
                    if res is not None and not res.empty:
                        res["archivo"] = archivo
                        resultados.append(res)
                        logger.debug(
                            f"  ✓ {iid} — {len(res)} filas · "
                            f"{time.time()-t0:.2f}s"
                        )
                    else:
                        logger.warning(f"  {iid} — resultado vacío")
                except Exception as e:
                    logger.error(f"  ✗ {iid} — Error: {e}")
                    errores.append(iid)

        duracion = time.time() - t_inicio
        logger.info(
            f"[Engine] Cálculo completado: "
            f"{len(resultados)} indicadores calculados, "
            f"{len(errores)} errores · {duracion:.2f}s"
        )

        if not resultados:
            return pd.DataFrame()

        df_final = pd.concat(resultados, ignore_index=True)
        return self._ordenar_resultado(df_final)

    def _cargar_parquet(self, archivo: str) -> Optional[pd.DataFrame]:
        """Carga un Parquet desde disco o lo retorna desde la caché."""
        if archivo not in self._cache:
            try:
                self._cache[archivo] = self.saver.load_one(archivo)
                logger.debug(
                    f"  [Engine] Cargado {archivo} "
                    f"({len(self._cache[archivo]):,} filas)"
                )
            except FileNotFoundError as e:
                logger.error(
                    f"  [Engine] {e}\n"
                    "  → Ejecuta primero: python pipeline/orchestrator.py"
                )
                return None
        return self._cache[archivo]

    def _ordenar_resultado(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ordena las columnas del DataFrame de resultados de forma estándar."""
        cols_fijas = [
            "dimension", "indicador_id", "indicador",
            "valor", "unidad", "n_muestra", "pob_estimada",
        ]
        cols_extra = [c for c in df.columns if c not in cols_fijas]
        cols_orden = [c for c in cols_fijas if c in df.columns] + cols_extra
        return df[cols_orden].sort_values(
            ["dimension", "indicador_id"], ignore_index=True
        )

    def limpiar_cache(self) -> None:
        """Limpia la caché de DataFrames en memoria."""
        self._cache.clear()
        logger.info("[Engine] Caché limpiada.")

    def resumen(self) -> None:
        """Imprime el resumen del catálogo de indicadores."""
        resumen_catalogo(self.catalogo)
