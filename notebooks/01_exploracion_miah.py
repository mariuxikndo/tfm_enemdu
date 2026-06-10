"""
notebooks/01_exploracion_miah.py
────────────────────────────────────────────────────────────────────
OE1 — Análisis exploratorio de los microdatos MIAH-ENEMDU 2025

Ejecutar desde la raíz del proyecto:
  python notebooks/01_exploracion_miah.py

O abrir como notebook en VS Code:
  Convertir a .ipynb con: jupytext --to notebook 01_exploracion_miah.py

Produce:
  - Perfil completo de cada archivo (tipos, nulos, valores únicos)
  - Verificación del factor de expansión (fexp)
  - Distribución por área y provincia
  - Valores únicos por variable ambiental
  - Reporte guardado en data/outputs/exploracion_reporte.txt
"""

# %% [markdown]
# # Exploración de microdatos MIAH-ENEMDU 2025
# ## OE1: Análisis de estructura, calidad y variables relevantes

# %%
import sys
import os
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")

# Asegurar que el path raíz del proyecto esté disponible
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pipeline.ingester import Ingester

print("=" * 60)
print("  Exploración MIAH-ENEMDU 2025")
print("=" * 60)

# %% [markdown]
# ## 1. Carga de los tres archivos

# %%
ingester = Ingester(ruta_settings="config/settings.yaml")
ingester.diagnostico()

# Cargar todos los archivos
dfs = ingester.ingest_all()

ambiental_ago = dfs.get("ambiental_ago")
ambiental_oct = dfs.get("ambiental_oct")
persona_ago   = dfs.get("persona_ago")

print(f"\nArchivos cargados: {list(dfs.keys())}\n")

# %% [markdown]
# ## 2. Resumen general de cada archivo

# %%
def resumen_archivo(df: pd.DataFrame, nombre: str) -> None:
    """Imprime el perfil básico de un DataFrame."""
    print(f"\n{'─'*55}")
    print(f"  {nombre}")
    print(f"{'─'*55}")
    print(f"  Filas     : {len(df):,}")
    print(f"  Columnas  : {len(df.columns)}")
    print(f"  Columnas  : {df.columns.tolist()}")
    print(f"\n  Tipos de dato:")
    for col in df.columns:
        nulos = df[col].isna().sum()
        pct   = nulos / len(df) * 100
        uniq  = df[col].nunique()
        print(f"    {col:<20} {str(df[col].dtype):<10} "
              f"nulos={nulos:>5} ({pct:4.1f}%)  únicos={uniq}")


if ambiental_ago is not None:
    resumen_archivo(ambiental_ago, "ambiental_2025_08.ods — Energía + Consumo")

if ambiental_oct is not None:
    resumen_archivo(ambiental_oct, "ambiental_2025_10.ods — Agua + Residuos + Conciencia")

if persona_ago is not None:
    resumen_archivo(persona_ago, "personas_2025_08.ods — Movilidad")

# %% [markdown]
# ## 3. Verificación del factor de expansión (fexp)

# %%
def verificar_fexp(df: pd.DataFrame, nombre: str) -> None:
    """Analiza la distribución del factor de expansión muestral."""
    if df is None or "fexp" not in df.columns:
        print(f"  [{nombre}] fexp no encontrado")
        return

    fexp = df["fexp"]
    print(f"\n  [{nombre}] Factor de expansión (fexp):")
    print(f"    Total registros   : {len(fexp):,}")
    print(f"    fexp nulos        : {fexp.isna().sum()}")
    print(f"    fexp = 0          : {(fexp == 0).sum()}")
    print(f"    fexp < 0          : {(fexp < 0).sum()}")
    print(f"    Min               : {fexp.min():,.2f}")
    print(f"    Max               : {fexp.max():,.2f}")
    print(f"    Media             : {fexp.mean():,.2f}")
    print(f"    Suma (≈ población): {fexp.sum():,.0f}")

print("\n" + "═"*55)
print("  FACTOR DE EXPANSIÓN MUESTRAL")
print("═"*55)
for nombre, df in [
    ("ambiental_ago", ambiental_ago),
    ("ambiental_oct", ambiental_oct),
    ("persona_ago",   persona_ago),
]:
    verificar_fexp(df, nombre)

