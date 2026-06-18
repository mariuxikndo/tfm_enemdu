"""
calculator/run_calculator.py
────────────────────────────────────────────────────────────────────
Script principal del motor de cálculo MIAH-ENEMDU 2025.

Ejecutar desde la raíz del proyecto:
  python calculator/run_calculator.py

O con make:
  make calculate

Produce en data/outputs/:
  - indicadores_nacional.parquet
  - indicadores_area.parquet
  - indicadores_provincia.parquet
  - indicators.db  (SQLite con las tres tablas anteriores + metadata)
"""

import logging
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator.engine   import Engine
from calculator.exporter import Exporter
from calculator.filters  import Filtros


def configurar_logging(nivel: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, nivel, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    inicio = time.time()

    try:
        with open("config/settings.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        nivel_log = cfg.get("logging", {}).get("nivel", "INFO")
    except FileNotFoundError:
        nivel_log = "INFO"

    configurar_logging(nivel_log)
    logger = logging.getLogger("run_calculator")

    logger.info("=" * 60)
    logger.info("  MOTOR DE CÁLCULO — MIAH-ENEMDU 2025")
    logger.info("=" * 60)

    # ── Inicializar motor y exportador ────────────────────────────
    logger.info("\n[1/2] Iniciando motor de cálculo...")
    engine   = Engine()
    exporter = Exporter()
    engine.resumen()

    # ── Exportar todos los niveles ────────────────────────────────
    logger.info("[2/2] Calculando y exportando indicadores...\n")
    rutas = exporter.exportar_todo(engine)

    # ── Prueba rápida: un indicador nacional ──────────────────────
    logger.info("\n  Prueba de verificación — IND_AGUA_01 (nacional):")
    df_prueba = engine.calcular_uno("IND_AGUA_01")
    if not df_prueba.empty and "valor" in df_prueba.columns:
        valor = df_prueba["valor"].iloc[0]
        pob   = df_prueba["pob_estimada"].iloc[0]
        logger.info(
            f"  ✓ Hogares que reusan el agua: {valor:.1f}% "
            f"(población estimada: {pob:,.0f})"
        )
    else:
        logger.warning("  ✗ No se pudo obtener el valor de prueba")

    # ── Resumen final ─────────────────────────────────────────────
    duracion = time.time() - inicio
    tablas   = exporter.tablas_disponibles()

    logger.info("\n" + "=" * 60)
    logger.info("  MOTOR DE CÁLCULO COMPLETADO")
    logger.info(f"  Duración: {duracion:.1f} segundos")
    logger.info(f"  Archivos generados:")
    for nivel, ruta in rutas.items():
        if ruta:
            kb = Path(ruta).stat().st_size / 1024
            logger.info(f"    {Path(ruta).name:<40} {kb:>7.1f} KB")
    logger.info(f"  SQLite ({exporter.ruta_db.name}):")
    for tabla in tablas:
        n = exporter._contar_filas_sqlite(tabla)
        logger.info(f"    tabla: {tabla:<35} {n:>5} filas")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    main()
