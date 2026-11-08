"""Puente entre los notebooks de produccion (06 y 07) y el codigo de pronostico
del tablero (pathologies/dengue/pronostico del repositorio
public-health-surveillance-system).

Todo lo que se entrena, evalua y exporta aqui pasa por las clases y funciones
del tablero: la serie (serie.construir_serie_semanal_departamental), los modelos
(catalogo), la prueba 85/15 (evaluacion.evaluar_en_prueba), las metricas
(evaluacion.metricas_desde_registros) y la exportacion (paquete). Este modulo
solo agrega lo que el tablero no necesita: la validacion cruzada dentro del
entrenamiento, el bloque de validacion de las redes, la prueba final en 2025 y
los espacios de busqueda de Optuna, restringidos a los hiperparametros que
acepta cada clase (hiperparametros_por_defecto).
"""

from __future__ import annotations

import copy
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from dengue.experimentacion import (
    H_MAX,
    CacheDePruebas,
    construir_registros,
    origenes_del_bloque,
)
from dengue.investigacion import REZAGOS_CANDIDATOS

VARIABLE_ENTORNO = "RUTA_TABLERO"
ARCHIVO_CONSOLIDADO = Path("data") / "dengue" / "consolidado" / "dengue_consolidado.parquet"

# 70/15/15: dentro del 85 % de entrenamiento, el 15 % del total es validacion.
FRACCION_VALIDACION_REDES = 0.15 / 0.85

PRUEBAS = {
    "arima": 30,
    "sarima": 25,
    "prophet_ar": 40,
    "xgboost": 80,
    "lightgbm": 80,
    "lstm": 30,
    "nbeats": 30,
}
PRUEBAS_RAPIDO = {clave: 3 for clave in PRUEBAS}

EPOCAS_MAXIMAS = 200
PACIENCIA = 20
EPOCAS_RAPIDO = 4
PACIENCIA_RAPIDO = 2


# ---------------------------------------------------------------------------
# Tablero
# ---------------------------------------------------------------------------

def preparar_tablero(ruta: str | Path | None = None) -> Path:
    """Resuelve la ruta del repositorio del tablero (argumento o variable de
    entorno RUTA_TABLERO), comprueba que tenga el codigo de pronostico y la
    agrega a sys.path para importarlo."""
    candidata = ruta or os.environ.get(VARIABLE_ENTORNO)
    if not candidata:
        raise ValueError(
            f"Define la ruta del repositorio del tablero en la celda de configuracion o en la "
            f"variable de entorno {VARIABLE_ENTORNO}."
        )
    ruta_tablero = Path(candidata).expanduser().resolve()
    if not (ruta_tablero / "pathologies" / "dengue" / "pronostico").is_dir():
        raise ValueError(f"{ruta_tablero} no tiene pathologies/dengue/pronostico: no es el repositorio del tablero.")
    if not (ruta_tablero / ARCHIVO_CONSOLIDADO).exists():
        raise ValueError(f"Falta el consolidado de dengue del tablero: {ruta_tablero / ARCHIVO_CONSOLIDADO}.")
    if str(ruta_tablero) not in sys.path:
        sys.path.insert(0, str(ruta_tablero))
    return ruta_tablero


def cargar_series(ruta_tablero: Path) -> dict[str, Any]:
    """Serie del tablero (2007 a 2025) y su recorte a 2007-2024."""
    from pathologies.dengue.pronostico.serie import construir_serie_semanal_departamental

    consolidado = pd.read_parquet(ruta_tablero / ARCHIVO_CONSOLIDADO)
    serie = construir_serie_semanal_departamental(consolidado)
    serie = serie[(serie["ano"] >= 2007) & (serie["ano"] <= 2025)].reset_index(drop=True)
    serie_2024 = serie[serie["ano"] <= 2024].reset_index(drop=True)
    return {"serie": serie, "serie_2024": serie_2024, "semanas_2024": len(serie_2024)}


def periodos(serie_2024: pd.DataFrame) -> dict[str, Any]:
    """Limites de los periodos de la metodologia (seccion 4) sobre la serie
    2007-2024, con la misma aritmetica que evaluar_en_prueba y entrenar_red."""
    from pathologies.dengue.pronostico.configuracion import FRACCION_PRUEBA

    n = len(serie_2024)
    semanas_prueba = int(round(n * FRACCION_PRUEBA))
    n85 = n - semanas_prueba
    semanas_validacion = int(round(n85 * FRACCION_VALIDACION_REDES))
    n70 = n85 - semanas_validacion
    fechas = pd.to_datetime(serie_2024["fecha_semana"])
    return {
        "semanas": n,
        "fin_entrenamiento": n85,
        "fin_ajuste_redes": n70,
        "fechas": {
            "inicio": fechas.iloc[0].strftime("%Y-%m-%d"),
            "inicio_validacion_redes": fechas.iloc[n70].strftime("%Y-%m-%d"),
            "inicio_prueba": fechas.iloc[n85].strftime("%Y-%m-%d"),
            "fin_prueba": fechas.iloc[n - 1].strftime("%Y-%m-%d"),
        },
    }


