"""
Orquestador del pipeline ETL completo MIAH-ENEMDU 2025.

Encadena las cuatro etapas:
  Ingester → Cleaner → Transformer → Saver

Ejecutar desde la raíz del proyecto:
  python pipeline/orchestrator.py

O con make:
  make pipeline

Genera al finalizar:
  - data/processed/*.parquet   (datos limpios y transformados)
  - data/processed/schema.json (diccionario de variables)
  - data/outputs/pipeline.log  (log de ejecución)
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

# Asegurar que el path raíz esté disponible al ejecutar directamente
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.ingester    import Ingester
from pipeline.cleaner     import Cleaner
from pipeline.transformer import Transformer
from pipeline.saver       import Saver


def configurar_logging(nivel: str = "INFO", archivo: str = None) -> None:
    """Configura el sistema de logging del pipeline."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if archivo:
        Path(archivo).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(archivo, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, nivel.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def ejecutar_pipeline(ruta_settings: str = "config/settings.yaml") -> dict:
    """
    Ejecuta el pipeline ETL completo.

    Parámetros
    ----------
    ruta_settings : str
        Ruta al archivo de configuración global

    Retorna
    -------
    dict con los DataFrames procesados y metadatos de ejecución
    """
    inicio = time.time()
    logger = logging.getLogger("orchestrator")

    logger.info("=" * 60)
    logger.info("  PIPELINE ETL — MIAH-ENEMDU 2025")
    logger.info(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Etapa 1: Ingesta
    logger.info("\n[1/4] INGESTA — Leyendo archivos ODS del INEC...")
    t1 = time.time()
    ingester = Ingester(ruta_settings)
    dfs_crudos = ingester.ingest_all()

    if not dfs_crudos:
        logger.error(
            "No se cargó ningún archivo. "
            "Verifica que los ODS estén en data/raw/"
        )
        sys.exit(1)

    logger.info(
        f"  ✓ Ingesta: {len(dfs_crudos)} archivos · "
        f"{sum(len(df) for df in dfs_crudos.values()):,} filas totales · "
        f"{time.time()-t1:.1f}s"
    )

    # Etapa 2: Limpieza
    logger.info("\n[2/4] LIMPIEZA — Aplicando reglas de cleaning_rules.yaml...")
    t2 = time.time()
    cleaner = Cleaner()
    dfs_limpios = cleaner.clean_all(dfs_crudos)
    logger.info(f"  ✓ Limpieza completada · {time.time()-t2:.1f}s")

    # Etapa 3: Transformación
    logger.info("\n[3/4] TRANSFORMACIÓN — Creando variables derivadas...")
    t3 = time.time()
    transformer = Transformer(ruta_settings)
    dfs_transformados = transformer.transform_all(dfs_limpios)
    logger.info(f"  ✓ Transformación completada · {time.time()-t3:.1f}s")

    # Etapa 4: Persistencia
    logger.info("\n[4/4] PERSISTENCIA — Guardando en formato Parquet...")
    t4 = time.time()
    saver = Saver(ruta_settings)
    rutas = saver.save_all(dfs_transformados)
    logger.info(f"  ✓ Guardado completado · {time.time()-t4:.1f}s")

    # Resumen final
    duracion = time.time() - inicio
    logger.info("\n" + "=" * 60)
    logger.info("  PIPELINE COMPLETADO")
    logger.info(f"  Duración total : {duracion:.1f} segundos")
    logger.info(f"  Archivos procesados:")
    for clave, df in dfs_transformados.items():
        logger.info(
            f"    {clave:<20} {len(df):>7,} filas · "
            f"{len(df.columns)} columnas"
        )
    logger.info("  Archivos Parquet:")
    for clave, ruta in rutas.items():
        kb = Path(ruta).stat().st_size / 1024
        logger.info(f"    {Path(ruta).name:<35} {kb:>7.1f} KB")
    logger.info("=" * 60 + "\n")

    return {
        "dfs":      dfs_transformados,
        "rutas":    rutas,
        "duracion": duracion,
    }


if __name__ == "__main__":
    # Cargar configuración de logging desde settings.yaml
    try:
        with open("config/settings.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        log_cfg = cfg.get("logging", {})
        configurar_logging(
            nivel   = log_cfg.get("nivel", "INFO"),
            archivo = log_cfg.get("archivo"),
        )
    except FileNotFoundError:
        configurar_logging()

    resultado = ejecutar_pipeline()
    print(
        f"\n  Pipeline finalizado en {resultado['duracion']:.1f}s. "
        f"Datos listos en data/processed/"
    )
