#
#  Makefile — Plataforma web indicadores ambientales ENEMDU
#
#  Uso:
#    make setup      → crea el entorno virtual e instala dependencias
#    make pipeline   → ejecuta el ETL completo
#    make calculate  → calcula todos los indicadores
#    make app        → lanza la webapp Streamlit
#    make test       → ejecuta los tests con pytest
#    make clean      → limpia archivos temporales
#

PYTHON   = .venv/bin/python
PIP      = .venv/bin/pip
VENV_DIR = .venv

.PHONY: setup pipeline calculate app test clean lint help

# Ayuda
help:
	@echo ""
	@echo "  Comandos disponibles:"
	@echo ""
	@echo "  make setup       Crea el entorno virtual e instala dependencias"
	@echo "  make pipeline    Ejecuta el pipeline ETL completo"
	@echo "  make calculate   Calcula todos los indicadores"
	@echo "  make app         Lanza la webapp en http://localhost:8501"
	@echo "  make test        Ejecuta los tests con pytest"
	@echo "  make clean       Elimina archivos temporales y caché"
	@echo ""

# Entorno virtual
setup:
	@echo "→ Creando entorno virtual..."
	python3 -m venv $(VENV_DIR)
	@echo "→ Instalando dependencias..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✓ Entorno listo. Actívalo con: source .venv/bin/activate"

# Pipeline ETL
pipeline:
	@echo "→ Ejecutando pipeline ETL..."
	$(PYTHON) pipeline/orchestrator.py
	@echo "✓ Pipeline completado."

# Motor de indicadores
calculate:
	@echo "→ Calculando indicadores..."
	$(PYTHON) -m calculator.engine
	@echo "✓ Indicadores calculados y exportados a data/outputs/"

# Webapp Streamlit
app:
	@echo "→ Iniciando webapp en http://localhost:8501"
	$(VENV_DIR)/bin/streamlit run webapp/app.py --server.port 8501

# Tests
test:
	@echo "→ Ejecutando tests..."
	$(VENV_DIR)/bin/pytest tests/ -v --tb=short --cov=pipeline --cov=calculator --cov-report=term-missing

# Limpieza
clean:
	@echo "→ Limpiando archivos temporales..."
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache"   -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Limpieza completada."