def clase_modelo(clave: str):
    from pathologies.dengue.pronostico import catalogo

    return catalogo.obtener_modelo(clave)


# ---------------------------------------------------------------------------
# Evaluaciones
# ---------------------------------------------------------------------------

def metricas(registros: pd.DataFrame) -> dict[str, Any]:
    from pathologies.dengue.pronostico import evaluacion

    return evaluacion.metricas_desde_registros(registros)


def evaluar_en_prueba(clase, hiperparametros: dict, serie_2024: pd.DataFrame) -> dict[str, Any]:
    """Prueba 85/15 del tablero: entrena con el 85 % y evalua el 15 % final."""
    from pathologies.dengue.pronostico import evaluacion

    resultado = evaluacion.evaluar_en_prueba(clase, copy.deepcopy(hiperparametros), serie_2024)
    resultado["metricas"] = evaluacion.metricas_desde_registros(resultado["registros"])
    return resultado


def evaluar_en_bloque(modelo, serie: pd.DataFrame, primera: int, ultima: int) -> pd.DataFrame:
    """Registros walk-forward del bloque [primera, ultima] con un modelo del
    tablero ya entrenado (pronosticar_trayectorias)."""
    serie_ordenada = serie.sort_values("fecha_semana").reset_index(drop=True)
    origenes = origenes_del_bloque(primera, ultima)
    trayectorias = modelo.pronosticar_trayectorias(serie_ordenada, origenes, H_MAX)
    fechas = list(pd.to_datetime(serie_ordenada["fecha_semana"]))
    return construir_registros(fechas, serie_ordenada["casos"].to_numpy(dtype=float), origenes, trayectorias,
                               primera, ultima)


def validacion_cruzada(clase, hiperparametros: dict, serie_entrenamiento: pd.DataFrame,
                       cortes: list[dict[str, int]]) -> dict[str, Any]:
    """Cada corte aplica evaluar_en_prueba del tablero a la serie que termina en
    el (entrena con su 85 % y evalua su 15 % final). Se promedia el RMSE global."""
    from pathologies.dengue.pronostico import evaluacion

    rmses, maes = [], []
    for corte in cortes:
        resultado = evaluacion.evaluar_en_prueba(clase, copy.deepcopy(hiperparametros),
                                                 serie_entrenamiento.iloc[:corte["largo"]])
        if resultado["semanas_entrenamiento"] != corte["inicio_bloque"]:
            raise RuntimeError("El corte no coincide con la particion de evaluar_en_prueba.")
        globales = evaluacion.metricas_desde_registros(resultado["registros"])["global"]["modelo"]
        rmses.append(globales["RMSE"])
        maes.append(globales["MAE"])
    return {"rmse": float(np.mean(rmses)), "mae": float(np.mean(maes)), "rmse_cortes": rmses, "mae_cortes": maes}


def evaluar_red_en_validacion(clase, hiperparametros: dict, serie_entrenamiento: pd.DataFrame) -> dict[str, Any]:
    """Entrena la red con el 85 % (el 70 % para ajustar y el 15 % final para la
    parada temprana) y evalua con el walk-forward ese mismo bloque de validacion."""
    modelo = clase(copy.deepcopy(hiperparametros))
    modelo.entrenar(serie_entrenamiento)
    n = len(serie_entrenamiento)
    fin_ajuste = n - int(round(n * modelo.hiperparametros["fraccion_validacion"]))
    registros = evaluar_en_bloque(modelo, serie_entrenamiento, fin_ajuste, n - 1)
    return {"registros": registros, "metricas": metricas(registros), "detalles": modelo.detalles_entrenamiento()}


def prueba_final(clase, hiperparametros: dict, serie: pd.DataFrame, semanas_2024: int) -> dict[str, Any]:
    """Entrena con 2007-2024 (modelo.entrenar) y pronostica desde cada origen
    hasta 6 semanas (modelo.pronosticar_trayectorias); conserva los registros
    cuya semana objetivo es de 2025."""
    modelo = clase(copy.deepcopy(hiperparametros))
    modelo.entrenar(serie.iloc[:semanas_2024].reset_index(drop=True))
    registros = evaluar_en_bloque(modelo, serie, semanas_2024, len(serie) - 1)
    return {"registros": registros, "metricas": metricas(registros), "detalles": modelo.detalles_entrenamiento()}


# ---------------------------------------------------------------------------
# Objetivos de Optuna
# ---------------------------------------------------------------------------

