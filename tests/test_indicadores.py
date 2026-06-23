"""
tests/test_indicadores.py
────────────────────────────────────────────────────────────────────
Tests de cálculo de indicadores ambientales con valores esperados.

Batería TC-10 a TC-22.

Todos los resultados esperados son verificables manualmente:
  - 100 filas, fexp=10 → población estimada = 1.000
  - Si X filas tienen valor positivo → indicador = X%
"""

import sys
from pathlib import Path

import pytest
import pandas as pd

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator.indicator_models import load_catalog, IndicadorProporcion, IndicadorMedia


# ── Fixture local de catálogo ─────────────────────────────────────
@pytest.fixture(scope="module")
def catalogo():
    return load_catalog("config/indicators.yaml")


# ══════════════════════════════════════════════════════════════════
#  Tolerancia para comparaciones de flotante
# ══════════════════════════════════════════════════════════════════
TOLERANCIA = 0.1   # ±0.1 puntos porcentuales


# ══════════════════════════════════════════════════════════════════
#  TC-10 a TC-14: Dimensión AGUA
# ══════════════════════════════════════════════════════════════════

class TestIndicadoresAgua:

    def test_TC10_IND_AGUA_01_nacional(self, catalogo, df_ambiental_oct):
        """TC-10: IND_AGUA_01 — hogares que reusan el agua = 60.0%"""
        ind = catalogo["IND_AGUA_01"]
        res = ind.calcular(df_ambiental_oct)
        assert not res.empty, "TC-10 FALLO: resultado vacío"
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 60.0) <= TOLERANCIA, \
            f"TC-10 FALLO: esperado 60.0%, obtenido {valor:.2f}%"

    def test_TC11_IND_AGUA_03_cierre_llaves(self, catalogo, df_ambiental_oct):
        """TC-11: IND_AGUA_03 — cierran llaves al jabonarse = 75.0%"""
        ind = catalogo["IND_AGUA_03"]
        res = ind.calcular(df_ambiental_oct)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 75.0) <= TOLERANCIA, \
            f"TC-11 FALLO: esperado 75.0%, obtenido {valor:.2f}%"

    def test_TC12_IND_AGUA_01_por_area(self, catalogo, df_ambiental_oct):
        """TC-12: IND_AGUA_01 desagregado por área — debe tener Urbano y Rural."""
        ind = catalogo["IND_AGUA_01"]
        res = ind.calcular(df_ambiental_oct, desagregacion="area")
        assert not res.empty, "TC-12 FALLO: resultado vacío"
        col_area = "area_nombre" if "area_nombre" in res.columns else "area"
        assert len(res) >= 2, \
            "TC-12 FALLO: debe haber al menos 2 filas (Urbano y Rural)"

    def test_TC13_IND_AGUA_08_indice_promedio(self, catalogo, df_ambiental_oct):
        """TC-13: IND_AGUA_08 — índice promedio de prácticas de agua."""
        ind = catalogo["IND_AGUA_08"]
        res = ind.calcular(df_ambiental_oct)
        assert not res.empty, "TC-13 FALLO: resultado vacío"
        valor = float(res["valor"].iloc[0])
        assert 0 <= valor <= 8, \
            f"TC-13 FALLO: el índice debe estar entre 0 y 8, obtenido {valor}"

    def test_TC14_unidad_porcentaje(self, catalogo, df_ambiental_oct):
        """TC-14: Los indicadores de proporción de agua deben tener unidad '%'."""
        for iid in ["IND_AGUA_01","IND_AGUA_02","IND_AGUA_03"]:
            ind = catalogo[iid]
            res = ind.calcular(df_ambiental_oct)
            assert res["unidad"].iloc[0] == "%", \
                f"TC-14 FALLO: {iid} unidad debería ser '%', obtenido '{res['unidad'].iloc[0]}'"


# ══════════════════════════════════════════════════════════════════
#  TC-15 a TC-16: Dimensión RESIDUOS
# ══════════════════════════════════════════════════════════════════

