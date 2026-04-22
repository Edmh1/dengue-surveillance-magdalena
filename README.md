# Dengue-surveillance-magdalena

> End-to-end epidemiological surveillance pipeline for dengue in Magdalena, Colombia.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![MLflow](https://img.shields.io/badge/MLflow-experiment%20tracking-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-red)

---

## Overview

A modular, reproducible data pipeline and interactive dashboard for dengue
surveillance in the department of Magdalena, a permanently endemic region
of Colombia. The system ingests raw SIVIGILA microdata (INS event codes 210,
220, 580), applies the six-step cleaning protocol defined by INS (Protocol v7,
2024), and produces analysis-ready datasets for epidemiological modeling and
visualization.

Built as part of the CITES health observatory at Universidad del Magdalena,
this module is designed to be extensible to other notifiable diseases within
the same surveillance infrastructure.

---

## Key features

- INS-compliant data cleaning pipeline (completeness checks, deduplication
  and discard exclusion per Protocol v7)
- Endemic channel construction via Quartiles/Medians and Bortman (1999)
  methods in parallel
- Climate feature ingestion via NASA Power API (temperature, precipitation,
  humidity)
- Reproducible preprocessing pipeline with scikit-learn
- Systematic comparison of 6 model families with MLflow experiment tracking
- Model interpretability with SHAP for the selected production model
- Interactive Streamlit dashboard with exploratory analysis and forecasting
  module
- Containerized for institutional deployment via Docker

---

## Tech stack

| Layer | Technology |
|---|---|
| Data ingestion | pandas, python-calamine, pyarrow |
| Climate data | NASA Power API via requests |
| ML pipeline | scikit-learn, Pipelines |
| Experiment tracking | MLflow |
| Model interpretability | SHAP |
| Visualization | Streamlit, Plotly |
| Testing | pytes |
| Containerization | Docker |
| Version control | Git + GitHub |

---

## Models evaluated

All models are evaluated systematically in notebooks using the same metrics
(MAE, RMSE, MAPE, R²) and tracked with MLflow. The best-performing model
for Magdalena's endemic transmission pattern is then productionized in the
pipeline.

| Family | Models |
|---|---|
| Statistical | ARIMA, SARIMA, SARIMAX, Prophet |
| Gradient boosting | XGBoost, LightGBM |
| Deep learning | LSTM |

---

## Project structure
```
dengue-surveillance-magdalena/
|--- data/
|   |--- raw/          
|   |--- interim/      
|   |--- processed/    
|--- notebooks/
|   |--- 01_eda.ipynb           # exploratory data analysis
|   ├--- 02_stationarity.ipynb  # stationarity tests and time series analysis
|   |--- 03_modeling.ipynb      # model experimentation and comparison
|--- src/
|   |--- dengue/    # The system is built with a modular architecture, making it easily scalable and adaptable to other pathologies and medical use cases
|--- dashboard/
|   |--- app.py
|   |--- pages/
|   --- utils/
|--- tests/
|--- requirements.txt
--- README.md
```
---

## Data sources

- **SIVIGILA** - individual-level notification records
  (INS open data portal, event codes 210 / 220 / 580)
- **NASA Power API** - climate variables (temperature, precipitation,
  humidity) via HTTP requests
- **DANE** - municipal population projections

---

## Getting started

```
# clone the repository
git clone https://github.com/your-username/dengue-surveillance-magdalena.git
cd dengue-surveillance-magdalena

# create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

```

---

## Conclusion
> En construcción :)