def objetivo_validacion_cruzada(clase, espacio: Callable, serie_entrenamiento: pd.DataFrame,
                                cortes: list[dict[str, int]], aic: Callable | None = None) -> Callable:
    cache = CacheDePruebas()

    def objetivo(trial):
        hiperparametros = espacio(trial)
        guardado = cache.buscar(trial.params)
        if guardado is not None:
            valor, atributos = guardado
            for clave, contenido in atributos.items():
                trial.set_user_attr(clave, contenido)
            trial.set_user_attr("repetida", True)
            return valor
        inicio = time.time()
        resultado = validacion_cruzada(clase, hiperparametros, serie_entrenamiento, cortes)
        atributos = {"mae": resultado["mae"], "rmse_cortes": resultado["rmse_cortes"],
                     "mae_cortes": resultado["mae_cortes"], "hiperparametros": hiperparametros}
        if aic is not None:
            atributos["aic"] = aic(hiperparametros)
        atributos["segundos"] = round(time.time() - inicio, 1)
        for clave, contenido in atributos.items():
            trial.set_user_attr(clave, contenido)
        cache.registrar(trial.params, resultado["rmse"], atributos)
        return resultado["rmse"]

    return objetivo


def objetivo_red(clase, espacio: Callable, serie_entrenamiento: pd.DataFrame, semillas: list[int]) -> Callable:
    """RMSE global (H1 a H6) medio de las semillas en el bloque de validacion,
    con poda por mediana despues de cada semilla."""
    import keras
    import optuna

    def objetivo(trial):
        hiperparametros = espacio(trial)
        rmses, maes, epocas = [], [], []
        inicio = time.time()
        for paso, semilla in enumerate(semillas):
            keras.backend.clear_session()
            resultado = evaluar_red_en_validacion(clase, {**hiperparametros, "semilla": semilla}, serie_entrenamiento)
            globales = resultado["metricas"]["global"]["modelo"]
            rmses.append(globales["RMSE"])
            maes.append(globales["MAE"])
            epocas.append(resultado["detalles"].get("epocas_ejecutadas"))
            trial.report(float(np.mean(rmses)), paso)
            if paso < len(semillas) - 1 and trial.should_prune():
                trial.set_user_attr("rmse_semillas", rmses)
                raise optuna.TrialPruned()
        sd = float(np.std(rmses, ddof=1)) if len(rmses) > 1 else 0.0
        for clave, contenido in {
            "rmse_media": float(np.mean(rmses)), "rmse_sd": sd, "mae": float(np.mean(maes)),
            "rmse_semillas": rmses, "mae_semillas": maes, "epocas": epocas,
            "hiperparametros": hiperparametros, "segundos": round(time.time() - inicio, 1),
        }.items():
            trial.set_user_attr(clave, contenido)
        return float(np.mean(rmses))

    return objetivo


# ---------------------------------------------------------------------------
# Espacios de busqueda (solo hiperparametros que aceptan las clases del tablero)
# ---------------------------------------------------------------------------

def _tendencia(d: int) -> str:
    """Con d = 0 el modelo necesita una constante (nivel medio de log1p(casos));
    con d = 1 statsmodels no admite constante y no hace falta."""
    return "c" if d == 0 else "n"


def espacio_arima(trial, D: int = 0) -> dict[str, Any]:
    d = trial.suggest_int("d", 0, 1)
    return {"orden": [trial.suggest_int("p", 0, 6), d, trial.suggest_int("q", 0, 4)],
            "orden_estacional": [0, 0, 0, 0], "tendencia": _tendencia(d)}


ESTRUCTURAS_ESTACIONALES = {"AR": (1, 0), "MA": (0, 1), "ARMA": (1, 1)}


def espacio_sarima(trial, D: int = 0) -> dict[str, Any]:
    """SARIMA con un termino estacional real (P + Q >= 1); con P = Q = 0 seria
    el mismo modelo que ARIMA."""
    d = trial.suggest_int("d", 0, 1)
    P, Q = ESTRUCTURAS_ESTACIONALES[trial.suggest_categorical("estructura_estacional", list(ESTRUCTURAS_ESTACIONALES))]
    return {"orden": [trial.suggest_int("p", 0, 4), d, trial.suggest_int("q", 0, 3)],
            "orden_estacional": [P, D, Q, 52], "tendencia": _tendencia(d)}


def espacio_prophet_ar(trial) -> dict[str, Any]:
    return {
        "rezagos": REZAGOS_CANDIDATOS[trial.suggest_categorical("rezagos", list(REZAGOS_CANDIDATOS))],
        # Prophet acepta un entero en yearly_seasonality: es el orden de Fourier.
        "estacionalidad_anual": trial.suggest_int("orden_fourier", 3, 20),
        "modo_estacionalidad": trial.suggest_categorical("modo_estacionalidad", ["additive", "multiplicative"]),
        "changepoint_prior_scale": trial.suggest_float("changepoint_prior_scale", 1e-3, 0.5, log=True),
        "seasonality_prior_scale": trial.suggest_float("seasonality_prior_scale", 1e-2, 10.0, log=True),
    }


