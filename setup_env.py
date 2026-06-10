#!/usr/bin/env python3
"""
setup_env.py — Verificador y configurador del entorno de desarrollo
Plataforma web indicadores ambientales ENEMDU · TFM

Uso:
    python setup_env.py

Comprueba que el entorno virtual está activo, las dependencias instaladas
y que la estructura de carpetas es correcta.
"""

import sys
import subprocess
from pathlib import Path


# Colores para la terminal
OK   = "\033[92m✓\033[0m"
ERR  = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
INFO = "\033[94mℹ\033[0m"


def check_python_version():
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"  {OK}  Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"  {ERR}  Python {version.major}.{version.minor} — Se requiere Python 3.10+")
        sys.exit(1)


def check_venv():
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        print(f"  {OK}  Entorno virtual activo: {sys.prefix}")
    else:
        print(f"  {WARN}  No estás dentro de un entorno virtual.")
        print(f"         Ejecuta: python3 -m venv .venv && source .venv/bin/activate")


def check_packages():
    required = [
        "pandas", "pyreadstat", "pyarrow", "duckdb",
        "yaml",   "streamlit",  "plotly",  "pytest",
        "numpy",  "geopandas"
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  {OK}  {pkg}")
        except ImportError:
            print(f"  {ERR}  {pkg}  ← no instalado")
            missing.append(pkg)

    if missing:
        print(f"\n  {INFO} Instala los paquetes faltantes con:")
        print(f"       pip install -r requirements.txt\n")


def check_folders():
    folders = [
        "data/raw", "data/processed", "data/outputs",
        "pipeline", "calculator", "webapp/pages", "webapp/components",
        "config", "notebooks", "tests", "docs", ".vscode"
    ]
    root = Path(__file__).parent
    for folder in folders:
        path = root / folder
        if path.exists():
            print(f"  {OK}  {folder}/")
        else:
            print(f"  {ERR}  {folder}/  ← carpeta no encontrada")
            path.mkdir(parents=True, exist_ok=True)
            print(f"       → Creada automáticamente")


def check_config_files():
    files = [
        ".vscode/settings.json",
        ".vscode/tasks.json",
        ".vscode/extensions.json",
        "requirements.txt",
        "Makefile",
        ".gitignore"
    ]
    root = Path(__file__).parent
    for f in files:
        path = root / f
        if path.exists():
            print(f"  {OK}  {f}")
        else:
            print(f"  {ERR}  {f}  ← archivo no encontrado")


if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  Verificación del entorno — ENEMDU Ambiental TFM")
    print("═" * 55)

    print("\n  Python")
    check_python_version()

    print("\n  Entorno virtual")
    check_venv()

    print("\n  Dependencias")
    check_packages()

    print("\n  Estructura de carpetas")
    check_folders()

    print("\n  Archivos de configuración")
    check_config_files()

    print("\n" + "═" * 55)
    print("  Para lanzar el proyecto usa:")
    print("    make pipeline   → ejecuta el ETL")
    print("    make app        → lanza la webapp")
    print("    make test       → corre los tests")
    print("═" * 55 + "\n")
