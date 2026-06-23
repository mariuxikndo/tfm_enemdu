"""
tests/test_exportacion.py
────────────────────────────────────────────────────────────────────
Tests de exportación de resultados y lectura desde SQLite.

Batería TC-31 a TC-35.
"""

import sys
import tempfile
from pathlib import Path

import pytest
import pandas as pd

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def exporter_tmp(tmp_path):
    """Exporter con base de datos temporal para no afectar data/outputs/."""
    import yaml
    from calculator.exporter import Exporter

    # Crear settings temporales apuntando a tmp_path
    settings = {
        "rutas": {
            "raw":       str(tmp_path / "raw"),
            "processed": str(tmp_path / "processed"),
            "outputs":   str(tmp_path / "outputs"),
            "db":        str(tmp_path / "outputs" / "test_indicators.db"),
        }
    }
    cfg_path = tmp_path / "settings.yaml"
    with open(cfg_path, "w") as f:
        yaml.dump(settings, f)

    return Exporter(ruta_settings=str(cfg_path))


@pytest.fixture
def df_resultado_ejemplo():
    """DataFrame de resultados de ejemplo para tests de exportación."""
    return pd.DataFrame({
        "dimension":      ["agua", "agua"],
        "indicador_id":   ["IND_AGUA_01", "IND_AGUA_02"],
        "indicador":      ["Reusan el agua", "Usan balde"],
        "valor":          [60.0, 55.0],
        "unidad":         ["%", "%"],
        "n_muestra":      [100, 100],
        "pob_estimada":   [1000.0, 1000.0],
        "archivo":        ["ambiental_oct", "ambiental_oct"],
    })


class TestExportacion:

    def test_TC31_exportar_a_sqlite(self, exporter_tmp, df_resultado_ejemplo):
        """TC-31: Los resultados deben guardarse correctamente en SQLite."""
        ruta = exporter_tmp.exportar(
            df_resultado_ejemplo,
            tabla="indicadores_nacionales",
            nivel="nacional",
        )
        assert ruta is not None, "TC-31 FALLO: exportar() retornó None"
        tablas = exporter_tmp.tablas_disponibles()
        assert "indicadores_nacionales" in tablas, \
            "TC-31 FALLO: la tabla 'indicadores_nacionales' no fue creada en SQLite"

    def test_TC32_leer_desde_sqlite(self, exporter_tmp, df_resultado_ejemplo):
        """TC-32: Los datos exportados deben poder leerse de vuelta correctamente."""
        exporter_tmp.exportar(
            df_resultado_ejemplo,
            tabla="indicadores_nacionales",
            nivel="nacional",
        )
        df_leido = exporter_tmp.cargar_nacionales()
        assert not df_leido.empty, \
            "TC-32 FALLO: cargar_nacionales() retornó DataFrame vacío"
        assert len(df_leido) == len(df_resultado_ejemplo), \
            f"TC-32 FALLO: se guardaron {len(df_resultado_ejemplo)} filas pero se leyeron {len(df_leido)}"

    def test_TC33_valores_intactos_en_sqlite(self, exporter_tmp, df_resultado_ejemplo):
        """TC-33: Los valores numéricos deben conservarse sin pérdida al pasar por SQLite."""
        exporter_tmp.exportar(
            df_resultado_ejemplo,
            tabla="indicadores_nacionales",
            nivel="nacional",
        )
        df_leido = exporter_tmp.cargar_nacionales()
        valor_original = df_resultado_ejemplo["valor"].iloc[0]
        valor_leido    = float(df_leido["valor"].iloc[0])
        assert abs(valor_original - valor_leido) < 0.01, \
            f"TC-33 FALLO: valor guardado {valor_original}, leído {valor_leido} (diferencia > 0.01)"

    def test_TC34_parquet_exportado(self, exporter_tmp, df_resultado_ejemplo):
        """TC-34: El archivo Parquet debe generarse junto al SQLite."""
        ruta = exporter_tmp.exportar(
            df_resultado_ejemplo,
            tabla="indicadores_nacionales",
            nivel="nacional",
        )
        assert Path(ruta).exists(), \
            f"TC-34 FALLO: el archivo Parquet no fue creado en {ruta}"
        df_parquet = pd.read_parquet(ruta, engine="pyarrow")
        assert not df_parquet.empty, \
            "TC-34 FALLO: el archivo Parquet está vacío"

    def test_TC35_dimension_filtrada_desde_sqlite(self, exporter_tmp, df_resultado_ejemplo):
        """TC-35: cargar_dimension() debe filtrar correctamente por dimensión."""
        exporter_tmp.exportar(
            df_resultado_ejemplo,
            tabla="indicadores_nacionales",
            nivel="nacional",
        )
        df_agua = exporter_tmp.cargar_dimension("agua", nivel="nacional")
        assert not df_agua.empty, \
            "TC-35 FALLO: no se encontraron indicadores de 'agua'"
        assert (df_agua["dimension"] == "agua").all(), \
            "TC-35 FALLO: cargar_dimension('agua') retornó filas de otra dimensión"
