"""
tests/test_validacion_inec.py
────────────────────────────────────────────────────────────────────
Validación de indicadores calculados contra valores de referencia
del Boletín Técnico del MIAH-ENEMDU 2023 (INEC).

CRITERIO DE ACEPTACIÓN: diferencia < 1% respecto al valor publicado.

Cómo completar este archivo:
─────────────────────────────
1. Descarga el boletín técnico del INEC (2023 o 2025 cuando esté disponible):
   https://www.ecuadorencifras.gob.ec/informacion-ambiental-en-hogares/

2. Busca los valores nacionales para cada indicador en las tablas del boletín.

3. Reemplaza los valores en REFERENCIA_INEC con los del boletín.
   Los valores actuales son PLACEHOLDERS (marcados con None).

4. Ejecuta: pytest tests/test_validacion_inec.py -v

Nota: Estos tests requieren que el pipeline y el motor se hayan
ejecutado previamente (data/outputs/indicators.db debe existir).
"""

import sys
from pathlib import Path

import pytest
import pandas as pd

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════
#  VALORES DE REFERENCIA — Completar con boletín oficial INEC
#  Fuente: INEC (2023). Boletín técnico: MIAH-ENEMDU.
# ══════════════════════════════════════════════════════════════════
#
#  Instrucciones:
#    - Reemplaza None con el valor porcentual publicado por el INEC
#    - Ejemplo: si el boletín dice "62.8% clasificó residuos" → 62.8
#    - Deja None si el indicador no está publicado en el boletín
#
REFERENCIA_INEC = {
    # Dimensión: Residuos
    "IND_RES_01":  None,   # % hogares que clasificaron residuos orgánicos
    "IND_RES_02":  None,   # % clasificaron papel/cartón
    "IND_RES_03":  None,   # % clasificaron plástico
    "IND_RES_04":  None,   # % clasificaron vidrio

    # Dimensión: Agua
    "IND_AGUA_01": None,   # % reusan el agua
    "IND_AGUA_03": None,   # % cierran llaves al jabonarse
    "IND_AGUA_04": None,   # % se duchan en < 10 min

    # Dimensión: Energía
    "IND_ENE_01":  None,   # % desconectan aparatos
    "IND_ENE_02":  None,   # % apagan focos al salir
    "IND_ENE_06":  None,   # % con electrodomésticos ahorradores

    # Dimensión: Movilidad
    "IND_MOV_01":  None,   # % usan transporte público colectivo

    # Dimensión: Conciencia
    "IND_CA_02":   None,   # % muy/excesivamente preocupados por el ambiente
    "IND_CA_04":   None,   # % usan bolsa reutilizable
}

TOLERANCIA_INEC = 1.0   # criterio: diferencia < 1% respecto al boletín


# ══════════════════════════════════════════════════════════════════
#  Fixture: carga los indicadores nacionales calculados
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def indicadores_calculados() -> pd.DataFrame:
    """
    Carga los indicadores nacionales desde el SQLite.
    Si no existe, ejecuta el motor directamente.
    """
    from calculator.exporter import Exporter
    from calculator.engine   import Engine

    exporter = Exporter()
    tablas   = exporter.tablas_disponibles()

    if "indicadores_nacionales" in tablas:
        df = exporter.cargar_nacionales()
        if not df.empty:
            return df

    # Fallback: calcular directamente
    pytest.skip(
        "indicators.db no disponible. "
        "Ejecuta primero: python calculator/run_calculator.py"
    )


# ══════════════════════════════════════════════════════════════════
#  Tests de validación contra INEC
# ══════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("indicador_id,valor_inec", [
    (iid, val)
    for iid, val in REFERENCIA_INEC.items()
    if val is not None
])
def test_validacion_vs_inec(indicador_id, valor_inec, indicadores_calculados):
    """
    Valida que el indicador calculado difiere en menos de 1% del boletín INEC.
    Se ejecuta solo para los indicadores con valor de referencia definido.
    """
    df = indicadores_calculados
    fila = df[df["indicador_id"] == indicador_id]

    assert not fila.empty, \
        f"VALIDACIÓN INEC FALLO: {indicador_id} no encontrado en los resultados calculados"

    valor_calculado = float(fila["valor"].iloc[0])
    diferencia      = abs(valor_calculado - valor_inec)

    assert diferencia <= TOLERANCIA_INEC, (
        f"VALIDACIÓN INEC FALLO: {indicador_id}\n"
        f"  Valor INEC (boletín): {valor_inec:.1f}%\n"
        f"  Valor calculado:      {valor_calculado:.1f}%\n"
        f"  Diferencia:           {diferencia:.2f}%\n"
        f"  Criterio aceptación:  ≤ {TOLERANCIA_INEC}%\n"
        f"  → Verificar la aplicación del factor de expansión muestral (fexp)"
    )


