"""
tests/test_pipeline.py
────────────────────────────────────────────────────────────────────
Tests del pipeline ETL: ingesta, limpieza y transformación.

Batería TC-01 a TC-09 del plan de evaluación funcional.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.cleaner     import Cleaner
from pipeline.transformer import Transformer


# ══════════════════════════════════════════════════════════════════
#  TC-01: Limpieza — valores nulos por tipo_nulo
# ══════════════════════════════════════════════════════════════════

class TestCleaner:

    def test_TC01_valores_nulo_reemplazados_por_nan(self):
        """TC-01: Los valores en tipo_nulo deben convertirse a NaN."""
        cleaner = Cleaner()
        df = pd.DataFrame({
            "area": [1, 2, 99, 0, 1],   # 99 y 0 son tipo_nulo en settings
            "fexp": [10.0] * 5,
        })
        df_limpio = cleaner.clean_one(df)
        # area=99 y area=0 deben ser NaN
        assert df_limpio["area"].isna().sum() == 2, \
            "TC-01 FALLO: Los valores 99 y 0 de 'area' debían convertirse a NaN"

    def test_TC02_fexp_invalido_elimina_fila(self):
        """TC-02: Filas con fexp=0 o negativo deben eliminarse."""
        cleaner = Cleaner()
        df = pd.DataFrame({
            "area": [1, 1, 2, 1, 2],
            "fexp": [10.0, 0.0, -1.0, 15.0, 8.0],
        })
        df_limpio = cleaner.clean_one(df)
        assert len(df_limpio) == 3, \
            "TC-02 FALLO: Deben quedar solo 3 filas (fexp=0 y fexp=-1 eliminadas)"
        assert (df_limpio["fexp"] > 0).all(), \
            "TC-02 FALLO: Todas las filas restantes deben tener fexp > 0"

    def test_TC03_valores_fuera_de_rango_nan(self):
        """TC-03: Valores fuera del rango permitido se convierten a NaN."""
        cleaner = Cleaner()
        df = pd.DataFrame({
            "s101p61": [1, 2, 3, 5, 1],   # 5 está fuera de [1,2,3]
            "fexp": [10.0] * 5,
        })
        df_limpio = cleaner.clean_one(df)
        assert df_limpio["s101p61"].isna().sum() == 1, \
            "TC-03 FALLO: El valor 5 en s101p61 debía convertirse a NaN"

    def test_TC04_tipos_de_dato_correctos(self):
        """TC-04: Las variables se convierten al tipo de dato correcto."""
        cleaner = Cleaner()
        df = pd.DataFrame({
            "area": ["1", "2", "1"],          # string → Int64
            "fexp": ["10.5", "8.0", "12.3"],  # string → float
        })
        df_limpio = cleaner.clean_one(df)
        assert df_limpio["area"].dtype.name in ["Int64", "int64", "int32"], \
            f"TC-04 FALLO: area debe ser Int64, obtenido {df_limpio['area'].dtype}"
        assert df_limpio["fexp"].dtype in [float, np.float64], \
            f"TC-04 FALLO: fexp debe ser float, obtenido {df_limpio['fexp'].dtype}"

    def test_TC05_escala_energia_binaria(self):
        """TC-05: Variables de energía aceptan solo 1, 2, 3 (no 4 o más)."""
        cleaner = Cleaner()
        df = pd.DataFrame({
            "s101p71": [1, 2, 3, 4, 1],  # 4 fuera de rango
            "fexp": [10.0] * 5,
        })
        df_limpio = cleaner.clean_one(df)
        valores_validos = df_limpio["s101p71"].dropna().unique()
        assert 4 not in valores_validos, \
            "TC-05 FALLO: El valor 4 en s101p71 debía ser eliminado (solo 1, 2, 3 válidos)"


# ══════════════════════════════════════════════════════════════════
#  TC-06 a TC-09: Transformación
# ══════════════════════════════════════════════════════════════════

class TestTransformer:

    def test_TC06_estandariza_nombre_provincia(self):
        """TC-06: prov_dirad en persona_ago se renombra a prov."""
        transformer = Transformer()
        df = pd.DataFrame({
            "area": [1, 2],
            "prov_dirad": [17, 9],
            "fexp": [10.0, 10.0],
            "s5p2": [1, 6],
            "s5p6a": [0, 1],
            "s5p6b": [30, 20],
            "s5p7a": [2.0, 5.0],
            "s5p7b": [500, 200],
        })
        df_t = transformer._transform_persona_ago(df)
        assert "prov" in df_t.columns, \
            "TC-06 FALLO: prov_dirad debía renombrarse a prov"
        assert "prov_dirad" not in df_t.columns, \
            "TC-06 FALLO: prov_dirad no debería existir después de la transformación"

    def test_TC07_tiempo_traslado_minutos(self):
        """TC-07: tiempo_traslado_min = horas*60 + minutos."""
        transformer = Transformer()
        df = pd.DataFrame({
            "area": [1, 1, 1],
            "prov_dirad": [17, 17, 17],
            "fexp": [10.0, 10.0, 10.0],
            "s5p2": [1, 4, 6],
            "s5p6a": [1, 0, 2],     # horas
            "s5p6b": [30, 45, 15],  # minutos
            "s5p7a": [5.0, 3.0, 12.0],
            "s5p7b": [0, 500, 0],
        })
        df_t = transformer._transform_persona_ago(df)
        assert "tiempo_traslado_min" in df_t.columns, \
            "TC-07 FALLO: tiempo_traslado_min no fue creado"
        esperados = [90.0, 45.0, 135.0]
        for i, esp in enumerate(esperados):
            assert df_t["tiempo_traslado_min"].iloc[i] == esp, \
                f"TC-07 FALLO fila {i}: esperado {esp} min, obtenido {df_t['tiempo_traslado_min'].iloc[i]}"

    def test_TC08_variable_inversa_energia(self):
        """TC-08: s101p73 (alimentos calientes): valor positivo = 2 (No)."""
        transformer = Transformer()
        df = pd.DataFrame({
            "area": [1, 1, 2],
            "prov": [17, 17, 9],
            "fexp": [10.0, 10.0, 10.0],
            "s101p71": [1, 1, 1],
            "s101p72": [1, 1, 1],
            "s101p73": [1, 2, 2],  # 1=introduce alimentos calientes (MALA práctica)
            "s101p74": [1, 1, 1],
            "s101p75": [1, 1, 1],
            "s101p76": [1, 1, 1],
            "s101p77": [2, 2, 2],
            "s91p7": [1, 1, 2],
            "s91p8a": [1, 1, 1],
            "s91p8b": [1, 1, 1],
            "s91p8c": [1, 1, 1],
            "s91p8d": [1, 1, 1],
            "ciudad": ["Quito", "Quito", "Guayaquil"],
        })
        df_t = transformer._transform_ambiental_ago(df)
        # Fila 0: s101p73=1 → positivo=0 (mala práctica)
        # Filas 1 y 2: s101p73=2 → positivo=1 (buena práctica)
        assert df_t["s101p73_positivo"].iloc[0] == 0, \
            "TC-08 FALLO: s101p73=1 debía resultar en positivo=0"
        assert df_t["s101p73_positivo"].iloc[1] == 1, \
            "TC-08 FALLO: s101p73=2 debía resultar en positivo=1"

    def test_TC09_clasificacion_transporte(self):
        """TC-09: Clasificación correcta de s5p2 según formulario AGO-2025."""
        transformer = Transformer()
        df = pd.DataFrame({
            "area": [1]*11,
            "prov_dirad": [17]*11,
            "fexp": [10.0]*11,
            "s5p2": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "s5p6a": [0]*11, "s5p6b": [30]*11,
            "s5p7a": [2.0]*11, "s5p7b": [0]*11,
        })
        df_t = transformer._transform_persona_ago(df)

        # Esperado según formulario AGO-2025
        esperado = {
            1:  "publico_colectivo",   # autobús
            2:  "contratacion",        # taxi/app
            3:  "contratacion",        # mototaxi
            4:  "publico_colectivo",   # metrovía/tranvía/trolebús
            5:  "publico_colectivo",   # metro
            6:  "privado_motorizado",  # automóvil
            7:  "privado_motorizado",  # moto privada
            8:  "no_motorizado",       # bicicleta
            9:  "no_motorizado",       # caminar
            10: "electrico",           # vehículo eléctrico
            11: "otro",
        }
        for s5p2_val, tipo_esp in esperado.items():
            fila = df_t[df_t["s5p2"] == s5p2_val]
            assert len(fila) == 1, f"TC-09 FALLO: no se encontró fila con s5p2={s5p2_val}"
            tipo_obt = fila["tipo_transporte"].iloc[0]
            assert tipo_obt == tipo_esp, \
                f"TC-09 FALLO: s5p2={s5p2_val} → esperado '{tipo_esp}', obtenido '{tipo_obt}'"