# %% [markdown]
# ## 4. Distribución geográfica

# %%
def distribucion_geo(df: pd.DataFrame, nombre: str,
                     col_area: str = "area",
                     col_prov: str = "prov") -> None:
    """Muestra distribución por área y provincia."""
    if df is None:
        return

    print(f"\n  [{nombre}] Distribución geográfica:")

    if col_area in df.columns:
        dist_area = df[col_area].value_counts().sort_index()
        for val, cnt in dist_area.items():
            etq = {1: "Urbano", 2: "Rural"}.get(val, str(val))
            pct = cnt / len(df) * 100
            print(f"    area={val} ({etq:<8}): {cnt:>6,} ({pct:5.1f}%)")

    # Detectar variable provincia (puede llamarse prov o prov_dirad)
    col_prov_real = col_prov if col_prov in df.columns else \
                    "prov_dirad" if "prov_dirad" in df.columns else None

    if col_prov_real:
        n_provincias = df[col_prov_real].nunique()
        print(f"\n    Provincias distintas ({col_prov_real}): {n_provincias}")
        top5 = df[col_prov_real].value_counts().head(5)
        print(f"    Top 5 provincias por frecuencia:")
        for prov, cnt in top5.items():
            print(f"      prov={prov}: {cnt:,}")

print("\n" + "═"*55)
print("  DISTRIBUCIÓN GEOGRÁFICA")
print("═"*55)
distribucion_geo(ambiental_ago, "ambiental_ago")
distribucion_geo(ambiental_oct, "ambiental_oct")
distribucion_geo(persona_ago,   "persona_ago")

# %% [markdown]
# ## 5. Valores únicos por variables ambientales clave

# %%
def perfil_variables(df: pd.DataFrame, variables: list, nombre: str) -> None:
    """Muestra la distribución de valores para un grupo de variables."""
    if df is None:
        return
    print(f"\n  [{nombre}]")
    for var in variables:
        if var not in df.columns:
            print(f"    {var:<15} → NO ENCONTRADA en el archivo")
            continue
        vc = df[var].value_counts(dropna=False).sort_index()
        vals_str = ", ".join([f"{v}:{c}" for v, c in vc.items()])
        print(f"    {var:<15} → {vals_str}")

# Energía
if ambiental_ago is not None:
    print("\n" + "═"*55)
    print("  VARIABLES ENERGÍA (s101p71-77)")
    print("═"*55)
    perfil_variables(
        ambiental_ago,
        ["s101p71","s101p72","s101p73","s101p74","s101p75","s101p76","s101p77"],
        "ambiental_ago"
    )

# Agua
if ambiental_oct is not None:
    print("\n" + "═"*55)
    print("  VARIABLES AGUA (s101p61-68)")
    print("═"*55)
    perfil_variables(
        ambiental_oct,
        ["s101p61","s101p62","s101p63","s101p64","s101p65","s101p66","s101p67","s101p68"],
        "ambiental_oct"
    )

# Residuos clasificación
if ambiental_oct is not None:
    print("\n" + "═"*55)
    print("  VARIABLES RESIDUOS — Clasificación")
    print("═"*55)
    perfil_variables(
        ambiental_oct,
        ["s101p11","s101p12a","s101p12b","s101p12c","s101p12d","s101p12e"],
        "ambiental_oct"
    )

# Conciencia ambiental
if ambiental_oct is not None:
    print("\n" + "═"*55)
    print("  VARIABLES CONCIENCIA AMBIENTAL")
    print("═"*55)
    perfil_variables(
        ambiental_oct,
        ["s91p91","s91p92","s91p93","s91p94","s91p95","s91p96","s91p10"],
        "ambiental_oct"
    )

# Movilidad
if persona_ago is not None:
    print("\n" + "═"*55)
    print("  VARIABLES MOVILIDAD")
    print("═"*55)
    perfil_variables(
        persona_ago,
        ["s5p2","s5p3","s5p4","s5p6a","s5p6b","s5p7a","s5p7b"],
        "persona_ago"
    )

# %% [markdown]
# ## 6. Prueba de cálculo ponderado con fexp
# Ejemplo: % hogares que apagan focos al salir (s101p72) — variable de energía