def test_todos_los_indicadores_se_calculan(indicadores_calculados):
    """
    Verifica que los 30 indicadores del catálogo están en los resultados.
    """
    from calculator.indicator_models import load_catalog
    catalogo = load_catalog("config/indicators.yaml")

    ids_esperados  = set(catalogo.keys())
    ids_calculados = set(indicadores_calculados["indicador_id"].unique()) \
        if "indicador_id" in indicadores_calculados.columns else set()

    faltantes = ids_esperados - ids_calculados

    assert not faltantes, (
        f"VALIDACIÓN FALLO: {len(faltantes)} indicadores no calculados:\n"
        + "\n".join(f"  - {iid}" for iid in sorted(faltantes))
    )


def test_no_hay_valores_nulos_en_nacionales(indicadores_calculados):
    """
    Verifica que ningún indicador nacional tiene valor NaN.
    Un NaN indica fallo en el cálculo (fexp=0, variable vacía, etc.).
    """
    nulos = indicadores_calculados["valor"].isna().sum() \
        if "valor" in indicadores_calculados.columns else 0

    assert nulos == 0, (
        f"VALIDACIÓN FALLO: {nulos} indicadores tienen valor NaN\n"
        f"  → Revisar que los Parquet procesados contienen las variables correctas"
    )


def test_valores_en_rango_0_100(indicadores_calculados):
    """
    Verifica que todos los indicadores de proporción están entre 0% y 100%.
    """
    df_prop = indicadores_calculados[
        indicadores_calculados["unidad"] == "%"
    ] if "unidad" in indicadores_calculados.columns else indicadores_calculados

    if df_prop.empty:
        pytest.skip("Sin indicadores de proporción en los resultados")

    fuera_rango = df_prop[
        (df_prop["valor"] < 0) | (df_prop["valor"] > 100)
    ]

    assert fuera_rango.empty, (
        f"VALIDACIÓN FALLO: {len(fuera_rango)} indicadores con valor fuera de [0, 100]:\n"
        + fuera_rango[["indicador_id","valor"]].to_string(index=False)
    )


# ══════════════════════════════════════════════════════════════════
#  Reporte de cobertura de validación
# ══════════════════════════════════════════════════════════════════

def test_reporte_cobertura_validacion(indicadores_calculados):
    """
    Genera un reporte de cobertura de la validación vs INEC.
    No falla — solo imprime el estado de cada indicador.
    """
    print("\n")
    print("═" * 65)
    print("  REPORTE DE VALIDACIÓN vs INEC MIAH-ENEMDU")
    print("═" * 65)

    if indicadores_calculados.empty or "indicador_id" not in indicadores_calculados.columns:
        print("  Sin datos calculados disponibles.")
        return

    for iid, val_ref in sorted(REFERENCIA_INEC.items()):
        fila = indicadores_calculados[indicadores_calculados["indicador_id"] == iid]
        if fila.empty:
            print(f"  ⚠  {iid:<20} No calculado")
            continue

        val_calc = float(fila["valor"].iloc[0])
        if val_ref is None:
            print(f"  ○  {iid:<20} Calculado: {val_calc:>6.1f}%   (sin ref. INEC)")
        else:
            diff = abs(val_calc - val_ref)
            estado = "✓" if diff <= TOLERANCIA_INEC else "✗"
            print(
                f"  {estado}  {iid:<20} "
                f"INEC: {val_ref:>6.1f}%   "
                f"Calc: {val_calc:>6.1f}%   "
                f"Diff: {diff:>4.2f}%"
            )

    pendientes = sum(1 for v in REFERENCIA_INEC.values() if v is None)
    print(f"\n  Indicadores con referencia INEC:  {len(REFERENCIA_INEC) - pendientes}/{len(REFERENCIA_INEC)}")
    print(f"  Pendientes de completar:          {pendientes}")
    print("═" * 65)
