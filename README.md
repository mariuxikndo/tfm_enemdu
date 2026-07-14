# 🌿 Plataforma MIAH-ENEMDU 2025

**Plataforma web para el análisis y visualización de indicadores ambientales de hogares ecuatorianos**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red.svg)](https://streamlit.io/)
[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)

Plataforma desarrollada como Trabajo de Fin de Máster (TFM) del Máster Universitario en Análisis y Visualización de Datos Masivos — UNIR.

🔗 **Plataforma en línea:** https://miah-enemdu.streamlit.app

---

## Descripción

La plataforma transforma los microdatos del Módulo de Información Ambiental en Hogares (MIAH) de la Encuesta Nacional de Empleo, Desempleo y Subempleo (ENEMDU) 2025 del INEC Ecuador en indicadores ambientales interactivos. Cubre cinco dimensiones del Marco para el Desarrollo de las Estadísticas Ambientales (MDEA) de Naciones Unidas:

| Dimensión | Indicadores | ODS |
|---|---|---|
| 💧 Uso del Agua | 8 | ODS 6 |
| ♻️ Gestión de Residuos | 6 | ODS 12 |
| ⚡ Eficiencia Energética | 8 | ODS 7 |
| 🚌 Movilidad | 3 | ODS 11 |
| 🌍 Conciencia Ambiental | 5 | ODS 13 |

Todos los indicadores se calculan aplicando el **factor de expansión muestral (fexp)** del INEC, lo que garantiza la representatividad estadística de los resultados a nivel nacional, por área geográfica y por provincia.

---

## Requisitos del sistema

- **Python** 3.11 o superior
- **Sistema operativo:** Windows 10/11, macOS 12+, Ubuntu 20.04+
- **RAM mínima:** 4 GB (recomendado 8 GB)
- **Espacio en disco:** 500 MB (datos + entorno virtual)
- **Conexión a internet:** necesaria solo para el despliegue en Streamlit Cloud

---

## Estructura del repositorio

```
tfm_enemdu/
│
├── config/                         # Configuración declarativa
│   ├── indicators.yaml             # Catálogo de 30 indicadores ambientales
│   ├── cleaning_rules.yaml         # Reglas de limpieza por variable ENEMDU
│   └── settings.yaml               # Rutas y parámetros globales del sistema
│
├── data/
│   ├── raw/                        # Microdatos originales .ods del INEC (no versionados)
│   ├── processed/                  # Datos limpios en formato Parquet (generados por pipeline)
│   └── outputs/                    # Indicadores calculados: SQLite + Parquet
│
├── pipeline/                       # Pipeline ETL (4 etapas)
│   ├── ingester.py                 # Etapa 1: Lectura de archivos .ods
│   ├── cleaner.py                  # Etapa 2: Limpieza y normalización
│   ├── transformer.py              # Etapa 3: Transformación y variables derivadas
│   ├── saver.py                    # Etapa 4: Persistencia en Parquet
│   └── orchestrator.py             # Coordinador: encadena las 4 etapas
│
├── calculator/                     # Motor de cálculo de indicadores
│   ├── indicator_models.py         # Clases de indicadores (Proporción, Media, Índice)
│   ├── filters.py                  # Clase Filtros (área, provincia, periodo)
│   ├── engine.py                   # Motor principal con aplicación de fexp
│   ├── exporter.py                 # Exportación a SQLite y Parquet
│   └── run_calculator.py           # Script de ejecución del motor
│
├── webapp/                         # Plataforma web Streamlit
│   ├── app.py                      # Página de inicio (landing page)
│   ├── data_layer.py               # Capa de acceso a datos con caché
│   ├── components/
│   │   ├── sidebar_filters.py      # Panel lateral de filtros
│   │   ├── charts.py               # Biblioteca de gráficos Plotly
│   │   └── dimension_page.py       # Plantilla reutilizable de dimensión
│   └── pages/
│       ├── 1_Agua.py               # Dashboard: Uso del Agua
│       ├── 2_Residuos.py           # Dashboard: Gestión de Residuos
│       ├── 3_Energia.py            # Dashboard: Eficiencia Energética
│       ├── 4_Movilidad.py          # Dashboard: Movilidad
│       ├── 5_Conciencia.py         # Dashboard: Conciencia Ambiental
│       └── 6_Comparativo.py        # Módulo de análisis comparativo
│
├── tests/                          # Batería de tests funcionales
│   ├── conftest.py                 # Fixtures compartidos con datos sintéticos
│   ├── test_pipeline.py            # Tests TC-01 a TC-09 (pipeline ETL)
│   ├── test_indicadores.py         # Tests TC-10 a TC-22 (indicadores)
│   ├── test_filtros_motor.py       # Tests TC-23 a TC-30 (filtros y fexp)
│   ├── test_exportacion.py         # Tests TC-31 a TC-35 (exportación)
│   └── analisis_sus.py             # Script de análisis de resultados SUS
│
├── requirements.txt                # Dependencias Python
├── Makefile                        # Automatización de tareas
└── README.md                       # Este archivo
```

---

## Instalación y ejecución local

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/mariuxikndo/tfm_enemdu.git
cd tfm_enemdu
```

### Paso 2 — Crear el entorno virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### Paso 3 — Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4 — Descargar los microdatos del INEC

Descarga el archivo comprimido desde el portal oficial del INEC:

🔗 **https://www.ecuadorencifras.gob.ec/hogares/**

El archivo descargado se llama `2_BDD_DATOS_ABIERTOS_MIAH_2025_11_ODS.zip`. Descomprímelo y copia los tres archivos .ods en la carpeta `data/raw/` del proyecto:

| Archivo | Contenido |
|---|---|
| `enemdu_mod_ambiental_2025_08.ods` | Prácticas energéticas y conciencia parcial (agosto 2025) |
| `enemdu_ambiental_2025_10.ods` | Agua, residuos y conciencia ambiental (octubre 2025) |
| `enemdu_persona_2025_08.ods` | Movilidad — personas de 12 años y más (agosto 2025) |

### Paso 5 — Ejecutar el pipeline ETL

```bash
python pipeline/orchestrator.py
```

Este comando procesa los tres archivos .ods y genera los archivos Parquet en `data/processed/`. Tiempo estimado: 2–5 minutos.

### Paso 6 — Calcular los indicadores

```bash
python calculator/run_calculator.py
```

Calcula los 30 indicadores en los tres niveles de desagregación (nacional, área, provincia) y los almacena en `data/outputs/indicators.db`. Tiempo estimado: 1–3 minutos.

### Paso 7 — Lanzar la plataforma web

```bash
python -m streamlit run webapp/app.py
```

La plataforma estará disponible en http://localhost:8501

---

## Ejecución con Makefile

Si tienes `make` disponible, puedes ejecutar todo el proceso con un único comando:

```bash
make all        # pipeline + calculator + webapp
make pipeline   # solo el pipeline ETL
make calc       # solo el motor de cálculo
make app        # solo la webapp
make test       # ejecutar los tests
```

---

## Ejecutar los tests

```bash
# Todos los tests
pytest tests/ -v

# Solo tests del pipeline
pytest tests/test_pipeline.py -v

# Solo tests de indicadores
pytest tests/test_indicadores.py -v

# Con informe de cobertura
pytest tests/ --cov=pipeline --cov=calculator -v
```

---

## Despliegue en Streamlit Community Cloud

1. Asegúrate de que el repositorio tenga `requirements.txt` y `.streamlit/config.toml` en la raíz.

2. Asegúrate de que los archivos Parquet generados estén en el repositorio:
   ```bash
   git add data/processed/ data/outputs/indicators.db
   git commit -m "Add processed data for cloud deployment"
   git push origin main
   ```

3. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con GitHub.

4. Haz clic en **New app** y completa el formulario:
   - **Repository:** `mariuxikndo/tfm_enemdu`
   - **Branch:** `main`
   - **Main file path:** `webapp/app.py`

5. Haz clic en **Deploy** y espera 3–5 minutos.

La plataforma quedará disponible en: https://miah-enemdu.streamlit.app

---

## Fuente de los datos

Los microdatos utilizados son producidos y publicados por el **Instituto Nacional de Estadística y Censos (INEC) del Ecuador** bajo condiciones de uso académico:

- **Encuesta:** ENEMDU — Módulo de Información Ambiental en Hogares (MIAH) 2025
- **Portal:** https://www.ecuadorencifras.gob.ec/informacion-ambiental-en-hogares/
- **Condición de uso:** datos estadísticos públicos, citar la fuente original

---

