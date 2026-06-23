"""
tests/conftest.py
────────────────────────────────────────────────────────────────────
Fixtures de pytest compartidos entre todos los módulos de test.

Los datos sintéticos están diseñados con valores conocidos para que
los resultados esperados sean verificables manualmente.

Convención de fixtures sintéticos:
  - 100 filas por archivo (fácil de calcular porcentajes)
  - fexp = 10.0 en todos los registros (población = 100 × 10 = 1.000 hogares)
  - 50 filas área=1 (Urbano), 50 filas área=2 (Rural)
  - 20 filas prov=17 (Pichincha), 20 filas prov=9 (Guayas), resto otras
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Constantes de los fixtures ────────────────────────────────────
N_FILAS   = 100
FEXP_BASE = 10.0      # factor de expansión uniforme
POB_TOTAL = N_FILAS * FEXP_BASE   # 1.000 hogares estimados


# ── Fixture: ambiental_ago (energía + consumo) ────────────────────
@pytest.fixture
def df_ambiental_ago():
    """
    DataFrame sintético que simula ambiental_2025_08.ods procesado.

    Valores conocidos para verificación manual:
      s101p71=1 (desconectan aparatos): 70 filas → 70.0%
      s101p72=1 (apagan focos):         80 filas → 80.0%
      s101p73=2 (NO alimentos calientes): 60 filas → 60.0% (valor positivo=2)
      s101p74=1 (planchan todo):         50 filas → 50.0%
      s101p75=1 (luz solar):             45 filas → 45.0%
      s101p76=1 (electrodomésticos):     40 filas → 40.0%
      s101p77=1 (paneles solares):        5 filas →  5.0%
      s91p7=1   (bolsa reutilizable):    35 filas → 35.0%
    """
    rng = np.random.default_rng(42)
    n   = N_FILAS

    df = pd.DataFrame({
        "area":    np.array([1]*50 + [2]*50, dtype=int),
        "prov":    np.array([17]*20 + [9]*20 + [1]*20 + [6]*20 + [13]*20, dtype=int),
        "cant":    np.ones(n, dtype=int),
        "fexp":    np.full(n, FEXP_BASE),
        "periodo": ["2025-08"] * n,
        "archivo_origen": ["enemdu_mod_ambiental_2025_08.ods"] * n,
        # Energía: valores binarios 1=Sí, 2=No, 3=No aplica
        "s101p71": pd.array([1]*70 + [2]*30, dtype=pd.Int64Dtype()),        # 70% positivo
        "s101p72": pd.array([1]*80 + [2]*20, dtype=pd.Int64Dtype()),        # 80% positivo
        "s101p73": pd.array([1]*40 + [2]*60, dtype=pd.Int64Dtype()),        # 60% positivo (valor_pos=2)
        "s101p74": pd.array([1]*50 + [2]*50, dtype=pd.Int64Dtype()),        # 50% positivo
        "s101p75": pd.array([1]*45 + [2]*55, dtype=pd.Int64Dtype()),        # 45% positivo
        "s101p76": pd.array([1]*40 + [2]*60, dtype=pd.Int64Dtype()),        # 40% positivo
        "s101p77": pd.array([1]*5  + [2]*95, dtype=pd.Int64Dtype()),        #  5% positivo
        # Variables derivadas (creadas por transformer)
        "s101p71_positivo": pd.array([1]*70 + [0]*30, dtype=pd.Int64Dtype()),
        "s101p72_positivo": pd.array([1]*80 + [0]*20, dtype=pd.Int64Dtype()),
        "s101p73_positivo": pd.array([0]*40 + [1]*60, dtype=pd.Int64Dtype()),
        "s101p74_positivo": pd.array([1]*50 + [0]*50, dtype=pd.Int64Dtype()),
        "s101p75_positivo": pd.array([1]*45 + [0]*55, dtype=pd.Int64Dtype()),
        "s101p76_positivo": pd.array([1]*40 + [0]*60, dtype=pd.Int64Dtype()),
        "s101p77_positivo": pd.array([1]*5  + [0]*95, dtype=pd.Int64Dtype()),
        "idx_energia":      pd.array([1]*70 + [0]*30, dtype=pd.Int64Dtype()),
        # Consumo responsable
        "s91p7":  pd.array([1]*35 + [2]*50 + [3]*15, dtype=pd.Int64Dtype()),  # 35% bolsa reutilizable
        "s91p8a": pd.array([1]*40 + [2]*30 + [3]*30, dtype=pd.Int64Dtype()),
        "s91p8b": pd.array([5]*30 + [1]*70, dtype=pd.Int64Dtype()),
        "s91p8c": pd.array([4]*25 + [1]*75, dtype=pd.Int64Dtype()),
        "s91p8d": pd.array([3]*20 + [1]*80, dtype=pd.Int64Dtype()),
        # Etiquetas
        "area_nombre": ["Urbano"]*50 + ["Rural"]*50,
        "prov_nombre": ["Pichincha"]*20 + ["Guayas"]*20 + ["Azuay"]*20 +
                       ["Chimborazo"]*20 + ["Manabí"]*20,
    })
    return df


# ── Fixture: ambiental_oct (agua + residuos + conciencia) ─────────
@pytest.fixture
def df_ambiental_oct():
    """
    DataFrame sintético para ambiental_2025_10.ods.

    Valores conocidos:
      s101p61=1 (reusan agua):      60 filas → 60.0%
      s101p62=1 (usan balde):       55 filas → 55.0%
      s101p63=1 (cierran llaves):   75 filas → 75.0%
      s101p64=1 (ducha <10min):     65 filas → 65.0%
      s101p65=1 (revisan tuberías): 40 filas → 40.0%
      s101p66=1 (economizadores):   25 filas → 25.0%
      s101p67=1 (doble descarga):   15 filas → 15.0%
      s101p68=1 (botella tanque):   10 filas → 10.0%
      idx_agua promedio: (60+55+75+65+40+25+15+10)/100 = 3.45 pts
      s101p11=1 (orgánicos):        65 filas → 65.0%
      s101p12a=1 (papel):           50 filas → 50.0%
      clasifica_inorganico=1:       70 filas → 70.0%
      percibe_problema_ambiental=1: 55 filas → 55.0%
      preocupacion_alta=1:          45 filas → 45.0% (s91p10 in [4,5])
      participo_actividad=1:        20 filas → 20.0%
    """
    n = N_FILAS

    df = pd.DataFrame({
        "area":    pd.array([1]*50 + [2]*50, dtype=pd.Int64Dtype()),
        "prov":    pd.array([17]*20 + [9]*20 + [1]*20 + [6]*20 + [13]*20, dtype=pd.Int64Dtype()),
        "fexp":    np.full(n, FEXP_BASE),
        "periodo": ["2025-10"] * n,
        "vivienda": np.arange(1, n+1, dtype=int),
        "hogar":    np.ones(n, dtype=int),
        "archivo_origen": ["enemdu_ambiental_2025_10.ods"] * n,
        # Agua: 1=Sí, 2=No, 3=No aplica
        "s101p61": pd.array([1]*60 + [2]*40, dtype=pd.Int64Dtype()),
        "s101p62": pd.array([1]*55 + [2]*45, dtype=pd.Int64Dtype()),
        "s101p63": pd.array([1]*75 + [2]*25, dtype=pd.Int64Dtype()),
        "s101p64": pd.array([1]*65 + [2]*35, dtype=pd.Int64Dtype()),
        "s101p65": pd.array([1]*40 + [2]*60, dtype=pd.Int64Dtype()),
        "s101p66": pd.array([1]*25 + [2]*75, dtype=pd.Int64Dtype()),
        "s101p67": pd.array([1]*15 + [2]*85, dtype=pd.Int64Dtype()),
        "s101p68": pd.array([1]*10 + [2]*90, dtype=pd.Int64Dtype()),
        # Variables derivadas de agua
        "s101p61_positivo": pd.array([1]*60 + [0]*40, dtype=pd.Int64Dtype()),
        "s101p62_positivo": pd.array([1]*55 + [0]*45, dtype=pd.Int64Dtype()),
        "s101p63_positivo": pd.array([1]*75 + [0]*25, dtype=pd.Int64Dtype()),
        "s101p64_positivo": pd.array([1]*65 + [0]*35, dtype=pd.Int64Dtype()),
        "s101p65_positivo": pd.array([1]*40 + [0]*60, dtype=pd.Int64Dtype()),
        "s101p66_positivo": pd.array([1]*25 + [0]*75, dtype=pd.Int64Dtype()),
        "s101p67_positivo": pd.array([1]*15 + [0]*85, dtype=pd.Int64Dtype()),
        "s101p68_positivo": pd.array([1]*10 + [0]*90, dtype=pd.Int64Dtype()),
        "idx_agua": pd.array(
            # 60 registros con 8 prácticas, 40 con 0 (simplificado)
            [4]*60 + [1]*40, dtype=int
        ),
        # Residuos: 1=Sí, 2=No
        "s101p11":  pd.array([1]*65 + [2]*35, dtype=pd.Int64Dtype()),
        "s101p12a": pd.array([1]*50 + [2]*50, dtype=pd.Int64Dtype()),
        "s101p12b": pd.array([1]*45 + [2]*55, dtype=pd.Int64Dtype()),
        "s101p12c": pd.array([1]*30 + [2]*70, dtype=pd.Int64Dtype()),
        "s101p12d": pd.array([1]*25 + [2]*75, dtype=pd.Int64Dtype()),
        "s101p12e": pd.array([1]*20 + [2]*80, dtype=pd.Int64Dtype()),
        # Variables derivadas de residuos
        "clasifica_inorganico": pd.array([1]*70 + [0]*30, dtype=pd.Int64Dtype()),
        # Disposición de residuos (1=centro acopio, 2=regaló, 3=basura, 4=quema, 5=compost, 6=almacenó, 7=no generó)
        "s101p2a": pd.array([1]*30 + [2]*10 + [3]*40 + [4]*10 + [5]*10, dtype=pd.Int64Dtype()),
        # Conciencia ambiental
        "s91p91": pd.array([1]*40 + [2]*60, dtype=pd.Int64Dtype()),
        "s91p92": pd.array([1]*35 + [2]*65, dtype=pd.Int64Dtype()),
        "s91p93": pd.array([1]*45 + [2]*55, dtype=pd.Int64Dtype()),
        "s91p94": pd.array([1]*50 + [2]*50, dtype=pd.Int64Dtype()),
        "s91p95": pd.array([1]*30 + [2]*70, dtype=pd.Int64Dtype()),
        "s91p96": pd.array([1]*25 + [2]*75, dtype=pd.Int64Dtype()),
        "s91p10": pd.array([4]*30 + [5]*15 + [3]*30 + [2]*15 + [1]*10, dtype=pd.Int64Dtype()),
        "s91p111": pd.array([1]*15 + [2]*85, dtype=pd.Int64Dtype()),
        "s91p112": pd.array([1]*10 + [2]*90, dtype=pd.Int64Dtype()),
        "s91p113": pd.array([1]*8  + [2]*92, dtype=pd.Int64Dtype()),
        "s91p114": pd.array([1]*12 + [2]*88, dtype=pd.Int64Dtype()),
        "s91p115": pd.array([1]*7  + [2]*93, dtype=pd.Int64Dtype()),
        # Variables derivadas de conciencia
        "percibe_problema_ambiental":   pd.array([1]*55 + [0]*45, dtype=pd.Int64Dtype()),
        "preocupacion_alta":            pd.array([1]*45 + [0]*55, dtype=pd.Int64Dtype()),
        "participo_actividad_ambiental": pd.array([1]*20 + [0]*80, dtype=pd.Int64Dtype()),
        "idx_conciencia":               pd.array([2]*45 + [1]*30 + [0]*25, dtype=pd.Int64Dtype()),
        # Etiquetas
        "area_nombre": ["Urbano"]*50 + ["Rural"]*50,
        "prov_nombre": ["Pichincha"]*20 + ["Guayas"]*20 + ["Azuay"]*20 +
                       ["Chimborazo"]*20 + ["Manabí"]*20,
    })
    return df


# ── Fixture: persona_ago (movilidad) ─────────────────────────────
@pytest.fixture
def df_persona_ago():
    """
    DataFrame sintético para persona_2025_08.ods.

    Valores conocidos (excluyendo s5p2=99 que son NaN):
      s5p2 códigos reales (formulario AGO-2025):
        1=Autobús:                30 → 30.0% de quienes responden
        4=Metrovía/Trolebús:      10 → 10.0%
        5=Metro:                   5 → 5.0%
        6=Automóvil:              20 → 20.0%
        7=Moto privada:           10 → 10.0%
        8=Bicicleta:               8 → 8.0%
        9=Caminar:                12 → 12.0%
        10=Vehículo eléctrico:     2 → 2.0%
        11=Otro:                   3 → 3.0%
      Transporte público colectivo (1+4+5): 45 → 45.0%
      Movilidad sostenible (1+4+5+8+9):     65 → 65.0%
    """
    n = N_FILAS

    # 100 personas; distribuimos los modos de transporte
    s5p2_vals = (
        [1]*30 + [4]*10 + [5]*5 +    # público colectivo: 45
        [6]*20 + [7]*10 +             # privado motorizado: 30
        [8]*8  + [9]*12 +             # no motorizado: 20
        [10]*2 + [11]*3               # eléctrico + otro: 5
    )  # total = 100 filas con valor válido

    tipo_transp = (
        ["publico_colectivo"]*45 +
        ["privado_motorizado"]*30 +
        ["no_motorizado"]*20 +
        ["electrico"]*2 +
        ["otro"]*3
    )

    df = pd.DataFrame({
        "area":    pd.array([1]*50 + [2]*50, dtype=pd.Int64Dtype()),
        "prov":    pd.array([17]*20 + [9]*20 + [1]*20 + [6]*20 + [13]*20, dtype=pd.Int64Dtype()),
        "cant":    np.ones(n, dtype=int),
        "vivienda": np.arange(1, n+1, dtype=int),
        "hogar":    np.ones(n, dtype=int),
        "p01":      np.arange(1, n+1, dtype=int),
        "p02":      pd.array([1]*50 + [2]*50, dtype=pd.Int64Dtype()),
        "p03":      pd.array([25]*50 + [35]*50, dtype=pd.Int64Dtype()),
        "fexp":     np.full(n, FEXP_BASE),
        "periodo":  ["2025-08"] * n,
        "archivo_origen": ["enemdu_persona_2025_08.ods"] * n,
        # Movilidad
        "s5p2":  pd.array(s5p2_vals, dtype=pd.Int64Dtype()),
        "s5p3":  pd.array([1]*30 + [2]*30 + [3]*20 + [7]*20, dtype=pd.Int64Dtype()),
        "s5p4":  pd.array([1]*30 + [2]*70, dtype=pd.Int64Dtype()),
        "s5p6a": pd.array([0]*40 + [1]*40 + [2]*20, dtype=pd.Int64Dtype()),
        "s5p6b": pd.array([30]*40 + [20]*40 + [45]*20, dtype=pd.Int64Dtype()),
        "s5p7a": pd.array([2]*40 + [5]*40 + [10]*20, dtype="float"),
        "s5p7b": pd.array([500]*40 + [200]*40 + [0]*20, dtype=pd.Int64Dtype()),
        "ingpc": np.random.default_rng(42).uniform(200, 1500, n),
        # Variables derivadas
        "tipo_transporte": tipo_transp,
        "usa_transporte_publico":   pd.array([1]*45 + [0]*55, dtype=pd.Int64Dtype()),
        "usa_movilidad_sostenible": pd.array([1]*65 + [0]*35, dtype=pd.Int64Dtype()),
        "tiempo_traslado_min": pd.array([30]*40 + [80]*40 + [45]*20, dtype=float),
        "distancia_km": pd.array([2.5]*40 + [5.2]*40 + [10.0]*20, dtype=float),
        # Etiquetas
        "area_nombre": ["Urbano"]*50 + ["Rural"]*50,
        "prov_nombre": ["Pichincha"]*20 + ["Guayas"]*20 + ["Azuay"]*20 +
                       ["Chimborazo"]*20 + ["Manabí"]*20,
    })
    return df
