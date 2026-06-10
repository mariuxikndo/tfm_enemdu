"""
pipeline/ingester.py
────────────────────────────────────────────────────────────────────
Módulo de ingesta de microdatos MIAH-ENEMDU 2025.

Responsabilidades:
  - Leer los archivos ODS del INEC desde data/raw/
  - Validar que las columnas esperadas estén presentes
  - Registrar metadatos de cada carga (nº filas, columnas, periodo)
  - Retornar DataFrames listos para el módulo cleaner.py

Archivos que procesa:
  - enemdu_mod_ambiental_2025_08.ods  (energía + consumo)
  - enemdu_ambiental_2025_10.ods      (agua + residuos + conciencia)
  - enemdu_persona_2025_08.ods        (movilidad)

Uso:
  from pipeline.ingester import Ingester
  ingester = Ingester()
  dfs = ingester.ingest_all()
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


# ── Columnas mínimas requeridas por archivo ──────────────────────
COLUMNAS_REQUERIDAS = {
    "ambiental_ago": [
        "area", "prov", "cant", "fexp",
        "s101p71", "s101p72", "s101p73", "s101p74", "s101p75",
        "s101p76", "s101p77",
        "s91p7", "s91p8a", "s91p8b", "s91p8c", "s91p8d",
    ],
    "ambiental_oct": [
        "area", "fexp",
        "s101p11", "s101p12a", "s101p12b", "s101p12c", "s101p12d", "s101p12e",
        "s101p2a", "s101p2b", "s101p2c", "s101p2d", "s101p2e", "s101p2f",
        "s101p61", "s101p62", "s101p63", "s101p64",
        "s101p65", "s101p66", "s101p67", "s101p68",
        "s91p91", "s91p92", "s91p93", "s91p94", "s91p95", "s91p96",
        "s91p10",
        "s91p111", "s91p112", "s91p113", "s91p114", "s91p115",
        "s91p121", "s91p122", "s91p123", "s91p124", "s91p125", "s91p126",
        "s91p131", "s91p132", "s91p133",
    ],
    "persona_ago": [
        "area", "fexp",
        "s5p2", "s5p3", "s5p4",
        "s5p6a", "s5p6b", "s5p7a", "s5p7b",
        "p02", "p03",
    ],
}


@dataclass
class ResultadoIngesta:
    """Resultado de la ingesta de un archivo."""
    clave:       str
    periodo:     str
    archivo:     str
    filas:       int
    columnas:    int
    columnas_ok: bool
    columnas_faltantes: list = field(default_factory=list)
    df:          Optional[pd.DataFrame] = field(default=None, repr=False)


class Ingester:
    """
    Lee los tres archivos ODS del MIAH-ENEMDU y valida su esquema.

    Parámetros
    ----------
    ruta_settings : str
        Ruta al archivo config/settings.yaml. Por defecto busca
        relativo a la raíz del proyecto.
    """

    def __init__(self, ruta_settings: str = "config/settings.yaml"):
        self.settings = self._cargar_settings(ruta_settings)
        self.ruta_raw = Path(self.settings["rutas"]["raw"])

    # ── Métodos públicos ─────────────────────────────────────────

    def ingest_all(self) -> dict[str, pd.DataFrame]:
        """
        Carga los tres archivos ODS y retorna un diccionario con los
        DataFrames resultantes.

        Retorna
        -------
        dict con claves: "ambiental_ago", "ambiental_oct", "persona_ago"
        """
        resultados = {}
        for clave, cfg in self.settings["archivos"].items():
            resultado = self._ingestar_archivo(clave, cfg)
            if resultado.df is not None:
                resultados[clave] = resultado.df
            self._log_resultado(resultado)

        logger.info(f"Ingesta completada: {len(resultados)}/3 archivos cargados.")
        return resultados

    def ingest_one(self, clave: str) -> pd.DataFrame:
        """
        Carga un único archivo por su clave de configuración.

        Parámetros
        ----------
        clave : str
            "ambiental_ago" | "ambiental_oct" | "persona_ago"
        """
        if clave not in self.settings["archivos"]:
            raise ValueError(
                f"Clave '{clave}' no encontrada en settings.yaml. "
                f"Claves válidas: {list(self.settings['archivos'].keys())}"
            )
        cfg = self.settings["archivos"][clave]
        resultado = self._ingestar_archivo(clave, cfg)
        self._log_resultado(resultado)
        if resultado.df is None:
            raise FileNotFoundError(
                f"No se pudo cargar el archivo '{cfg['nombre']}'. "
                f"Verifica que esté en {self.ruta_raw}"
            )
        return resultado.df

    # ── Métodos privados ─────────────────────────────────────────

    def _cargar_settings(self, ruta: str) -> dict:
        """Carga y retorna el archivo settings.yaml."""
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            raise FileNotFoundError(
                f"No se encontró settings.yaml en '{ruta}'. "
                "Ejecuta el proyecto desde la raíz: cd enemdu-ambiental"
            )
        with open(ruta_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _ingestar_archivo(self, clave: str, cfg: dict) -> ResultadoIngesta:
        """
        Lee un archivo ODS y construye un ResultadoIngesta.
        """
        ruta_archivo = self.ruta_raw / cfg["nombre"]
        periodo = cfg["periodo"]
        hoja = cfg.get("hoja", 0)

        # ── Verificar que el archivo existe ──────────────────────
        if not ruta_archivo.exists():
            logger.error(
                f"[{clave}] Archivo no encontrado: {ruta_archivo}\n"
                f"  → Descárgalo del INEC y colócalo en {self.ruta_raw}"
            )
            return ResultadoIngesta(
                clave=clave, periodo=periodo,
                archivo=str(ruta_archivo),
                filas=0, columnas=0,
                columnas_ok=False, df=None,
            )

        # ── Leer ODS ─────────────────────────────────────────────
        logger.info(f"[{clave}] Leyendo {ruta_archivo.name} ...")
        try:
            df = pd.read_excel(
                ruta_archivo,
                sheet_name=hoja,
                engine="odf",   # requiere: pip install odfpy
            )
        except Exception as e:
            logger.error(f"[{clave}] Error al leer {ruta_archivo.name}: {e}")
            return ResultadoIngesta(
                clave=clave, periodo=periodo,
                archivo=str(ruta_archivo),
                filas=0, columnas=0,
                columnas_ok=False, df=None,
            )

        # ── Estandarizar nombres de columnas a minúsculas ─────────
        df.columns = [str(c).strip().lower() for c in df.columns]

        # ── Agregar columna de periodo ─────────────────────────────
        df["periodo"] = periodo
        df["archivo_origen"] = cfg["nombre"]

        # ── Validar columnas requeridas ────────────────────────────
        requeridas = COLUMNAS_REQUERIDAS.get(clave, [])
        faltantes = [c for c in requeridas if c not in df.columns]
        columnas_ok = len(faltantes) == 0

        if not columnas_ok:
            logger.warning(
                f"[{clave}] Columnas requeridas faltantes ({len(faltantes)}): "
                f"{faltantes}\n"
                "  → Verifica que el archivo es el correcto y no está truncado."
            )

        return ResultadoIngesta(
            clave=clave,
            periodo=periodo,
            archivo=str(ruta_archivo),
            filas=len(df),
            columnas=len(df.columns),
            columnas_ok=columnas_ok,
            columnas_faltantes=faltantes,
            df=df,
        )

    def _log_resultado(self, r: ResultadoIngesta) -> None:
        """Registra un resumen del resultado de ingesta."""
        estado = "✓" if r.columnas_ok and r.filas > 0 else "✗"
        logger.info(
            f"  {estado} [{r.clave}] {Path(r.archivo).name} | "
            f"{r.filas:,} filas · {r.columnas} columnas · periodo {r.periodo}"
        )
        if r.columnas_faltantes:
            logger.warning(
                f"    Faltantes: {r.columnas_faltantes}"
            )

    # ── Utilidades de diagnóstico ────────────────────────────────

    def diagnostico(self) -> None:
        """
        Imprime un diagnóstico rápido de los archivos disponibles
        sin cargarlos completamente.
        """
        print("\n" + "═" * 60)
        print("  Diagnóstico de archivos MIAH-ENEMDU")
        print("═" * 60)
        for clave, cfg in self.settings["archivos"].items():
            ruta = self.ruta_raw / cfg["nombre"]
            existe = "✓" if ruta.exists() else "✗"
            tamaño = ""
            if ruta.exists():
                kb = ruta.stat().st_size / 1024
                tamaño = f"({kb:.0f} KB)"
            print(f"  {existe}  {clave:<15} {cfg['nombre']} {tamaño}")
        print("═" * 60 + "\n")
