# Dengue-surveillance-magdalena

> End-to-end epidemiological surveillance pipeline for dengue in Magdalena, Colombia.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![MLflow](https://img.shields.io/badge/MLflow-experiment%20tracking-orange)

---

## Overview

A modular, reproducible data pipeline for dengue surveillance in the department
of Magdalena, a permanently endemic region of Colombia. The system ingests raw
SIVIGILA microdata (INS event codes 210, 220, 580; years 2007-2024), cleans and
consolidates it into analysis-ready datasets, enriches it with climate variables,
and compares forecasting models for weekly case counts.

Built as part of the CITES health observatory at Universidad del Magdalena,
the data layer is designed to be extensible to other notifiable diseases within
the same surveillance infrastructure.

The interactive dashboard and its Docker deployment are maintained in a separate
repository (see [Dashboard & deployment](#dashboard--deployment)).

---

## Key features

- Parallel ingestion of annual SIVIGILA Excel files into a single Parquet dataset
- Data cleaning and consolidation (completeness checks, deduplication, discard
  handling) performed in the EDA notebook
- Climate feature engineering from three gridded sources (NASA POWER, ERA5,
  CHIRPS), validated point-to-pixel against IDEAM ground stations to select the
  best source per variable
- Weekly modeling dataset combining confirmed cases with the winning climate
  source per variable
- Systematic model comparison (MAE, RMSE, MAPE, R²) tracked with MLflow
- Feature importance for the gradient-boosting models
- Climate-based clustering of Magdalena municipalities
- Ablation study isolating the predictive contribution of climate vs. dengue lags

---

## Tech stack

| Layer | Technology |
|---|---|
| Data ingestion | pandas, python-calamine, openpyxl, xlrd, pyarrow |
| Climate data | NASA POWER / ERA5 / CHIRPS (openmeteo-requests, earthengine-api, requests), IDEAM API |
| Geospatial | geopandas, folium, pykrige, scikit-gstat |
| Statistical models | statsmodels, pmdarima, prophet |
| Gradient boosting | xgboost, lightgbm |
| Deep learning | tensorflow / keras (LSTM; N-BEATS in notebooks 06-07), darts (N-BEATS in notebooks 03-05) |
| Hyperparameter search | Optuna |
| Experiment tracking | MLflow |
| Visualization | matplotlib, seaborn, plotly |
| Version control | Git + GitHub |

---

## Notebooks

| Notebook | Purpose |
|---|---|
| `01_dengue_eda.ipynb` | Exploratory analysis, cleaning and consolidation of SIVIGILA microdata |
| `02_dengue_climate_feature.ipynb` | Climate feature ingestion, point-to-pixel validation, weekly consolidation |
| `03_dengue_modeling.ipynb` | Model experimentation and comparison (statistical, boosting, deep learning) |
| `04_dengue_clustering.ipynb` | Climate-based clustering of municipalities |
| `05_dengue_ablacion_clima_vs_lags.ipynb` | Ablation: climate vs. dengue lags |
| `06_produccion_estadisticos_ml.ipynb` | Production: tuning, selection and export of the statistical and machine learning models used by the dashboard |
| `07_produccion_deep_learning.ipynb` | Production: tuning (5 seeds), selection and export of the deep learning model; final comparison of the 7 candidates |

---

## Forecasting methodology (dashboard models)

The methodology, written in Spanish for the technical report, is in
[METODOLOGIA_PRONOSTICO.md](METODOLOGIA_PRONOSTICO.md), the single reference for
how models are chosen, evaluated and exported. In short: notebooks 01 to 05 are
research and make the design decisions; notebooks 06 and 07 are production and,
with those decisions fixed, choose and tune one model per family (statistical,
machine learning, deep learning, no climate) on the dashboard series with the
dashboard's own forecasting code, then export the packages the dashboard runs.

---

## Project structure
```
dengue-surveillance-magdalena/
|--- data/
|   |--- raw/          # SIVIGILA Excel files + geojson / lookups
|   |--- interim/      # consolidated raw Parquet
|   |--- processed/    # clean + weekly modeling datasets
|   |--- external/     # climate sources, IDEAM, mappings, population
|--- notebooks/        # 01 EDA, 02 climate, 03 modeling, 04 clustering, 05 ablation, 06-07 production
|--- src/
|   |--- dengue/
|   |   |--- loader.py          # parallel load of raw SIVIGILA Excels
|   |   |--- loader_ideam.py    # IDEAM station data via API
|   |   |--- experimentacion.py # shared by 03, 05, 06, 07: outputs, metrics, seeds, Optuna, selection rules
|   |   |--- investigacion.py   # research models with and without climate (03, 05)
|   |   |--- produccion.py      # bridge to the dashboard forecasting code (06, 07)
|--- outputs/
|   |--- figures/      # one folder per notebook
|   |--- resultados/   # JSON results per notebook and Optuna histories
|   |--- paquetes/     # .zip packages for the dashboard
|--- mlruns/ , mlflow.db
|--- requirements.txt
|--- ENTORNO.md                 # installation and execution (Windows, Linux with GPU)
|--- METODOLOGIA_PRONOSTICO.md  # forecasting methodology (source of truth)
|--- README.md
```
---

## Data sources

- **SIVIGILA** — individual-level notification records
  (INS, event codes 210 / 220 / 580, 2007-2024)
- **NASA POWER / ERA5 / CHIRPS** — gridded daily climate variables
  (temperature, precipitation, humidity)
- **IDEAM** — ground-station observations used to validate climate sources
- **DANE** — municipal population projections and cartography (geojson / DIVIPOLA)

---

## Getting started

```bash
# clone the repository
git clone https://github.com/your-username/dengue-surveillance-magdalena.git
cd dengue-surveillance-magdalena

# create and activate virtual environment (Python 3.12)
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

Run the notebooks in order: 01, 02, 04, 03, 05, 06, 07. The pipeline is not
real-time: to add new years, drop the annual Excel files into `data/raw/` and
re-run from `01`.

Notebooks 03, 05, 06 and 07 start with a configuration cell with `MODO_RAPIDO`:
`True` runs a short end-to-end check (few Optuna trials, one seed, few epochs)
and writes everything under `_rapido` subfolders; `False` runs the full
methodology. Installation on Windows and on Linux with an NVIDIA GPU, how to
point notebooks 06 and 07 to the dashboard repository (`RUTA_TABLERO`), library
version compatibility with the dashboard and the commands to run each notebook
are in [ENTORNO.md](ENTORNO.md).

Outputs: figures in `outputs/figures/<notebook folder>/` (300 dpi, 6.5 in wide),
results and Optuna histories in `outputs/resultados/`, dashboard packages in
`outputs/paquetes/`, and `outputs/RESULTADOS_PARA_INFORME.md` (generated by
notebook 07 from the JSON results).

---

## Dashboard & deployment

The interactive Streamlit dashboard and its Docker containerization are developed
and deployed in a **separate repository:** [check it out :)](https://github.com/Edmh1/public-health-surveillance-system.git) and are not part of this codebase, which
covers the data pipeline, feature engineering and modeling.

---

## Experimentation hardware

The official run of notebooks 03, 05, 06 and 07 was done on one machine (Intel
Core i7-13650HX, NVIDIA RTX 5050, Windows 11); its results are the ones in
`outputs/`, the notebooks and the dashboard packages. Details are in section 13
of [METODOLOGIA_PRONOSTICO.md](METODOLOGIA_PRONOSTICO.md); run times are in
[ENTORNO.md](ENTORNO.md).

---

## Conclusion

The results of the official run on machine A (7 November 2026) are summarized in
section 13 of [METODOLOGIA_PRONOSTICO.md](METODOLOGIA_PRONOSTICO.md), and all
tables are in `outputs/RESULTADOS_PARA_INFORME.md`. The dashboard uses Prophet-AR
(statistical), XGBoost (machine learning) and LSTM (deep learning), forecasts
without climate and recommends a 4-week horizon.
