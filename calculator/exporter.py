"""
calculator/exporter.py
────────────────────────────────────────────────────────────────────
Exporta los resultados del motor de cálculo a la capa de servicio.

Destinos:
  - SQLite (indicators.db): para la webapp Streamlit
  - Parquet: para análisis externos o notebooks

Tablas en SQLite:
  - indicadores_nacionales   : resultados sin desagregación
  - indicadores_por_area     : desagregados por área (urbano/rural)
  - indicadores_por_provincia: desagregados por provincia
  - metadata                 : fecha de cálculo y parámetros

Uso:
  from calculator.engine   import Engine
  from calculator.exporter import Exporter

  engine   = Engine()
  exporter = Exporter()

  resultados = engine.calcular_todos()
  exporter.exportar(resultados, nivel="nacional")
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class Exporter:
    """
    Exporta los resultados del motor de cálculo a SQLite y Parquet.

    Parámetros
    ----------
    ruta_settings : str
        Ruta al archivo config/settings.yaml
    """

    def __init__(self, ruta_settings: str = "config/settings.yaml"):
        self.settings   = self._cargar_settings(ruta_settings)
        self.ruta_db    = Path(
            self.settings.get("rutas", {}).get("db", "data/outputs/indicators.db")
        )
        self.ruta_out   = Path(
            self.settings.get("rutas", {}).get("outputs", "data/outputs/")
        )
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_out.mkdir(parents=True, exist_ok=True)

    # ── API pública ───────────────────────────────────────────────

    def exportar_todo(self, engine) -> dict[str, Path]:
        """
        Calcula y exporta todos los indicadores en tres niveles:
        nacional, por área y por provincia.

        Parámetros
        ----------
        engine : instancia de calculator.engine.Engine

        Retorna
        -------
        dict con rutas de los archivos generados
        """
        from calculator.filters import Filtros

        logger.info("[Exporter] Iniciando exportación completa...")
        rutas: dict[str, Path] = {}

        # ── Nacional ──────────────────────────────────────────────
        logger.info("  Calculando nivel nacional...")
        df_nac = engine.calcular_todos(Filtros(), desagregacion=None)
        if not df_nac.empty:
            rutas["nacional"] = self.exportar(
                df_nac, tabla="indicadores_nacionales", nivel="nacional"
            )

        # ── Por área ──────────────────────────────────────────────
        logger.info("  Calculando por área (urbano/rural)...")
        df_area = engine.calcular_todos(Filtros(), desagregacion="area")
        if not df_area.empty:
            rutas["area"] = self.exportar(
                df_area, tabla="indicadores_por_area", nivel="area"
            )

        # ── Por provincia ─────────────────────────────────────────
        logger.info("  Calculando por provincia...")
        df_prov = engine.calcular_todos(Filtros(), desagregacion="prov")
        if not df_prov.empty:
            rutas["provincia"] = self.exportar(
                df_prov, tabla="indicadores_por_provincia", nivel="provincia"
            )

        # ── Metadata ──────────────────────────────────────────────
        self._guardar_metadata(
            n_indicadores=len(engine.catalogo),
            niveles=list(rutas.keys()),
        )

        logger.info(
            f"[Exporter] Exportación completada — "
            f"{len(rutas)} niveles guardados en {self.ruta_db}"
        )
        return rutas

    def exportar(
        self,
        df:     pd.DataFrame,
        tabla:  str,
        nivel:  str = "",
        modo:   str = "replace",
    ) -> Path:
        """
        Exporta un DataFrame de resultados a SQLite y Parquet.

        Parámetros
        ----------
        df    : DataFrame de resultados del engine
        tabla : nombre de la tabla SQLite destino
        nivel : "nacional" | "area" | "provincia" (para el nombre del Parquet)
        modo  : "replace" | "append" para la tabla SQLite

        Retorna
        -------
        Path del archivo Parquet generado
        """
        if df.empty:
            logger.warning(f"[Exporter] DataFrame vacío para tabla '{tabla}' — omitido")
            return None

        # ── Guardar en SQLite ─────────────────────────────────────
        try:
            with sqlite3.connect(self.ruta_db) as conn:
                df.to_sql(tabla, conn, if_exists=modo, index=False)
            n_filas = self._contar_filas_sqlite(tabla)
            logger.info(
                f"  ✓ SQLite [{tabla}]: {len(df):,} filas escritas "
                f"(total en tabla: {n_filas:,})"
            )
        except Exception as e:
            logger.error(f"  ✗ Error escribiendo SQLite [{tabla}]: {e}")

        # ── Guardar en Parquet ────────────────────────────────────
        nombre_parquet = f"indicadores_{nivel}.parquet" if nivel else "indicadores.parquet"
        ruta_parquet   = self.ruta_out / nombre_parquet
        try:
            df.to_parquet(ruta_parquet, engine="pyarrow", index=False)
            kb = ruta_parquet.stat().st_size / 1024
            logger.info(f"  ✓ Parquet [{nombre_parquet}]: {kb:.1f} KB")
        except Exception as e:
            logger.error(f"  ✗ Error escribiendo Parquet [{nombre_parquet}]: {e}")

        return ruta_parquet

    # ── Lectura desde SQLite (para la webapp) ─────────────────────

    def cargar_nacionales(self) -> pd.DataFrame:
        """Carga la tabla de indicadores nacionales desde SQLite."""
        return self._leer_sqlite("indicadores_nacionales")

    def cargar_por_area(self) -> pd.DataFrame:
        """Carga la tabla de indicadores por área desde SQLite."""
        return self._leer_sqlite("indicadores_por_area")

    def cargar_por_provincia(self) -> pd.DataFrame:
        """Carga la tabla de indicadores por provincia desde SQLite."""
        return self._leer_sqlite("indicadores_por_provincia")

    def cargar_dimension(
        self,
        dimension: str,
        nivel:     str = "nacional",
    ) -> pd.DataFrame:
        """
        Carga indicadores de una dimensión desde SQLite.

        Parámetros
        ----------
        dimension : "agua" | "residuos" | "energia" | "movilidad" | "conciencia"
        nivel     : "nacional" | "area" | "provincia"
        """
        tabla_map = {
            "nacional":   "indicadores_nacionales",
            "area":       "indicadores_por_area",
            "provincia":  "indicadores_por_provincia",
        }
        tabla = tabla_map.get(nivel, "indicadores_nacionales")
        df = self._leer_sqlite(tabla)
        if df.empty or "dimension" not in df.columns:
            return df
        return df[df["dimension"] == dimension].copy()

    def cargar_indicador(
        self,
        indicador_id: str,
        nivel:        str = "nacional",
    ) -> pd.DataFrame:
        """Carga un indicador específico desde SQLite."""
        tabla_map = {
            "nacional":  "indicadores_nacionales",
            "area":      "indicadores_por_area",
            "provincia": "indicadores_por_provincia",
        }
        tabla = tabla_map.get(nivel, "indicadores_nacionales")
        df = self._leer_sqlite(tabla)
        if df.empty or "indicador_id" not in df.columns:
            return df
        return df[df["indicador_id"] == indicador_id].copy()

    def tablas_disponibles(self) -> list[str]:
        """Lista las tablas disponibles en el SQLite."""
        if not self.ruta_db.exists():
            return []
        try:
            with sqlite3.connect(self.ruta_db) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    # ── Métodos privados ─────────────────────────────────────────

    def _leer_sqlite(self, tabla: str) -> pd.DataFrame:
        """Lee una tabla de SQLite y retorna un DataFrame."""
        if not self.ruta_db.exists():
            logger.error(
                f"[Exporter] Base de datos no encontrada: {self.ruta_db}\n"
                "  → Ejecuta: python calculator/run_calculator.py"
            )
            return pd.DataFrame()
        try:
            with sqlite3.connect(self.ruta_db) as conn:
                tablas = pd.read_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'", conn
                )["name"].tolist()
                if tabla not in tablas:
                    logger.warning(
                        f"[Exporter] Tabla '{tabla}' no existe en {self.ruta_db}"
                    )
                    return pd.DataFrame()
                return pd.read_sql(f"SELECT * FROM {tabla}", conn)
        except Exception as e:
            logger.error(f"[Exporter] Error leyendo '{tabla}': {e}")
            return pd.DataFrame()

    def _contar_filas_sqlite(self, tabla: str) -> int:
        try:
            with sqlite3.connect(self.ruta_db) as conn:
                result = conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()
                return result[0] if result else 0
        except Exception:
            return 0

    def _guardar_metadata(self, n_indicadores: int, niveles: list) -> None:
        """Guarda metadatos de la ejecución en SQLite."""
        df_meta = pd.DataFrame([{
            "fecha_calculo":   datetime.now().isoformat(),
            "n_indicadores":   n_indicadores,
            "niveles":         ", ".join(niveles),
            "fuente":          "MIAH-ENEMDU 2025",
            "version":         "1.0",
        }])
        try:
            with sqlite3.connect(self.ruta_db) as conn:
                df_meta.to_sql("metadata", conn, if_exists="append", index=False)
        except Exception as e:
            logger.warning(f"[Exporter] No se pudo guardar metadata: {e}")

    def _cargar_settings(self, ruta: str) -> dict:
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            return {}
        with open(ruta_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