def _espacio_arbol(trial) -> dict[str, Any]:
    return {
        "rezagos": REZAGOS_CANDIDATOS[trial.suggest_categorical("rezagos", list(REZAGOS_CANDIDATOS))],
        "transformacion": trial.suggest_categorical("transformacion", ["ninguna", "log1p"]),
        "n_estimators": trial.suggest_int("n_estimators", 100, 1500, log=True),
        "learning_rate": trial.suggest_float("learning_rate", 5e-3, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 100.0, log=True),
        "random_state": 42,
    }


def espacio_xgboost(trial) -> dict[str, Any]:
    hp = _espacio_arbol(trial)
    hp["max_depth"] = trial.suggest_int("max_depth", 2, 8)
    hp["min_child_weight"] = trial.suggest_float("min_child_weight", 0.5, 50.0, log=True)
    return hp


def espacio_lightgbm(trial) -> dict[str, Any]:
    hp = _espacio_arbol(trial)
    hp["num_leaves"] = trial.suggest_int("num_leaves", 4, 64, log=True)
    hp["min_child_samples"] = trial.suggest_int("min_child_samples", 5, 80, log=True)
    hp["subsample_freq"] = 1
    return hp


def fijos_redes(modo_rapido: bool) -> dict[str, Any]:
    return {
        "epocas_maximas": EPOCAS_RAPIDO if modo_rapido else EPOCAS_MAXIMAS,
        "paciencia": PACIENCIA_RAPIDO if modo_rapido else PACIENCIA,
        "fraccion_validacion": FRACCION_VALIDACION_REDES,
    }


def espacio_lstm(trial, modo_rapido: bool = False) -> dict[str, Any]:
    capas = trial.suggest_int("capas", 1, 3)
    unidades = [trial.suggest_int(f"unidades_capa{k + 1}", 8, 128, log=True) for k in range(capas)]
    nombre_optimizador = trial.suggest_categorical("optimizador", ["adam", "rmsprop"])
    tasa = trial.suggest_float("tasa_aprendizaje", 1e-4, 1e-2, log=True)
    clase_keras = {"adam": "Adam", "rmsprop": "RMSprop"}[nombre_optimizador]
    return {
        "ventana_semanas": trial.suggest_int("ventana_semanas", 6, 52),
        "unidades": unidades,
        "dropout": trial.suggest_float("dropout", 0.0, 0.5),
        # La clase del tablero pasa optimizador a compile(); Keras acepta la
        # configuracion serializada, que lleva la tasa de aprendizaje.
        "optimizador": {"class_name": clase_keras, "config": {"learning_rate": tasa}},
        "batch_size": 2 ** trial.suggest_int("log2_batch_size", 3, 6),
        "paciencia_tasa_aprendizaje": PACIENCIA_RAPIDO if modo_rapido else 10,
        **fijos_redes(modo_rapido),
    }


def espacio_nbeats(trial, modo_rapido: bool = False) -> dict[str, Any]:
    return {
        "ventana_semanas": trial.suggest_int("ventana_semanas", 6, 52),
        "num_pilas": trial.suggest_int("num_pilas", 2, 30, log=True),
        "bloques_por_pila": trial.suggest_int("bloques_por_pila", 1, 2),
        "capas_por_bloque": trial.suggest_int("capas_por_bloque", 1, 4),
        "ancho_capa": trial.suggest_int("ancho_capa", 32, 256, log=True),
        "dropout": trial.suggest_float("dropout", 0.0, 0.5),
        "tasa_aprendizaje": trial.suggest_float("tasa_aprendizaje", 1e-4, 1e-2, log=True),
        "batch_size": 2 ** trial.suggest_int("log2_batch_size", 3, 6),
        **fijos_redes(modo_rapido),
    }


def aic_arima(serie_entrenamiento: pd.DataFrame) -> Callable[[dict], float | None]:
    """AIC de una configuracion de ARIMA o SARIMA ajustada con el 85 % (se
    registra como referencia, no decide)."""
    import warnings

    from statsmodels.tsa.arima.model import ARIMA

    casos_log = np.log1p(serie_entrenamiento.sort_values("fecha_semana")["casos"].to_numpy(dtype=float))

    def calcular(hp: dict) -> float | None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ajuste = ARIMA(casos_log, order=tuple(hp["orden"]), seasonal_order=tuple(hp["orden_estacional"]),
                               trend=hp.get("tendencia", "n"), enforce_stationarity=False,
                               enforce_invertibility=False).fit()
            return float(ajuste.aic)
        except Exception:
            return None

    return calcular