# %%
def calcular_indicador_binario_ponderado(
    df: pd.DataFrame,
    variable: str,
    valor_positivo: int,
    descripcion: str,
    desglose_area: bool = True,
) -> None:
    """
    Calcula un indicador binario ponderado con fexp.
    valor_positivo: el código que representa "Sí" o el comportamiento positivo.
    """
    if df is None or variable not in df.columns or "fexp" not in df.columns:
        return

    # Filtrar registros válidos (sin nulos en variable ni en fexp)
    df_valido = df.dropna(subset=[variable, "fexp"]).copy()
    df_valido = df_valido[df_valido["fexp"] > 0]
    df_valido[variable] = pd.to_numeric(df_valido[variable], errors="coerce")
    df_valido = df_valido.dropna(subset=[variable])

    total_pond = df_valido["fexp"].sum()
    positivos  = df_valido.loc[df_valido[variable] == valor_positivo, "fexp"].sum()
    pct_total  = positivos / total_pond * 100

    print(f"\n  {descripcion}")
    print(f"    Variable          : {variable} = {valor_positivo}")
    print(f"    Registros válidos : {len(df_valido):,}")
    print(f"    Población estimada: {total_pond:,.0f}")
    print(f"    % nacional        : {pct_total:.1f}%")

    if desglose_area and "area" in df_valido.columns:
        for area_val, etq in [(1, "Urbano"), (2, "Rural")]:
            sub = df_valido[df_valido["area"] == area_val]
            if len(sub) == 0:
                continue
            t = sub["fexp"].sum()
            p = sub.loc[sub[variable] == valor_positivo, "fexp"].sum()
            print(f"    % {etq:<10}    : {p/t*100:.1f}%  (n={len(sub):,})")


print("\n" + "═"*55)
print("  PRUEBA DE CÁLCULO CON FACTOR DE EXPANSIÓN")
print("═"*55)

# Energía: apagan focos (s101p72) — 1=Siempre
if ambiental_ago is not None:
    calcular_indicador_binario_ponderado(
        ambiental_ago, "s101p72", 1,
        "Hogares que SIEMPRE apagan focos al salir"
    )

# Agua: reusan el agua (s101p61) — 1=Siempre
if ambiental_oct is not None:
    calcular_indicador_binario_ponderado(
        ambiental_oct, "s101p61", 1,
        "Hogares que SIEMPRE reusan el agua"
    )

# Residuos: clasifican orgánicos (s101p11) — 1=Sí
if ambiental_oct is not None:
    calcular_indicador_binario_ponderado(
        ambiental_oct, "s101p11", 1,
        "Hogares que clasificaron residuos orgánicos"
    )

# Movilidad: transporte público (s5p2) — verificar código en exploración
if persona_ago is not None and "s5p2" in persona_ago.columns:
    print(f"\n  Valores únicos en s5p2 (medio de traslado):")
    print(f"    {persona_ago['s5p2'].value_counts().to_dict()}")

# %% [markdown]
# ## 7. Guardar reporte de exploración

# %%
import io
from contextlib import redirect_stdout

os.makedirs("data/outputs", exist_ok=True)
reporte_path = "data/outputs/exploracion_reporte.txt"

print(f"\n\n  Guardando reporte en {reporte_path} ...")
# El reporte se genera ejecutando el script — ver output de consola
with open(reporte_path, "w", encoding="utf-8") as f:
    f.write("REPORTE DE EXPLORACIÓN — MIAH-ENEMDU 2025\n")
    f.write("=" * 60 + "\n\n")
    for nombre, df in [
        ("ambiental_ago", ambiental_ago),
        ("ambiental_oct", ambiental_oct),
        ("persona_ago",   persona_ago),
    ]:
        if df is not None:
            f.write(f"\n[{nombre}]\n")
            f.write(f"  Filas    : {len(df):,}\n")
            f.write(f"  Columnas : {df.columns.tolist()}\n")
            f.write(f"  Nulos:\n")
            for col in df.columns:
                n = df[col].isna().sum()
                if n > 0:
                    f.write(f"    {col}: {n} nulos ({n/len(df)*100:.1f}%)\n")

print(f"  ✓ Reporte guardado.\n")
print("  EXPLORACIÓN COMPLETADA — revisa los resultados arriba")
print("  y ajusta cleaning_rules.yaml si encuentras valores inesperados.\n")
