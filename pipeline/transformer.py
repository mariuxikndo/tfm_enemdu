"""
pipeline/transformer.py
────────────────────────────────────────────────────────────────────
Módulo de transformación de microdatos MIAH-ENEMDU 2025.

Responsabilidades:
  - Estandarizar nombres de variables geográficas entre archivos
  - Crear variables derivadas necesarias para los indicadores
  - Calcular tiempo y distancia de traslado en unidades únicas
  - Agregar columnas de clasificación (p.ej. tipo de transporte)
  - Etiquetar área y provincia con nombres legibles

Uso:
  from pipeline.transformer import Transformer
  transformer = Transformer()
  dfs_transformados = transformer.transform_all(dfs_limpios)
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class Transformer:
    """
    Transforma y enriquece los DataFrames limpios del MIAH-ENEMDU.

    Parámetros
    ----------
    ruta_settings : str
        Ruta al archivo config/settings.yaml
    """

    def __init__(self, ruta_settings: str = "config/settings.yaml"):
        self.settings = self._cargar_settings(ruta_settings)

    # ── Métodos públicos ─────────────────────────────────────────

    def transform_all(
        self, dfs: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
        """
        Transforma todos los DataFrames del diccionario.
        """
        dfs_t = {}
        for clave, df in dfs.items():
            logger.info(f"[transformer] Transformando {clave}...")
            if clave == "ambiental_ago":
                dfs_t[clave] = self._transform_ambiental_ago(df)
            elif clave == "ambiental_oct":
                dfs_t[clave] = self._transform_ambiental_oct(df)
            elif clave == "persona_ago":
                dfs_t[clave] = self._transform_persona_ago(df)
            else:
                dfs_t[clave] = df
        return dfs_t

    # ── Transformaciones por archivo ─────────────────────────────

    def _transform_ambiental_ago(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transformaciones para ambiental_2025_08.ods
        Dimensiones: Energía + Consumo responsable
        """
        df = df.copy()

        # Estandarizar nombre de provincia (ya se llama "prov" en este archivo)
        df = self._etiquetar_area(df)
        df = self._etiquetar_provincia(df, col_prov="prov")

        # ── Variables derivadas: Energía ──────────────────────────
        # Escala REAL: 1=Sí, 2=No, 3=No aplica (formulario AGO-2025)
        # Valor positivo (buena práctica) = 1=Sí para casi todos,
        # EXCEPTO s101p73 donde la buena práctica es 2=No
        # (introducir alimentos calientes ES una mala práctica)
        VARS_POSITIVO_SI = [
            "s101p71", "s101p72", "s101p74", "s101p75",
        ]
        VARS_POSITIVO_NO = [
            "s101p73",  # NO introducir alimentos calientes = buena práctica
        ]

        for var in VARS_POSITIVO_SI:
            if var in df.columns:
                df[var + "_positivo"] = df[var].apply(
                    lambda x: 1 if pd.notna(x) and int(x) == 1 else
                              (0 if pd.notna(x) and int(x) in [2, 3] else np.nan)
                ).astype("Int64")

        for var in VARS_POSITIVO_NO:
            if var in df.columns:
                df[var + "_positivo"] = df[var].apply(
                    lambda x: 1 if pd.notna(x) and int(x) == 2 else
                              (0 if pd.notna(x) and int(x) in [1, 3] else np.nan)
                ).astype("Int64")

        # Índice de eficiencia energética (0-7):
        # suma de hábitos positivos + tiene electrodomésticos ahorradores + paneles
        cols_energia = [
            "s101p71_positivo", "s101p72_positivo", "s101p73_positivo",
            "s101p74_positivo", "s101p75_positivo",
        ]
        # s101p76 y s101p77: 1=Sí → positivo
        for var in ["s101p76", "s101p77"]:
            if var in df.columns:
                nuevo = var + "_positivo"
                df[nuevo] = df[var].apply(
                    lambda x: 1 if pd.notna(x) and int(x) == 1 else
                              (0 if pd.notna(x) else np.nan)
                ).astype("Int64")
                cols_energia.append(nuevo)

        cols_exist = [c for c in cols_energia if c in df.columns]
        if cols_exist:
            df["idx_energia"] = df[cols_exist].sum(axis=1, skipna=False)

        logger.info(
            f"  [ambiental_ago] Variables derivadas creadas: "
            f"{[c for c in df.columns if '_positivo' in c or c == 'idx_energia']}"
        )
        return df

    def _transform_ambiental_oct(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transformaciones para ambiental_2025_10.ods
        Dimensiones: Agua + Residuos + Conciencia ambiental
        """
        df = df.copy()
        df = self._etiquetar_area(df)

        # ── Variables derivadas: Agua ─────────────────────────────
        # Escala REAL: 1=Sí, 2=No, 3=No aplica (formulario OCT-2025)
        # Valor positivo (buena práctica) = 1=Sí en todas las variables
        vars_agua_positivo_si = [
            "s101p61", "s101p62", "s101p63",
            "s101p64", "s101p65", "s101p66", "s101p67", "s101p68",
        ]
        for var in vars_agua_positivo_si:
            if var in df.columns:
                df[var + "_positivo"] = df[var].apply(
                    lambda x: 1 if pd.notna(x) and int(x) == 1 else
                              (0 if pd.notna(x) and int(x) in [2, 3] else np.nan)
                ).astype("Int64")

        # Índice de prácticas de ahorro de agua (0-8)
        cols_agua = [c for c in df.columns
                     if c.startswith("s101p6") and c.endswith("_positivo")]
        if cols_agua:
            df["idx_agua"] = df[cols_agua].sum(axis=1, skipna=False)

        # ── Variables derivadas: Residuos ─────────────────────────
        # Clasificó al menos un tipo de residuo inorgánico
        vars_inorg = ["s101p12a", "s101p12b", "s101p12c", "s101p12d", "s101p12e"]
        cols_inorg = [c for c in vars_inorg if c in df.columns]
        if cols_inorg:
            df["clasifica_inorganico"] = df[cols_inorg].apply(
                lambda row: 1 if (row == 1).any() else
                            (0 if row.notna().all() else np.nan),
                axis=1
            ).astype("Int64")

        # ── Variables derivadas: Conciencia ambiental ─────────────
        # Percibe al menos un problema ambiental en su barrio
        vars_problemas = [
            "s91p91", "s91p92", "s91p93",
            "s91p94", "s91p95", "s91p96",
        ]
        cols_prob = [c for c in vars_problemas if c in df.columns]
        if cols_prob:
            df["percibe_problema_ambiental"] = df[cols_prob].apply(
                lambda row: 1 if (row == 1).any() else
                            (0 if row.notna().all() else np.nan),
                axis=1
            ).astype("Int64")

        # Participó en al menos una actividad ambiental
        vars_participa = [
            "s91p111", "s91p112", "s91p113", "s91p114", "s91p115",
        ]
        cols_part = [c for c in vars_participa if c in df.columns]
        if cols_part:
            df["participo_actividad_ambiental"] = df[cols_part].apply(
                lambda row: 1 if (row == 1).any() else
                            (0 if row.notna().all() else np.nan),
                axis=1
            ).astype("Int64")

        # Índice de conciencia ambiental (ICA):
        # Escala REAL s91p10: 1=Nada, 2=Poco, 3=Medianamente, 4=Mucho, 5=Excesivamente
        # "Preocupación alta" = MUCHO (4) o EXCESIVAMENTE (5)
        if "s91p10" in df.columns:
            df["preocupacion_alta"] = df["s91p10"].apply(
                lambda x: 1 if pd.notna(x) and int(x) in [4, 5] else
                          (0 if pd.notna(x) else np.nan)
            ).astype("Int64")

        cols_ica = [
            c for c in ["preocupacion_alta",
                        "percibe_problema_ambiental",
                        "participo_actividad_ambiental"]
            if c in df.columns
        ]
        if cols_ica:
            df["idx_conciencia"] = df[cols_ica].sum(axis=1, skipna=False)

        return df

    def _transform_persona_ago(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transformaciones para persona_2025_08.ods
        Dimensión: Movilidad
        """
        df = df.copy()

        # ── 1. Estandarizar nombre de provincia ───────────────────
        # En este archivo se llama "prov_dirad"; estandarizar a "prov"
        if "prov_dirad" in df.columns and "prov" not in df.columns:
            df = df.rename(columns={"prov_dirad": "prov"})
            logger.info("  [persona_ago] prov_dirad → prov (estandarizado)")

        df = self._etiquetar_area(df)
        df = self._etiquetar_provincia(df, col_prov="prov")

        # ── 2. Tiempo total de traslado en minutos ────────────────
        if "s5p6a" in df.columns and "s5p6b" in df.columns:
            horas   = pd.to_numeric(df["s5p6a"], errors="coerce")
            minutos = pd.to_numeric(df["s5p6b"], errors="coerce")
            df["tiempo_traslado_min"] = horas * 60 + minutos
            # Filtrar valores imposibles (> 8 horas = 480 min)
            df.loc[df["tiempo_traslado_min"] > 480, "tiempo_traslado_min"] = np.nan
            logger.info("  [persona_ago] tiempo_traslado_min calculado")

        # ── 3. Distancia total en kilómetros ──────────────────────
        if "s5p7a" in df.columns and "s5p7b" in df.columns:
            km     = pd.to_numeric(df["s5p7a"], errors="coerce")
            metros = pd.to_numeric(df["s5p7b"], errors="coerce")
            df["distancia_km"] = km + (metros / 1000)
            # Filtrar distancias imposibles (> 200 km)
            df.loc[df["distancia_km"] > 200, "distancia_km"] = np.nan
            logger.info("  [persona_ago] distancia_km calculado")

        # ── 4. Clasificación del tipo de transporte ───────────────
        # Códigos REALES según formulario AGO-2025, Sección 5, pregunta 2:
        # 1=Autobús
        # 2=Taxi o servicio por aplicación
        # 3=Mototaxi/tricimoto
        # 4=Metrovía/Tranvía/Trolebús
        # 5=Metro
        # 6=Automóvil
        # 7=Motocicleta privada
        # 8=Bicicleta
        # 9=Caminar
        # 10=Vehículo eléctrico
        # 11=Otro (especifique)
        # 99=No aplica → ya excluido por cleaning_rules
        TRANSP_PUBLICO_COLECTIVO = [1, 4, 5]   # bus, metrovía/trolebús/tranvía, metro
        TRANSP_CONTRATACION      = [2, 3]        # taxi/app, mototaxi
        TRANSP_PRIVADO_MOT       = [6, 7]        # automóvil, moto privada
        TRANSP_NO_MOTORIZADO     = [8, 9]        # bicicleta, caminar
        TRANSP_ELECTRICO         = [10]          # vehículo eléctrico
        OTRO                     = [11]

        if "s5p2" in df.columns:
            s5p2_num = pd.to_numeric(df["s5p2"], errors="coerce")

            df["tipo_transporte"] = np.where(
                s5p2_num.isin(TRANSP_PUBLICO_COLECTIVO), "publico_colectivo",
                np.where(
                    s5p2_num.isin(TRANSP_CONTRATACION), "contratacion",
                    np.where(
                        s5p2_num.isin(TRANSP_PRIVADO_MOT), "privado_motorizado",
                        np.where(
                            s5p2_num.isin(TRANSP_NO_MOTORIZADO), "no_motorizado",
                            np.where(
                                s5p2_num.isin(TRANSP_ELECTRICO), "electrico",
                                np.where(s5p2_num.notna(), "otro", None)
                            )
                        )
                    )
                )
            )

            # Movilidad sostenible = público colectivo + no motorizado
            SOSTENIBLE = TRANSP_PUBLICO_COLECTIVO + TRANSP_NO_MOTORIZADO
            NO_APLICA_VALS = []  # 99 ya fue limpiado a NaN

            df["usa_movilidad_sostenible"] = s5p2_num.apply(
                lambda x: 1 if pd.notna(x) and int(x) in SOSTENIBLE
                          else (0 if pd.notna(x) else np.nan)
            ).astype("Int64")

            # Usa transporte público colectivo (sin taxi ni mototaxi)
            df["usa_transporte_publico"] = s5p2_num.apply(
                lambda x: 1 if pd.notna(x) and int(x) in TRANSP_PUBLICO_COLECTIVO
                          else (0 if pd.notna(x) else np.nan)
            ).astype("Int64")

            logger.info(
                "  [persona_ago] tipo_transporte y "
                "usa_transporte_sostenible calculados"
            )

        return df

    # ── Utilidades compartidas ───────────────────────────────────

    def _etiquetar_area(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade columna area_nombre (Urbano/Rural)."""
        etiquetas = self.settings.get("etiquetas_area", {1: "Urbano", 2: "Rural"})
        if "area" in df.columns:
            df["area_nombre"] = (
                pd.to_numeric(df["area"], errors="coerce")
                .map(etiquetas)
            )
        return df

    def _etiquetar_provincia(
        self, df: pd.DataFrame, col_prov: str = "prov"
    ) -> pd.DataFrame:
        """Añade columna prov_nombre con el nombre de la provincia."""
        etiquetas = self.settings.get("etiquetas_provincia", {})
        # YAML puede devolver keys como strings
        etiquetas_int = {int(k): v for k, v in etiquetas.items()}
        if col_prov in df.columns:
            df["prov_nombre"] = (
                pd.to_numeric(df[col_prov], errors="coerce")
                .map(etiquetas_int)
            )
        return df

    def _cargar_settings(self, ruta: str) -> dict:
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            return {}
        with open(ruta_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
