"""
tests/test_filtros_motor.py
────────────────────────────────────────────────────────────────────
Tests de filtros dinámicos y del motor de cálculo.

Batería TC-23 a TC-30.
"""

import sys
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator.filters import Filtros
from calculator.indicator_models import load_catalog


TOLERANCIA = 0.1


# ══════════════════════════════════════════════════════════════════
#  TC-23 a TC-26: Filtros dinámicos
# ══════════════════════════════════════════════════════════════════

class TestFiltros:

    def test_TC23_filtro_area_urbano(self, df_ambiental_oct):
        """TC-23: Filtro area=1 (Urbano) debe retener solo 50 filas."""
        f = Filtros(area=1)
        df_f = f.aplicar(df_ambiental_oct)
        assert len(df_f) == 50, \
            f"TC-23 FALLO: esperadas 50 filas urbanas, obtenidas {len(df_f)}"
        assert (df_f["area"] == 1).all(), \
            "TC-23 FALLO: todas las filas deben ser área=1 (Urbano)"

    def test_TC24_filtro_area_rural(self, df_ambiental_oct):
        """TC-24: Filtro area=2 (Rural) debe retener solo 50 filas."""
        f = Filtros(area=2)
        df_f = f.aplicar(df_ambiental_oct)
        assert len(df_f) == 50, \
            f"TC-24 FALLO: esperadas 50 filas rurales, obtenidas {len(df_f)}"

    def test_TC25_filtro_provincia(self, df_ambiental_oct):
        """TC-25: Filtro prov=17 (Pichincha) debe retener solo 20 filas."""
        f = Filtros(prov=17)
        df_f = f.aplicar(df_ambiental_oct)
        assert len(df_f) == 20, \
            f"TC-25 FALLO: esperadas 20 filas de Pichincha, obtenidas {len(df_f)}"
        assert (df_f["prov"] == 17).all(), \
            "TC-25 FALLO: todas las filas deben ser prov=17"

    def test_TC26_filtro_sin_resultados(self, df_ambiental_oct):
        """TC-26: Filtro con provincia inexistente debe retornar DataFrame vacío."""
        f = Filtros(prov=99)
        df_f = f.aplicar(df_ambiental_oct)
        assert df_f.empty, \
            f"TC-26 FALLO: con prov=99 el resultado debería ser vacío, obtenido {len(df_f)} filas"

    def test_TC27_filtro_combinado_area_provincia(self, df_ambiental_oct):
        """TC-27: Filtro combinado área=1 + prov=17 debe retornar subconjunto."""
        f = Filtros(area=1, prov=17)
        df_f = f.aplicar(df_ambiental_oct)
        assert len(df_f) > 0, "TC-27 FALLO: el filtro combinado no debe vaciar el resultado"
        assert (df_f["area"] == 1).all(), "TC-27 FALLO: todas las filas deben ser Urbano"
        assert (df_f["prov"] == 17).all(), "TC-27 FALLO: todas las filas deben ser Pichincha"

    def test_TC28_descripcion_filtro(self):
        """TC-28: La descripción del filtro debe ser legible."""
        f = Filtros(area=1, prov=17)
        desc = f.descripcion()
        assert "Urbano" in desc, f"TC-28 FALLO: 'Urbano' no aparece en '{desc}'"
        assert "17" in desc or "Pichincha" in desc.lower(), \
            f"TC-28 FALLO: la provincia no aparece en '{desc}'"

    def test_TC29_compatibilidad_periodo_archivo(self):
        """TC-29: El filtro de período debe ser incompatible con el archivo incorrecto."""
        f_ago = Filtros(periodo="2025-08")
        f_oct = Filtros(periodo="2025-10")
        assert f_ago.es_compatible("ambiental_ago") is True
        assert f_ago.es_compatible("ambiental_oct") is False, \
            "TC-29 FALLO: periodo 2025-08 no debería ser compatible con ambiental_oct"
        assert f_oct.es_compatible("ambiental_oct") is True
        assert f_oct.es_compatible("persona_ago") is False


# ══════════════════════════════════════════════════════════════════
#  TC-30: Aplicación del factor de expansión muestral
# ══════════════════════════════════════════════════════════════════

class TestFactorExpansion:

    def test_TC30_fexp_afecta_resultado(self):
        """
        TC-30: El factor de expansión (fexp) debe afectar el cálculo ponderado.

        Con fexp desigual, el indicador ponderado difiere del no ponderado.
        """
        catalogo = load_catalog("config/indicators.yaml")
        ind = catalogo["IND_AGUA_01"]

        # DataFrame con fexp desigual: los Sí tienen fexp alto, los No tienen fexp bajo
        df_sesgado = pd.DataFrame({
            "area":         pd.array([1]*10 + [2]*10, dtype="Int64"),
            "fexp":         [100.0]*5 + [1.0]*5 + [100.0]*5 + [1.0]*5,
            # 5 hogares con s101p61=1 y fexp=100, 5 con s101p61=2 y fexp=1
            "s101p61":      pd.array([1]*5 + [2]*5 + [1]*5 + [2]*5, dtype="Int64"),
            "periodo":      ["2025-10"] * 20,
            "area_nombre":  ["Urbano"]*10 + ["Rural"]*10,
            "prov_nombre":  ["Pichincha"]*20,
        })

        res = ind.calcular(df_sesgado)
        valor_ponderado = float(res["valor"].iloc[0])

        # Sin ponderación: 10/20 = 50%
        # Con ponderación: (5*100) / (5*100 + 5*1) * 100 ≈ 99%
        assert valor_ponderado > 90, \
            f"TC-30 FALLO: con fexp alto en positivos, el indicador ponderado debe ser " \
            f"≫50% (esperado ≈99%, obtenido {valor_ponderado:.1f}%). " \
            "Verificar que fexp se aplica correctamente."
        assert valor_ponderado != 50.0, \
            "TC-30 FALLO: el indicador ponderado NO debe ser igual al no ponderado " \
            "cuando fexp es desigual."
