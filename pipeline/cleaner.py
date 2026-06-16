"""
pipeline/cleaner.py
────────────────────────────────────────────────────────────────────
Módulo de limpieza de microdatos MIAH-ENEMDU 2025.

Responsabilidades:
  - Aplicar reglas de limpieza definidas en config/cleaning_rules.yaml
  - Reemplazar valores nulos/inválidos por NaN
  - Convertir columnas al tipo de dato correcto
  - Validar rangos permitidos
  - Registrar métricas de calidad (% nulos antes/después)

Uso:
  from pipeline.cleaner import Cleaner
  cleaner = Cleaner()
  dfs_limpios = cleaner.clean_all(dfs_crudos)
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class Cleaner:
    """
    Aplica reglas de limpieza a los DataFrames del MIAH-ENEMDU.

    Parámetros
    
    ruta_reglas : str
        Ruta al archivo config/cleaning_rules.yaml
    """

    def __init__(self, ruta_reglas: str = "config/cleaning_rules.yaml"):
        self.reglas = self._cargar_reglas(ruta_reglas)

    # Métodos públicos

    def clean_all(
        self, dfs: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
        """
        Limpia todos los DataFrames del diccionario.

        Parámetros
       
        dfs : dict con claves "ambiental_ago", "ambiental_oct", "persona_ago"

        Retorna
        
        dict con los mismos DataFrames después de limpieza
        """
        dfs_limpios = {}
        for clave, df in dfs.items():
            logger.info(f"[cleaner] Limpiando {clave} ({len(df):,} filas)...")
            df_limpio = self.clean_one(df, clave)
            dfs_limpios[clave] = df_limpio
        return dfs_limpios

    def clean_one(
        self, df: pd.DataFrame, clave: str = ""
    ) -> pd.DataFrame:
        """
        Limpia un único DataFrame aplicando las reglas del YAML.

        Parámetros

        df    : DataFrame crudo del ingester
        clave : nombre del archivo (para logging)
        """
        df = df.copy()
        metricas_antes = self._contar_nulos(df)

        # 1. Limpiar cada columna según sus reglas
        for col in df.columns:
            if col not in self.reglas:
                continue
            regla = self.reglas[col]
            df[col] = self._limpiar_columna(df[col], regla, col)

        # 2. Eliminar filas donde fexp es inválido
        if "fexp" in df.columns:
            antes = len(df)
            df = df[df["fexp"].notna() & (df["fexp"] > 0)].copy()
            eliminadas = antes - len(df)
            if eliminadas > 0:
                logger.warning(
                    f"[{clave}] {eliminadas} filas eliminadas por fexp inválido"
                )

        metricas_despues = self._contar_nulos(df)
        self._log_metricas(clave, metricas_antes, metricas_despues, len(df))

        return df

    # Métodos privados

    def _cargar_reglas(self, ruta: str) -> dict:
        """Carga el archivo cleaning_rules.yaml."""
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            logger.warning(
                f"No se encontró cleaning_rules.yaml en '{ruta}'. "
                "Se aplicará limpieza mínima."
            )
            return {}
        with open(ruta_path, encoding="utf-8") as f:
            reglas_raw = yaml.safe_load(f)
        # Resolver aliases YAML (los * de las reglas compartidas)
        return reglas_raw if reglas_raw else {}

    def _limpiar_columna(
        self, serie: pd.Series, regla: dict, nombre_col: str
    ) -> pd.Series:
        """
        Aplica una regla de limpieza a una Serie de pandas.

        Pasos:
          1. Reemplazar valores nulos por NaN
          2. Validar rango/lista de valores permitidos
          3. Convertir al tipo de dato destino
        """
        if regla is None:
            return serie

        # Paso 1: reemplazar valores nulos por NaN
        tipo_nulo = regla.get("tipo_nulo", [])
        if tipo_nulo:
            serie = serie.replace(tipo_nulo, np.nan)

        # Paso 2: validar valores permitidos
        valores_valid = regla.get("valores_valid")
        if valores_valid and not serie.isna().all():
            # Convertir temporalmente para comparar
            serie_num = pd.to_numeric(serie, errors="coerce")
            if isinstance(valores_valid, list):
                # Lista de valores permitidos
                mascara_invalida = ~serie_num.isna() & ~serie_num.isin(valores_valid)
                if mascara_invalida.sum() > 0:
                    logger.warning(
                        f"  {nombre_col}: {mascara_invalida.sum()} valores "
                        f"fuera del rango permitido → reemplazados por NaN"
                    )
                    serie = serie.where(~mascara_invalida, np.nan)

        # Paso 3: recodificar si aplica
        recodificar = regla.get("recodificar", {})
        if recodificar:
            serie = serie.replace(recodificar)

        # Paso 4: convertir tipo de dato
        tipo_dato = regla.get("tipo_dato")
        if tipo_dato:
            serie = self._convertir_tipo(serie, tipo_dato, nombre_col)

        # Paso 5: validaciones extras
        extra = regla.get("validacion_extra")
        if extra == "mayor_que_cero":
            serie = serie.where(serie > 0, np.nan)
        elif extra == "mayor_igual_cero":
            serie = serie.where(serie >= 0, np.nan)

        return serie

    def _convertir_tipo(
        self, serie: pd.Series, tipo: str, nombre_col: str
    ) -> pd.Series:
        """Convierte una Serie al tipo de dato especificado."""
        try:
            if tipo == "int":
                # Int64 (mayúscula) permite enteros con NaN
                return pd.to_numeric(serie, errors="coerce").astype("Int64")
            elif tipo == "float":
                return pd.to_numeric(serie, errors="coerce").astype(float)
            elif tipo == "str":
                return serie.astype(str).replace("nan", np.nan)
            else:
                return serie
        except Exception as e:
            logger.warning(
                f"  {nombre_col}: error al convertir a {tipo}: {e}"
            )
            return serie

    def _contar_nulos(self, df: pd.DataFrame) -> dict:
        """Cuenta nulos por columna."""
        return {col: df[col].isna().sum() for col in df.columns}

    def _log_metricas(
        self,
        clave: str,
        antes: dict,
        despues: dict,
        filas_final: int,
    ) -> None:
        """Registra el resumen de limpieza."""
        cols_afectadas = [
            col for col in antes
            if despues.get(col, 0) != antes.get(col, 0)
        ]
        logger.info(
            f"[{clave}] Limpieza completada: "
            f"{filas_final:,} filas · "
            f"{len(cols_afectadas)} columnas modificadas"
        )
        for col in cols_afectadas:
            delta = despues[col] - antes[col]
            pct   = despues[col] / filas_final * 100 if filas_final > 0 else 0
            logger.info(
                f"  {col:<20}: "
                f"{antes[col]} → {despues[col]} nulos "
                f"(+{delta}, {pct:.1f}%)"
            )
