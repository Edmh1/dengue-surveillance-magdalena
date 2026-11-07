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
| Deep learning | tensorflow / keras (LSTM; N-BEATS in notebooks 06-07), darts (N-BEATS in notebooks 03-05) |
| Hyperparameter search | Optuna |
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
| `06_produccion_estadisticos_ml.ipynb` | Production: tuning, selection and export of the statistical and machine learning models used by the dashboard |
| `07_produccion_deep_learning.ipynb` | Production: tuning (5 seeds), selection and export of the deep learning model; final comparison of the 7 candidates |

---

## Forecasting methodology (dashboard models)

The full methodology, written in Spanish for the technical report, is in
[METODOLOGIA_PRONOSTICO.md](METODOLOGIA_PRONOSTICO.md). Summary:

- Notebooks 01 to 05 are research (series 2007-2024, with climate): they make the
  design decisions (case definition, climate source, log1p transform,
  autoregressive inputs, viable families, multi-step evaluation, forecasting
  without climate). Notebooks 06 and 07 are production: with those decisions
  fixed, they choose and tune the concrete model of each family on the dashboard
  series (2007-2025) with the dashboard's own forecasting code, so what is
  evaluated here is exactly what the dashboard runs. Metrics from the two series
  are not comparable. The methodology has a table with the question each
  notebook answers and the decision it supports.
- One model per family (statistical, machine learning, deep learning), no climate.
- Periods, identical for all families: training 2007 to April 2022 (85 % of
  2007-2024), test April 2022 to December 2024 (15 %), final prospective test on
  2025 (never used for any decision).
- Walk-forward multi-step evaluation at every horizon from 1 to 6 weeks.
- Hyperparameters tuned with Optuna (TPE sampler, fixed seed) inside the
  training period only, minimizing the global RMSE over horizons 1 to 6:
  temporal cross-validation with three folds for statistical and ML models
  (85/15); a separate validation block for deep learning (70/15/15), with 5
  seeds, determinism and median pruning, choosing the most stable configuration.
- Winner per family chosen on the test period by the global RMSE over all
  horizon 1 to 6 records at once (the same global metric the dashboard stores
  in each manifest); within 2 % of RMSE the lower global MAE wins, and for deep
  learning the lower spread across seeds breaks a remaining tie. Persistence is
  a control, not a selection criterion. Full report: MAE, RMSE, MAPE and R²,
  global and at horizons 1 to 6.
- Export: validation on the last 15 % of 2007-2025 (metrics and blind forecasts
  saved for the dashboard), then the final model trained on the full range,
  packaged as a .zip and uploaded from the dashboard's management section.

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

All experimentation runs on two machines. Machine A produces the official results
(the ones in `outputs/`, the notebooks and the dashboard packages); machine B
repeats the same methodology on different hardware, with TensorFlow on GPU, and
also runs the sensitivity analysis of the deep learning search. Its full results
go to `resultados_cluster/`, next to machine A's, so both can be compared openly.

| | Machine A (official run) | Machine B (cluster) |
|---|---|---|
| CPU | Intel Core i7-13650HX (14 cores), 24 GB RAM | to be recorded |
| GPU | NVIDIA RTX 5050, 8 GB | NVIDIA RTX 6000 Ada, 48 GB (gpu2) |
| OS / Python | Windows 11 / 3.12.10 | Rocky Linux / 3.12 |
| TensorFlow | CPU (no GPU support on native Windows) | GPU |
| PyTorch | GPU (CUDA 13.0) | GPU |
| Runs | notebooks 03, 05, 06, 07 | notebooks 03, 05, 06, 07 + sensitivity analysis (`SENSIBILIDAD=1`) |
| Results | `outputs/` | `resultados_cluster/` |

Run times on machine A (full mode, chains 03→05 and 06→07 in parallel):

| Notebook | Minutes |
|---|---|
| 03 Modeling with climate | 94 |
| 05 Climate vs. lags ablation | 154 |
| 06 Production: statistical and ML | 67 |
| 07 Production: deep learning | 150 |

Notebooks 01, 02 and 04 were not re-run (they need the raw SIVIGILA files and
Earth Engine credentials); their outputs come from the original data preparation.

---

## Conclusion

Results of the official full run on machine A (MODO_RAPIDO = 0, 7 November 2026).
Details and library versions are in section 13 of
[METODOLOGIA_PRONOSTICO.md](METODOLOGIA_PRONOSTICO.md); all tables are in
`outputs/RESULTADOS_PARA_INFORME.md`.

Dashboard winners (dashboard series, test April 2022 to December 2024, global
RMSE over horizons 1 to 6; persistence 18.12):

| Family | Winner | RMSE | R² | RMSE / persistence | RMSE 2025 (persistence 38.73) |
|---|---|---|---|---|---|
| Statistical | Prophet-AR | 16.21 | 0.768 | 0.894 | 41.74 |
| Machine learning | XGBoost | 20.15 | 0.641 | 1.112 | 44.24 |
| Deep learning | LSTM (5 seeds) | 18.86 ± 0.38 | 0.685 | 1.041 | 44.58 ± 0.65 |

- Prophet-AR is the best of the seven candidates and the only one that beats
  persistence on the test period (horizons 2 to 6).
- In 2025, an outbreak larger than anything in the history, no winner beats
  persistence.
- Recommended horizon: 4 weeks, the longest horizon at which all three winners
  explain at least 60 % of the weekly variation on the test period (R² 0.750,
  0.624 and 0.658); in 2025 they still explain about half (0.537, 0.532, 0.469).
- Climate (notebook 05) improves five of the seven research models, little at one
  week and more at long horizons, but not every family. It was measured with
  observed climate inside the horizon, and there is no climate data for 2025. The
  dashboard therefore forecasts without climate in this version; adding climate
  is future work.
- Machine B's full run and the sensitivity analysis of the deep learning search
  (`SENSIBILIDAD=1`) will be added in `resultados_cluster/` and compared with
  this run.
