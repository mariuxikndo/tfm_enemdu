"""
pipeline/saver.py
────────────────────────────────────────────────────────────────────
Módulo de persistencia de microdatos transformados en formato Parquet.

Responsabilidades:
  - Guardar cada DataFrame transformado como archivo .parquet
  - Generar un archivo schema.json con el diccionario de variables
  - Verificar que los archivos se escribieron correctamente

Uso:
  from pipeline.saver import Saver
  saver = Saver()
  saver.save_all(dfs_transformados)
"""

import json
import logging
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class Saver:
    """
    Persiste los DataFrames transformados en formato Parquet.

    Parámetros
    ----------
    ruta_settings : str
        Ruta al archivo config/settings.yaml
    """

    def __init__(self, ruta_settings: str = "config/settings.yaml"):
        self.settings = self._cargar_settings(ruta_settings)
        self.ruta_processed = Path(
            self.settings.get("rutas", {}).get("processed", "data/processed/")
        )
        self.ruta_processed.mkdir(parents=True, exist_ok=True)

    # ── Métodos públicos ─────────────────────────────────────────

    def save_all(self, dfs: dict[str, pd.DataFrame]) -> dict[str, Path]:
        """
        Guarda todos los DataFrames como archivos Parquet.

        Retorna
        -------
        dict con clave → ruta del archivo guardado
        """
        rutas_guardadas = {}
        for clave, df in dfs.items():
            ruta = self.save_one(df, clave)
            if ruta:
                rutas_guardadas[clave] = ruta

        self._guardar_schema(dfs)
        logger.info(
            f"[saver] {len(rutas_guardadas)} archivos guardados "
            f"en {self.ruta_processed}"
        )
        return rutas_guardadas

    def save_one(self, df: pd.DataFrame, clave: str) -> Path:
        """
        Guarda un único DataFrame como archivo Parquet.

        Parámetros
        ----------
        df    : DataFrame transformado
        clave : nombre del archivo destino (sin extensión)
        """
        nombre_archivo = f"{clave}.parquet"
        ruta_destino   = self.ruta_processed / nombre_archivo

        try:
            df.to_parquet(
                ruta_destino,
                engine="pyarrow",
                index=False,
                compression="snappy",   # buena relación velocidad/compresión
            )
            kb = ruta_destino.stat().st_size / 1024
            logger.info(
                f"  ✓ {nombre_archivo} guardado — "
                f"{len(df):,} filas · {kb:.1f} KB"
            )
            return ruta_destino
        except Exception as e:
            logger.error(f"  ✗ Error guardando {nombre_archivo}: {e}")
            return None

    def load_one(self, clave: str) -> pd.DataFrame:
        """
        Carga un archivo Parquet procesado.

        Parámetros
        ----------
        clave : "ambiental_ago" | "ambiental_oct" | "persona_ago"
        """
        ruta = self.ruta_processed / f"{clave}.parquet"
        if not ruta.exists():
            raise FileNotFoundError(
                f"No se encontró {ruta}. "
                "Ejecuta primero el pipeline con: make pipeline"
            )
        return pd.read_parquet(ruta, engine="pyarrow")

    def load_all(self) -> dict[str, pd.DataFrame]:
        """Carga todos los archivos Parquet disponibles."""
        dfs = {}
        for archivo in self.ruta_processed.glob("*.parquet"):
            clave = archivo.stem
            dfs[clave] = pd.read_parquet(archivo, engine="pyarrow")
            logger.info(
                f"  Cargado {archivo.name} — {len(dfs[clave]):,} filas"
            )
        return dfs

    # ── Métodos privados ─────────────────────────────────────────

    def _guardar_schema(self, dfs: dict[str, pd.DataFrame]) -> None:
        """
        Guarda un schema.json con el diccionario de variables
        de cada archivo procesado.
        """
        schema = {}
        for clave, df in dfs.items():
            schema[clave] = {
                "filas":    len(df),
                "columnas": len(df.columns),
                "variables": {
                    col: {
                        "tipo":   str(df[col].dtype),
                        "nulos":  int(df[col].isna().sum()),
                        "pct_nulos": round(df[col].isna().sum() / len(df) * 100, 2),
                    }
                    for col in df.columns
                }
            }

        ruta_schema = self.ruta_processed / "schema.json"
        with open(ruta_schema, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        logger.info(f"  schema.json guardado en {ruta_schema}")

    def _cargar_settings(self, ruta: str) -> dict:
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            return {}
        with open(ruta_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