class TestIndicadoresResiduos:

    def test_TC15_IND_RES_01_organicos(self, catalogo, df_ambiental_oct):
        """TC-15: IND_RES_01 — clasificaron residuos orgánicos = 65.0%"""
        ind = catalogo["IND_RES_01"]
        res = ind.calcular(df_ambiental_oct)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 65.0) <= TOLERANCIA, \
            f"TC-15 FALLO: esperado 65.0%, obtenido {valor:.2f}%"

    def test_TC16_IND_RES_05_clasifica_inorganico(self, catalogo, df_ambiental_oct):
        """TC-16: IND_RES_05 — al menos un inorgánico = 70.0%"""
        ind = catalogo["IND_RES_05"]
        res = ind.calcular(df_ambiental_oct)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 70.0) <= TOLERANCIA, \
            f"TC-16 FALLO: esperado 70.0%, obtenido {valor:.2f}%"


# ══════════════════════════════════════════════════════════════════
#  TC-17 a TC-18: Dimensión ENERGÍA
# ══════════════════════════════════════════════════════════════════

class TestIndicadoresEnergia:

    def test_TC17_IND_ENE_01_desconectan_aparatos(self, catalogo, df_ambiental_ago):
        """TC-17: IND_ENE_01 — desconectan aparatos = 70.0%"""
        ind = catalogo["IND_ENE_01"]
        res = ind.calcular(df_ambiental_ago)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 70.0) <= TOLERANCIA, \
            f"TC-17 FALLO: esperado 70.0%, obtenido {valor:.2f}%"

    def test_TC18_IND_ENE_03_variable_inversa(self, catalogo, df_ambiental_ago):
        """TC-18: IND_ENE_03 — NO introducen alimentos calientes = 60.0% (var. inversa)"""
        ind = catalogo["IND_ENE_03"]
        res = ind.calcular(df_ambiental_ago)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 60.0) <= TOLERANCIA, \
            f"TC-18 FALLO: esperado 60.0%, obtenido {valor:.2f}% " \
            "(IND_ENE_03 usa valor_pos=[2], si falla puede ser error en valor_pos)"


# ══════════════════════════════════════════════════════════════════
#  TC-19 a TC-20: Dimensión MOVILIDAD
# ══════════════════════════════════════════════════════════════════

class TestIndicadoresMovilidad:

    def test_TC19_IND_MOV_01_transporte_publico(self, catalogo, df_persona_ago):
        """TC-19: IND_MOV_01 — usan transporte público colectivo = 45.0%"""
        ind = catalogo["IND_MOV_01"]
        res = ind.calcular(df_persona_ago)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 45.0) <= TOLERANCIA, \
            f"TC-19 FALLO: esperado 45.0%, obtenido {valor:.2f}% " \
            "(códigos públicos: 1=autobús, 4=metrovía, 5=metro)"

    def test_TC20_IND_MOV_02_movilidad_sostenible(self, catalogo, df_persona_ago):
        """TC-20: IND_MOV_02 — movilidad sostenible = 65.0%"""
        ind = catalogo["IND_MOV_02"]
        res = ind.calcular(df_persona_ago)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 65.0) <= TOLERANCIA, \
            f"TC-20 FALLO: esperado 65.0%, obtenido {valor:.2f}%"


# ══════════════════════════════════════════════════════════════════
#  TC-21 a TC-22: Dimensión CONCIENCIA AMBIENTAL
# ══════════════════════════════════════════════════════════════════

class TestIndicadoresConciencia:

    def test_TC21_IND_CA_02_preocupacion_alta(self, catalogo, df_ambiental_oct):
        """TC-21: IND_CA_02 — muy/excesivamente preocupados = 45.0% (s91p10 in [4,5])"""
        ind = catalogo["IND_CA_02"]
        res = ind.calcular(df_ambiental_oct)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 45.0) <= TOLERANCIA, \
            f"TC-21 FALLO: esperado 45.0%, obtenido {valor:.2f}% " \
            "(escala: 4=Mucho, 5=Excesivamente)"

    def test_TC22_IND_CA_04_bolsa_reutilizable(self, catalogo, df_ambiental_ago):
        """TC-22: IND_CA_04 — usan bolsa reutilizable = 35.0%"""
        ind = catalogo["IND_CA_04"]
        res = ind.calcular(df_ambiental_ago)
        valor = float(res["valor"].iloc[0])
        assert abs(valor - 35.0) <= TOLERANCIA, \
            f"TC-22 FALLO: esperado 35.0%, obtenido {valor:.2f}%"
