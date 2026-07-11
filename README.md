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
- Model interpretability with SHAP for the gradient-boosting models
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
| Deep learning | tensorflow / keras (LSTM), darts (N-BEATS) |
| Experiment tracking | MLflow |
| Interpretability | SHAP |
| Visualization | matplotlib, seaborn, plotly |
| Version control | Git + GitHub |

---

## Models evaluated

All models are evaluated on the same weekly dataset with the same metrics
(MAE, RMSE, MAPE, R²) and tracked with MLflow.

| Family | Models |
|---|---|
| Statistical | ARIMA / SARIMA (baselines), SARIMAX, Prophet |
| Gradient boosting | XGBoost, LightGBM |
| Deep learning | LSTM, N-BEATS |

---

## Notebooks

| Notebook | Purpose |
|---|---|
| `01_dengue_eda.ipynb` | Exploratory analysis, cleaning and consolidation of SIVIGILA microdata |
| `02_dengue_climate_feature.ipynb` | Climate feature ingestion, point-to-pixel validation, weekly consolidation |
| `03_dengue_modeling.ipynb` | Model experimentation and comparison (statistical, boosting, deep learning) |
| `04_dengue_clustering.ipynb` | Climate-based clustering of municipalities |
| `05_dengue_ablacion_clima_vs_lags.ipynb` | Ablation: climate vs. dengue lags |

---

## Project structure
```
dengue-surveillance-magdalena/
|--- data/
|   |--- raw/          # SIVIGILA Excel files + geojson / lookups
|   |--- interim/      # consolidated raw Parquet
|   |--- processed/    # clean + weekly modeling datasets
|   |--- external/     # climate sources, IDEAM, mappings, population
|--- notebooks/        # 01 EDA -> 02 climate -> 03 modeling -> 04 clustering -> 05 ablation
|--- src/
|   |--- dengue/
|   |   |--- loader.py         # parallel load of raw SIVIGILA Excels
|   |   |--- loader_ideam.py   # IDEAM station data via API
|--- outputs/
|   |--- figures/      # eda / climate / model figures
|--- mlruns/ , mlflow.db
|--- requirements.txt
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

Run the notebooks in order (01 → 05). The pipeline is not real-time: to add new
years, drop the annual Excel files into `data/raw/` and re-run from `01`.

---

## Dashboard & deployment

The interactive Streamlit dashboard and its Docker containerization are developed
and deployed in a **separate repository:** [check it out :)](https://github.com/Edmh1/public-health-surveillance-system.git) and are not part of this codebase, which
covers the data pipeline, feature engineering and modeling.

---

## Conclusion
> En construcción :)
