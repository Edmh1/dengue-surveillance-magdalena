"""Modelos de la investigacion (notebooks 03 y 05), con y sin clima.

Cada modelo sigue el mismo contrato que los del tablero:
- entrenar(df, fin, fin_ajuste=None): aprende con las filas [0, fin). Las redes
  usan [fin_ajuste, fin) como validacion para la parada temprana.
- trayectorias(df, origenes): desde cada origen recibe los casos reales hasta el
  origen y pronostica H_MAX semanas de forma recursiva (las entradas que caen
  dentro del horizonte se completan con la propia prediccion). Devuelve la
  matriz (origenes x H_MAX) en casos.

El clima entra como covariable observada: en el pronostico multipaso se usan
sus valores reales, tambien dentro del horizonte (supuesto favorable al clima,
que aisla la perdida de la senal autorregresiva).

Los espacios de busqueda y el numero de pruebas estan definidos aqui una sola
vez, asi que las versiones con clima (03) y sin clima (05) de cada familia usan
exactamente el mismo espacio y el mismo presupuesto.
"""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from dengue.experimentacion import (
    H_MAX,
    CacheDePruebas,
    calcular_metricas,
    construir_registros,
    origenes_del_bloque,
)

LAGS_CLIMA = [4, 8, 12, 16]
REZAGOS_REFERENCIA = [1, 2, 4, 8]
REZAGOS_CANDIDATOS = {
    "1-2-4-8": [1, 2, 4, 8],
    "1-2-3-4": [1, 2, 3, 4],
    "1-2-3-4-8": [1, 2, 3, 4, 8],
    "1-2-4-8-12": [1, 2, 4, 8, 12],
    "1-2-3-4-6-8": [1, 2, 3, 4, 6, 8],
    "1-2-4-8-16": [1, 2, 4, 8, 16],
}
PERIODO_ESTACIONAL = 52

# Pruebas de Optuna por modelo (modo completo y modo rapido). Justificacion en
# los notebooks: el presupuesto crece con el tamano del espacio y baja con el
# costo de cada prueba.
PRUEBAS = {
    "arima": 30,
    "sarima": 25,
    "prophet": 40,
    "xgboost": 80,
    "lightgbm": 80,
    "lstm": 20,
    "nbeats": 20,
}
PRUEBAS_RAPIDO = {clave: 3 for clave in PRUEBAS}

EPOCAS_MAXIMAS = 200
PACIENCIA = 20
PACIENCIA_TASA = 10
EPOCAS_RAPIDO = 4
PACIENCIA_RAPIDO = 2


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def historial_inicial(valores: np.ndarray, origenes: list[int], largo: int, horizonte: int) -> np.ndarray:
    """Igual que recursivo.historial_inicial del tablero: una fila por origen; la
    columna j es la posicion (origen - largo + j); las ultimas horizonte columnas
    se llenan con las predicciones."""
    historial = np.full((len(origenes), largo + 1 + horizonte), np.nan)
    for fila, origen in enumerate(origenes):
        historial[fila, :largo + 1] = valores[origen - largo:origen + 1]
    return historial


def _transformar(valores: np.ndarray, transformacion: str) -> np.ndarray:
    return np.log1p(valores) if transformacion == "log1p" else valores


def _destransformar(valores: np.ndarray, transformacion: str) -> np.ndarray:
    return np.expm1(valores) if transformacion == "log1p" else valores


def _serie_climatica(df: pd.DataFrame, variable: str) -> pd.Series:
    """Variable climatica con su transformacion: precipitacion_log = log1p,
    sufijo _diff = primera diferencia, resto en su escala."""
    if variable == "precipitacion_log":
        return np.log1p(df["precipitacion"].astype(float))
    if variable.endswith("_diff"):
        return df[variable.replace("_diff", "")].astype(float).diff()
    return df[variable].astype(float)


def matriz_clima_rezagada(df: pd.DataFrame, variables: list[str], lags: list[int] = LAGS_CLIMA) -> tuple[np.ndarray, list[str]]:
    """Columna por variable y rezago, alineada con la fila objetivo: la fila t
    tiene el clima de t - lag. Se agregan H_MAX filas al final repitiendo la
    ultima (solo afectan semanas objetivo fuera de la serie, que se descartan)."""
    if not variables:
        return np.empty((len(df) + H_MAX, 0)), []
    columnas, nombres = [], []
    for variable in variables:
        base = _serie_climatica(df, variable)
        for lag in lags:
            columnas.append(base.shift(lag).to_numpy(dtype=float))
            nombres.append(f"{variable}_lag{lag}")
    matriz = np.column_stack(columnas)
    relleno = np.repeat(matriz[-1:, :], H_MAX, axis=0)
    return np.vstack([matriz, relleno]), nombres


def silenciar_prophet() -> None:
    """cmdstanpy configura su propio registro al importarse: se importa aqui y se
    baja despues."""
    import logging

    import cmdstanpy  # noqa: F401

    for nombre in ("cmdstanpy", "prophet", "prophet.plot"):
        registro = logging.getLogger(nombre)
        registro.setLevel(logging.ERROR)
        for manejador in registro.handlers:
            manejador.setLevel(logging.ERROR)


def silenciar_lightning() -> None:
    """PyTorch Lightning configura su registro al importarse e informa cada
    entrenamiento (GPU disponible, epocas alcanzadas): se baja a errores."""
    import logging

    for nombre in ("lightning", "lightning.pytorch", "pytorch_lightning", "lightning.fabric", "darts"):
        registro = logging.getLogger(nombre)
        registro.setLevel(logging.ERROR)
        for manejador in registro.handlers:
            manejador.setLevel(logging.ERROR)
    for nombre in list(logging.Logger.manager.loggerDict):
        if nombre.startswith(("lightning", "pytorch_lightning", "darts")):
            logging.getLogger(nombre).setLevel(logging.ERROR)


def _fechas_futuras(fechas: list, origenes: list[int], paso: int) -> list[pd.Timestamp]:
    return [pd.Timestamp(fechas[o]) + pd.Timedelta(weeks=paso) for o in origenes]


# ---------------------------------------------------------------------------
# Modelos estadisticos
# ---------------------------------------------------------------------------

class SarimaxInv:
    """ARIMA, SARIMA o SARIMAX sobre log1p(casos). motor='arima' usa la clase
    ARIMA de statsmodels (sin exogenas); motor='sarimax' usa SARIMAX (con las
    exogenas climaticas rezagadas). Para pronosticar desde un origen se aplica el
    filtro de Kalman con los parametros estimados, sin volver a estimarlos."""

    familia = "estadistico"

    def __init__(self, orden, orden_estacional=(0, 0, 0, 0), exogenas: list[str] | None = None, motor: str = "arima",
                 tendencia: str | None = None):
        self.orden = tuple(int(v) for v in orden)
        self.orden_estacional = tuple(int(v) for v in orden_estacional)
        self.exogenas = list(exogenas or [])
        self.motor = motor
        self.tendencia = tendencia if tendencia is not None else _tendencia(self.orden[1])
        self.ajuste = None
        self.aic = None

    @classmethod
    def desde_hiperparametros(cls, hp: dict[str, Any], exogenas: list[str] | None = None, motor: str = "arima"):
        return cls(hp["orden"], hp["orden_estacional"], exogenas=exogenas, motor=motor, tendencia=hp.get("tendencia"))

    def _preparar(self, df: pd.DataFrame):
        y = np.log1p(df["casos"].to_numpy(dtype=float))
        X, _ = matriz_clima_rezagada(df, self.exogenas)
        inicio = 0
        if X.shape[1]:
            completas = ~np.isnan(X[:len(df)]).any(axis=1)
            inicio = int(np.argmax(completas))
        return y, (X if X.shape[1] else None), inicio

    def _modelo(self, y, X):
        if self.motor == "sarimax":
            from statsmodels.tsa.statespace.sarimax import SARIMAX

            return SARIMAX(y, exog=X, order=self.orden, seasonal_order=self.orden_estacional, trend=self.tendencia,
                           enforce_stationarity=False, enforce_invertibility=False)
        from statsmodels.tsa.arima.model import ARIMA

        return ARIMA(y, exog=X, order=self.orden, seasonal_order=self.orden_estacional, trend=self.tendencia,
                     enforce_stationarity=False, enforce_invertibility=False)

    def entrenar(self, df: pd.DataFrame, fin: int, fin_ajuste: int | None = None) -> None:
        y, X, inicio = self._preparar(df)
        self.inicio = inicio
        exog = X[inicio:fin] if X is not None else None
        modelo = self._modelo(y[inicio:fin], exog)
        self.ajuste = modelo.fit(disp=False) if self.motor == "sarimax" else modelo.fit()
        self.aic = float(self.ajuste.aic)

    def trayectorias(self, df: pd.DataFrame, origenes: list[int]) -> np.ndarray:
        y, X, inicio = self._preparar(df)
        salida = np.zeros((len(origenes), H_MAX))
        for fila, origen in enumerate(origenes):
            exog_hist = X[inicio:origen + 1] if X is not None else None
            filtrado = self.ajuste.apply(y[inicio:origen + 1], exog=exog_hist, refit=False)
            exog_fut = X[origen + 1:origen + 1 + H_MAX] if X is not None else None
            pronostico = np.asarray(filtrado.forecast(steps=H_MAX, exog=exog_fut), dtype=float)
            salida[fila] = np.maximum(np.expm1(pronostico), 0.0)
        return salida

    def hiperparametros(self) -> dict[str, Any]:
        return {"orden": list(self.orden), "orden_estacional": list(self.orden_estacional),
                "tendencia": self.tendencia, "exogenas": self.exogenas}


class ProphetInv:
    """Prophet con estacionalidad anual (orden de Fourier ajustable), rezagos de
    log1p(casos) como regresores (Prophet-AR) y, opcionalmente, clima rezagado."""

    familia = "estadistico"

    def __init__(self, hp: dict[str, Any] | None = None, clima: list[str] | None = None, usar_ar: bool = True):
        base = {
            "rezagos": list(REZAGOS_REFERENCIA),
            "orden_fourier": 10,
            "modo_estacionalidad": "additive",
            "changepoint_prior_scale": 0.05,
            "seasonality_prior_scale": 10.0,
        }
        base.update(hp or {})
        self.hp = base
        self.clima = list(clima or [])
        self.usar_ar = usar_ar
        self.modelo = None

    def _rezagos(self) -> list[int]:
        return list(self.hp["rezagos"]) if self.usar_ar else []

    def _inicio(self) -> int:
        inicio = max(self._rezagos(), default=0)
        if self.clima:
            inicio = max(inicio, max(LAGS_CLIMA) + 1)
        return inicio

    def entrenar(self, df: pd.DataFrame, fin: int, fin_ajuste: int | None = None) -> None:
        from prophet import Prophet

        silenciar_prophet()
        casos_log = np.log1p(df["casos"].to_numpy(dtype=float))
        clima, nombres = matriz_clima_rezagada(df, self.clima)
        filas = np.arange(self._inicio(), fin)
        datos = pd.DataFrame({"ds": pd.to_datetime(df["fecha_semana"].to_numpy()[filas]), "y": casos_log[filas]})
        for rezago in self._rezagos():
            datos[f"casos_lag{rezago}_log"] = casos_log[filas - rezago]
        for j, nombre in enumerate(nombres):
            datos[nombre] = clima[filas, j]
        modelo = Prophet(
            yearly_seasonality=int(self.hp["orden_fourier"]),
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode=self.hp["modo_estacionalidad"],
            changepoint_prior_scale=float(self.hp["changepoint_prior_scale"]),
            seasonality_prior_scale=float(self.hp["seasonality_prior_scale"]),
        )
        self.regresores = [c for c in datos.columns if c not in ("ds", "y")]
        for columna in self.regresores:
            modelo.add_regressor(columna)
        modelo.fit(datos)
        self.modelo = modelo

    def trayectorias(self, df: pd.DataFrame, origenes: list[int]) -> np.ndarray:
        casos_log = np.log1p(df["casos"].to_numpy(dtype=float))
        fechas = list(pd.to_datetime(df["fecha_semana"]))
        clima, nombres = matriz_clima_rezagada(df, self.clima)
        rezagos = self._rezagos()
        largo = max(rezagos, default=0)
        historial = historial_inicial(casos_log, origenes, largo, H_MAX)
        origenes_arr = np.asarray(origenes)
        salida = np.zeros((len(origenes), H_MAX))
        for paso in range(1, H_MAX + 1):
            columna = largo + paso
            fechas_obj = _fechas_futuras(fechas, origenes, paso)
            entrada = pd.DataFrame({"ds": fechas_obj})
            for rezago in rezagos:
                entrada[f"casos_lag{rezago}_log"] = historial[:, columna - rezago]
            for j, nombre in enumerate(nombres):
                entrada[nombre] = clima[origenes_arr + paso, j]
            prediccion = self.modelo.predict(entrada)
            yhat = prediccion.set_index("ds")["yhat"].reindex(pd.DatetimeIndex(fechas_obj)).to_numpy()
            yhat = np.maximum(yhat, 0.0)
            historial[:, columna] = yhat
            salida[:, paso - 1] = np.expm1(yhat)
        return salida

    def hiperparametros(self) -> dict[str, Any]:
        return {**self.hp, "clima": self.clima, "usar_ar": self.usar_ar}


# ---------------------------------------------------------------------------
# Arboles (XGBoost y LightGBM)
# ---------------------------------------------------------------------------

_PARAMETROS_ARBOL = {
    "xgboost": ("n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree",
                "reg_alpha", "reg_lambda", "min_child_weight"),
    "lightgbm": ("n_estimators", "num_leaves", "learning_rate", "subsample", "colsample_bytree",
                 "reg_alpha", "reg_lambda", "min_child_samples"),
}


class ArbolInv:
    """XGBoost o LightGBM sobre rezagos de casos (en escala original o log1p) y,
    opcionalmente, clima rezagado 4, 8, 12 y 16 semanas."""

    familia = "aprendizaje_automatico"

    def __init__(self, tipo: str, hp: dict[str, Any], clima: list[str] | None = None):
        self.tipo = tipo
        self.hp = dict(hp)
        self.clima = list(clima or [])
        self.modelo = None

    def _rezagos(self) -> list[int]:
        return list(self.hp.get("rezagos", REZAGOS_REFERENCIA))

    def _estimador(self):
        parametros = {k: self.hp[k] for k in _PARAMETROS_ARBOL[self.tipo] if k in self.hp}
        if self.tipo == "xgboost":
            from xgboost import XGBRegressor

            return XGBRegressor(random_state=42, n_jobs=1, importance_type="gain", **parametros)
        from lightgbm import LGBMRegressor

        return LGBMRegressor(random_state=42, n_jobs=1, verbose=-1, subsample_freq=1,
                             importance_type="gain", **parametros)

    def entrenar(self, df: pd.DataFrame, fin: int, fin_ajuste: int | None = None) -> None:
        transformacion = self.hp.get("transformacion", "ninguna")
        valores = _transformar(df["casos"].to_numpy(dtype=float), transformacion)
        clima, nombres_clima = matriz_clima_rezagada(df, self.clima)
        rezagos = self._rezagos()
        inicio = max(max(rezagos), max(LAGS_CLIMA) if self.clima else 0)
        filas = np.arange(inicio, fin)
        columnas = [valores[filas - r] for r in rezagos] + [clima[filas, j] for j in range(len(nombres_clima))]
        X = pd.DataFrame(np.column_stack(columnas), columns=[f"casos_lag{r}" for r in rezagos] + nombres_clima)
        self.columnas = list(X.columns)
        self.modelo = self._estimador()
        self.modelo.fit(X, valores[filas])

    def trayectorias(self, df: pd.DataFrame, origenes: list[int]) -> np.ndarray:
        transformacion = self.hp.get("transformacion", "ninguna")
        valores = _transformar(df["casos"].to_numpy(dtype=float), transformacion)
        clima, _ = matriz_clima_rezagada(df, self.clima)
        rezagos = self._rezagos()
        largo = max(rezagos)
        historial = historial_inicial(valores, origenes, largo, H_MAX)
        origenes_arr = np.asarray(origenes)
        salida = np.zeros((len(origenes), H_MAX))
        for paso in range(1, H_MAX + 1):
            columna = largo + paso
            columnas = [historial[:, columna - r] for r in rezagos]
            columnas += [clima[origenes_arr + paso, j] for j in range(clima.shape[1])]
            X = pd.DataFrame(np.column_stack(columnas), columns=self.columnas)
            prediccion = np.maximum(np.asarray(self.modelo.predict(X), dtype=float), 0.0)
            historial[:, columna] = prediccion
            salida[:, paso - 1] = prediccion
        return np.maximum(_destransformar(salida, transformacion), 0.0)

    def importancias(self) -> pd.Series:
        return pd.Series(self.modelo.feature_importances_, index=self.columnas).sort_values(ascending=False)

    def hiperparametros(self) -> dict[str, Any]:
        return {**self.hp, "clima": self.clima}


# ---------------------------------------------------------------------------
# Redes
# ---------------------------------------------------------------------------

def _matriz_red(df: pd.DataFrame, clima: list[str]) -> np.ndarray:
    columnas = [np.log1p(df["casos"].to_numpy(dtype=float))]
    for variable in clima:
        columnas.append(df[variable].to_numpy(dtype=float))
    return np.column_stack(columnas)


class LstmInv:
    """LSTM en Keras sobre una ventana de log1p(casos) y, opcionalmente, clima.
    Escalado min-max ajustado solo con [0, fin_ajuste); parada temprana sobre la
    validacion restaurando los mejores pesos y tasa de aprendizaje a la mitad
    cuando se estanca."""

    familia = "aprendizaje_profundo"

    def __init__(self, hp: dict[str, Any], clima: list[str] | None = None, semilla: int = 42,
                 epocas: int = EPOCAS_MAXIMAS, paciencia: int = PACIENCIA, paciencia_tasa: int = PACIENCIA_TASA):
        self.hp = dict(hp)
        self.clima = list(clima or [])
        self.semilla = int(semilla)
        self.epocas = epocas
        self.paciencia = paciencia
        self.paciencia_tasa = paciencia_tasa
        self.red = None
        self.detalles: dict[str, Any] = {}

    def _construir(self, n_variables: int):
        import keras

        ventana = int(self.hp["ventana"])
        unidades = list(self.hp["unidades"])
        capas = [keras.Input(shape=(ventana, n_variables))]
        for posicion, cantidad in enumerate(unidades):
            capas.append(keras.layers.LSTM(int(cantidad), activation="tanh",
                                           return_sequences=posicion < len(unidades) - 1))
            if self.hp["dropout"] > 0:
                capas.append(keras.layers.Dropout(float(self.hp["dropout"])))
        capas.append(keras.layers.Dense(1))
        red = keras.Sequential(capas)
        optimizadores = {"adam": keras.optimizers.Adam, "rmsprop": keras.optimizers.RMSprop}
        optimizador = optimizadores[self.hp["optimizador"]](learning_rate=float(self.hp["tasa_aprendizaje"]))
        red.compile(optimizer=optimizador, loss="mean_absolute_error")
        return red

    def entrenar(self, df: pd.DataFrame, fin: int, fin_ajuste: int | None = None) -> None:
        import keras

        from dengue.experimentacion import fijar_semilla_tensorflow

        datos = _matriz_red(df, self.clima)
        self.minimo = datos[:fin_ajuste].min(axis=0)
        self.amplitud = np.where(datos[:fin_ajuste].max(axis=0) - self.minimo == 0, 1.0,
                                 datos[:fin_ajuste].max(axis=0) - self.minimo)
        escalados = (datos - self.minimo) / self.amplitud
        ventana = int(self.hp["ventana"])
        objetivos = np.arange(ventana, fin)
        X = np.stack([escalados[t - ventana:t] for t in objetivos]).astype("float32")
        y = escalados[objetivos, 0].astype("float32")
        es_validacion = objetivos >= fin_ajuste

        keras.backend.clear_session()
        fijar_semilla_tensorflow(self.semilla)
        self.red = self._construir(datos.shape[1])
        callbacks = [
            keras.callbacks.EarlyStopping(monitor="val_loss", patience=self.paciencia, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=self.paciencia_tasa, min_lr=1e-5),
        ]
        historia = self.red.fit(
            X[~es_validacion], y[~es_validacion],
            validation_data=(X[es_validacion], y[es_validacion]),
            epochs=self.epocas, batch_size=int(self.hp["batch_size"]), callbacks=callbacks, verbose=0,
        )
        perdidas = historia.history["val_loss"]
        self.historia = historia.history
        self.detalles = {"epocas_ejecutadas": len(perdidas), "mejor_epoca": int(np.argmin(perdidas)) + 1}

    def trayectorias(self, df: pd.DataFrame, origenes: list[int]) -> np.ndarray:
        datos = _matriz_red(df, self.clima)
        escalados = (datos - self.minimo) / self.amplitud
        escalados = np.vstack([escalados, np.repeat(escalados[-1:], H_MAX, axis=0)])
        ventana = int(self.hp["ventana"])
        origenes_arr = np.asarray(origenes)
        entradas = np.stack([escalados[o - ventana + 1:o + 1] for o in origenes]).astype("float32")
        salida = np.zeros((len(origenes), H_MAX))
        for paso in range(1, H_MAX + 1):
            prediccion = np.asarray(self.red(entradas, training=False)).reshape(-1)
            prediccion_log = np.maximum(prediccion * self.amplitud[0] + self.minimo[0], 0.0)
            salida[:, paso - 1] = np.expm1(prediccion_log)
            nueva = escalados[origenes_arr + paso].copy()
            nueva[:, 0] = (prediccion_log - self.minimo[0]) / self.amplitud[0]
            entradas = np.concatenate([entradas[:, 1:, :], nueva[:, None, :].astype("float32")], axis=1)
        return salida

    def hiperparametros(self) -> dict[str, Any]:
        return {**self.hp, "clima": self.clima}


class NBeatsInv:
    """N-BEATS generico de darts sobre log1p(casos), con clima escalado como
    past_covariates opcional. Salida de una semana y pronostico recursivo
    (output_chunk_length=1). Parada temprana sobre la validacion y se restauran
    los pesos de la mejor epoca desde el checkpoint."""

    familia = "aprendizaje_profundo"

    def __init__(self, hp: dict[str, Any], clima: list[str] | None = None, semilla: int = 42,
                 epocas: int = EPOCAS_MAXIMAS, paciencia: int = PACIENCIA):
        self.hp = dict(hp)
        self.clima = list(clima or [])
        self.semilla = int(semilla)
        self.epocas = epocas
        self.paciencia = paciencia
        self.modelo = None
        self.detalles: dict[str, Any] = {}

    def _series(self, df: pd.DataFrame, fin_ajuste: int):
        from darts import TimeSeries

        fechas = pd.DatetimeIndex(pd.to_datetime(df["fecha_semana"]))
        y = pd.Series(np.log1p(df["casos"].to_numpy(dtype=float)).astype("float32"), index=fechas)
        serie = TimeSeries.from_series(y, freq="W-SUN")
        covariables = None
        if self.clima:
            datos = df[self.clima].to_numpy(dtype=float)
            minimo = datos[:fin_ajuste].min(axis=0)
            amplitud = np.where(datos[:fin_ajuste].max(axis=0) - minimo == 0, 1.0, datos[:fin_ajuste].max(axis=0) - minimo)
            escalados = (datos - minimo) / amplitud
            escalados = np.vstack([escalados, np.repeat(escalados[-1:], H_MAX, axis=0)])
            indice = pd.date_range(fechas[0], periods=len(escalados), freq="W-SUN")
            covariables = TimeSeries.from_dataframe(
                pd.DataFrame(escalados.astype("float32"), index=indice, columns=self.clima), freq="W-SUN")
        return serie, covariables

    def entrenar(self, df: pd.DataFrame, fin: int, fin_ajuste: int | None = None) -> None:
        import torch
        from darts.models import NBEATSModel
        from pytorch_lightning.callbacks import EarlyStopping

        silenciar_lightning()
        serie, covariables = self._series(df, fin_ajuste)
        self._fin_ajuste = fin_ajuste
        ventana = int(self.hp["ventana"])
        self._carpeta = Path(tempfile.mkdtemp(prefix="nbeats_"))
        nombre = "nbeats"
        parada = EarlyStopping(monitor="val_loss", patience=self.paciencia, min_delta=1e-5, mode="min")
        acelerador = "gpu" if torch.cuda.is_available() else "cpu"
        modelo = NBEATSModel(
            input_chunk_length=ventana,
            output_chunk_length=1,
            generic_architecture=True,
            num_stacks=int(self.hp["num_pilas"]),
            num_blocks=int(self.hp["num_bloques"]),
            num_layers=int(self.hp["num_capas"]),
            layer_widths=int(self.hp["ancho_capa"]),
            dropout=float(self.hp["dropout"]),
            batch_size=int(self.hp["batch_size"]),
            n_epochs=self.epocas,
            optimizer_kwargs={"lr": float(self.hp["tasa_aprendizaje"])},
            random_state=self.semilla,
            model_name=nombre,
            work_dir=str(self._carpeta),
            save_checkpoints=True,
            force_reset=True,
            pl_trainer_kwargs={
                "accelerator": acelerador,
                "devices": 1,
                "callbacks": [parada],
                "enable_progress_bar": False,
                "enable_model_summary": False,
                "logger": False,
            },
        )
        entrenamiento = serie[:fin_ajuste]
        validacion = serie[fin_ajuste - ventana:fin]
        argumentos = {}
        if covariables is not None:
            argumentos = {"past_covariates": covariables, "val_past_covariates": covariables}
        modelo.fit(entrenamiento, val_series=validacion, verbose=False, **argumentos)
        epocas = int(modelo.epochs_trained)
        self.modelo = NBEATSModel.load_from_checkpoint(nombre, work_dir=str(self._carpeta), best=True)
        self.detalles = {"epocas_ejecutadas": epocas}

    def trayectorias(self, df: pd.DataFrame, origenes: list[int]) -> np.ndarray:
        serie, covariables = self._series(df, self._fin_ajuste)
        series = [serie[:o + 1] for o in origenes]
        argumentos = {}
        if covariables is not None:
            argumentos = {"past_covariates": [covariables] * len(series)}
        silenciar_lightning()
        pronosticos = self.modelo.predict(n=H_MAX, series=series, verbose=False, show_warnings=False, **argumentos)
        salida = np.vstack([np.asarray(p.values(), dtype=float).reshape(-1)[:H_MAX] for p in pronosticos])
        return np.maximum(np.expm1(salida), 0.0)

    def limpiar(self) -> None:
        if getattr(self, "_carpeta", None) is not None:
            shutil.rmtree(self._carpeta, ignore_errors=True)

    def hiperparametros(self) -> dict[str, Any]:
        return {**self.hp, "clima": self.clima}


# ---------------------------------------------------------------------------
# Espacios de busqueda (iguales con y sin clima)
# ---------------------------------------------------------------------------

def _tendencia(d: int) -> str:
    """Con d = 0 el modelo lleva constante (nivel medio de log1p(casos))."""
    return "c" if d == 0 else "n"


def espacio_arima(trial, D: int = 0) -> dict[str, Any]:
    d = trial.suggest_int("d", 0, 1)
    return {"orden": [trial.suggest_int("p", 0, 6), d, trial.suggest_int("q", 0, 4)],
            "orden_estacional": [0, 0, 0, 0], "tendencia": _tendencia(d)}


def espacio_sarima(trial, D: int = 0) -> dict[str, Any]:
    """Espacio del SARIMA de la investigacion: incluye P = Q = 0, asi que el
    estudio puede quedarse sin termino estacional si la validacion lo prefiere."""
    d = trial.suggest_int("d", 0, 1)
    orden = [trial.suggest_int("p", 0, 4), d, trial.suggest_int("q", 0, 3)]
    estacional = [trial.suggest_int("P", 0, 1), D, trial.suggest_int("Q", 0, 1), PERIODO_ESTACIONAL]
    return {"orden": orden, "orden_estacional": estacional, "tendencia": _tendencia(d)}


def espacio_prophet(trial) -> dict[str, Any]:
    return {
        "rezagos": REZAGOS_CANDIDATOS[trial.suggest_categorical("rezagos", list(REZAGOS_CANDIDATOS))],
        "orden_fourier": trial.suggest_int("orden_fourier", 3, 20),
        "modo_estacionalidad": trial.suggest_categorical("modo_estacionalidad", ["additive", "multiplicative"]),
        "changepoint_prior_scale": trial.suggest_float("changepoint_prior_scale", 1e-3, 0.5, log=True),
        "seasonality_prior_scale": trial.suggest_float("seasonality_prior_scale", 1e-2, 10.0, log=True),
    }


def _espacio_arbol_comun(trial) -> dict[str, Any]:
    return {
        "rezagos": REZAGOS_CANDIDATOS[trial.suggest_categorical("rezagos", list(REZAGOS_CANDIDATOS))],
        "transformacion": trial.suggest_categorical("transformacion", ["ninguna", "log1p"]),
        "n_estimators": trial.suggest_int("n_estimators", 100, 1500, log=True),
        "learning_rate": trial.suggest_float("learning_rate", 5e-3, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 100.0, log=True),
    }


def espacio_xgboost(trial) -> dict[str, Any]:
    hp = _espacio_arbol_comun(trial)
    hp["max_depth"] = trial.suggest_int("max_depth", 2, 8)
    hp["min_child_weight"] = trial.suggest_float("min_child_weight", 0.5, 50.0, log=True)
    return hp


def espacio_lightgbm(trial) -> dict[str, Any]:
    hp = _espacio_arbol_comun(trial)
    hp["num_leaves"] = trial.suggest_int("num_leaves", 4, 64, log=True)
    hp["min_child_samples"] = trial.suggest_int("min_child_samples", 5, 80, log=True)
    return hp


def espacio_lstm(trial) -> dict[str, Any]:
    capas = trial.suggest_int("capas", 1, 3)
    unidades = [trial.suggest_int(f"unidades_capa{k + 1}", 8, 128, log=True) for k in range(capas)]
    return {
        "ventana": trial.suggest_int("ventana", 6, 52),
        "unidades": unidades,
        "dropout": trial.suggest_float("dropout", 0.0, 0.5),
        "optimizador": trial.suggest_categorical("optimizador", ["adam", "rmsprop"]),
        "tasa_aprendizaje": trial.suggest_float("tasa_aprendizaje", 1e-4, 1e-2, log=True),
        "batch_size": 2 ** trial.suggest_int("log2_batch_size", 3, 6),
    }


def espacio_nbeats(trial) -> dict[str, Any]:
    return {
        "ventana": trial.suggest_int("ventana", 6, 52),
        "num_pilas": trial.suggest_int("num_pilas", 2, 30, log=True),
        "num_bloques": trial.suggest_int("num_bloques", 1, 2),
        "num_capas": trial.suggest_int("num_capas", 1, 4),
        "ancho_capa": trial.suggest_int("ancho_capa", 32, 256, log=True),
        "dropout": trial.suggest_float("dropout", 0.0, 0.5),
        "tasa_aprendizaje": trial.suggest_float("tasa_aprendizaje", 1e-4, 1e-2, log=True),
        "batch_size": 2 ** trial.suggest_int("log2_batch_size", 3, 6),
    }


# ---------------------------------------------------------------------------
# Evaluacion y objetivos
# ---------------------------------------------------------------------------

def evaluar_en_bloque(modelo, df: pd.DataFrame, primera: int, ultima: int, paso: int = 1) -> pd.DataFrame:
    """Registros walk-forward del bloque [primera, ultima] con un modelo ya entrenado."""
    origenes = origenes_del_bloque(primera, ultima, paso=paso)
    trayectorias = modelo.trayectorias(df, origenes)
    fechas = list(pd.to_datetime(df["fecha_semana"]))
    return construir_registros(fechas, df["casos"].to_numpy(dtype=float), origenes, trayectorias, primera, ultima)


def validacion_cruzada(crear: Callable[[], Any], df: pd.DataFrame, cortes: list[dict[str, int]], paso: int = 1) -> dict[str, Any]:
    """Promedio del RMSE global (H1 a H6) de los cortes, cada uno entrenando con
    lo anterior a su bloque y evaluando el bloque con el walk-forward."""
    rmses, maes, aics = [], [], []
    for corte in cortes:
        modelo = crear()
        modelo.entrenar(df, corte["inicio_bloque"])
        registros = evaluar_en_bloque(modelo, df, corte["inicio_bloque"], corte["fin_bloque"] - 1, paso=paso)
        metricas = calcular_metricas(registros["casos_reales"], registros["pronostico_modelo"])
        rmses.append(metricas["RMSE"])
        maes.append(metricas["MAE"])
        if getattr(modelo, "aic", None) is not None:
            aics.append(modelo.aic)
    resultado = {"rmse": float(np.mean(rmses)), "mae": float(np.mean(maes)), "rmse_cortes": rmses, "mae_cortes": maes}
    if aics:
        resultado["aic_cortes"] = aics
    return resultado


def objetivo_validacion_cruzada(espacio: Callable, construir: Callable[[dict], Any], df: pd.DataFrame,
                                cortes: list[dict[str, int]], paso: int = 1) -> Callable:
    cache = CacheDePruebas()

    def objetivo(trial):
        hp = espacio(trial)
        guardado = cache.buscar(trial.params)
        if guardado is not None:
            valor, atributos = guardado
            for clave, contenido in atributos.items():
                trial.set_user_attr(clave, contenido)
            trial.set_user_attr("repetida", True)
            return valor
        inicio = time.time()
        resultado = validacion_cruzada(lambda: construir(hp), df, cortes, paso=paso)
        atributos = {"mae": resultado["mae"], "rmse_cortes": resultado["rmse_cortes"],
                     "mae_cortes": resultado["mae_cortes"], "hiperparametros": hp,
                     "segundos": round(time.time() - inicio, 1)}
        if "aic_cortes" in resultado:
            atributos["aic_cortes"] = resultado["aic_cortes"]
        for clave, contenido in atributos.items():
            trial.set_user_attr(clave, contenido)
        cache.registrar(trial.params, resultado["rmse"], atributos)
        return resultado["rmse"]

    return objetivo


def objetivo_red(espacio: Callable, construir: Callable[[dict, int], Any], df: pd.DataFrame,
                 fin_ajuste: int, fin: int, semillas: list[int]) -> Callable:
    """RMSE global (H1 a H6) medio de las semillas en el bloque de validacion
    [fin_ajuste, fin). Informa la media parcial despues de cada semilla para la
    poda por mediana."""
    import optuna

    def objetivo(trial):
        hp = espacio(trial)
        rmses, maes, epocas = [], [], []
        inicio = time.time()
        for paso, semilla in enumerate(semillas):
            modelo = construir(hp, semilla)
            modelo.entrenar(df, fin, fin_ajuste)
            registros = evaluar_en_bloque(modelo, df, fin_ajuste, fin - 1)
            metricas = calcular_metricas(registros["casos_reales"], registros["pronostico_modelo"])
            rmses.append(metricas["RMSE"])
            maes.append(metricas["MAE"])
            epocas.append(modelo.detalles.get("epocas_ejecutadas"))
            if hasattr(modelo, "limpiar"):
                modelo.limpiar()
            trial.report(float(np.mean(rmses)), paso)
            if paso < len(semillas) - 1 and trial.should_prune():
                trial.set_user_attr("rmse_semillas", rmses)
                raise optuna.TrialPruned()
        sd = float(np.std(rmses, ddof=1)) if len(rmses) > 1 else 0.0
        for clave, contenido in {
            "rmse_media": float(np.mean(rmses)), "rmse_sd": sd, "mae": float(np.mean(maes)),
            "rmse_semillas": rmses, "mae_semillas": maes, "epocas": epocas, "hiperparametros": hp,
            "segundos": round(time.time() - inicio, 1),
        }.items():
            trial.set_user_attr(clave, contenido)
        return float(np.mean(rmses))

    return objetivo


def configuraciones_completas(estudio) -> list[dict[str, Any]]:
    """Pruebas completas de un estudio de redes, en el formato de
    experimentacion.elegir_configuracion_estable."""
    import optuna

    salida = []
    for trial in estudio.trials:
        if trial.state != optuna.trial.TrialState.COMPLETE:
            continue
        salida.append({
            "numero": trial.number,
            "rmse_media": trial.user_attrs["rmse_media"],
            "rmse_sd": trial.user_attrs["rmse_sd"],
            "mae": trial.user_attrs["mae"],
            "hiperparametros": trial.user_attrs["hiperparametros"],
        })
    return salida


# ---------------------------------------------------------------------------
# Experimento: busqueda, prueba y resultados de un notebook de investigacion
# ---------------------------------------------------------------------------

class Experimento:
    """Reune lo que hacen el 03 y el 05 con cada modelo: la busqueda con Optuna
    (historial en outputs/resultados/optuna), la prueba walk-forward en el 15 %
    final (con una o varias semillas) y el resumen para el JSON de resultados."""

    def __init__(self, df: pd.DataFrame, fin_ajuste: int, fin_entrenamiento: int, salidas, prefijo: str):
        self.df = df
        self.fin_ajuste = fin_ajuste
        self.fin_entrenamiento = fin_entrenamiento
        self.ultima = len(df) - 1
        self.salidas = salidas
        self.prefijo = prefijo
        self.resultados: dict[str, dict[str, Any]] = {}
        self.estudios: dict[str, Any] = {}
        self.registros: dict[str, pd.DataFrame] = {}
        self.persistencia: dict[str, Any] | None = None

    def estudiar(self, nombre: str, objetivo: Callable, pruebas: int, podador=None):
        from dengue.experimentacion import crear_estudio, guardar_historial, resumen_estudio

        estudio = crear_estudio(f"{self.prefijo}_{nombre}", podador)
        estudio.optimize(objetivo, n_trials=pruebas, gc_after_trial=True)
        rutas = guardar_historial(estudio, self.salidas, f"{self.prefijo}_{nombre}")
        self.estudios[nombre] = {"estudio": estudio, "resumen": {**resumen_estudio(estudio), "historial": rutas}}
        return estudio

    def evaluar_prueba(self, nombre: str, familia: str, crear: Callable, hiperparametros: dict[str, Any],
                       semillas: list[int] | None = None, estudio: str | None = None, **extra) -> dict[str, Any]:
        """crear() devuelve un modelo sin entrenar; en las redes crear(semilla)."""
        from dengue.experimentacion import metricas_de_registros, resumir_semillas

        lista, partes, detalles = [], [], []
        for semilla in (semillas or [None]):
            modelo = crear() if semilla is None else crear(semilla)
            modelo.entrenar(self.df, self.fin_entrenamiento, self.fin_ajuste)
            registros = evaluar_en_bloque(modelo, self.df, self.fin_entrenamiento, self.ultima)
            lista.append(metricas_de_registros(registros))
            partes.append(registros.assign(semilla=semilla) if semilla is not None else registros)
            detalles.append(getattr(modelo, "detalles", {}))
            if hasattr(modelo, "limpiar"):
                modelo.limpiar()
        registros = pd.concat(partes, ignore_index=True)
        registros.to_csv(self.salidas.registros / f"{self.prefijo}_{nombre}_prueba.csv", index=False)
        metricas = resumir_semillas(lista) if semillas else lista[0]
        if self.persistencia is None:
            self.persistencia = {"global": lista[0]["global"]["persistencia"],
                                 "por_horizonte": {h: v["persistencia"] for h, v in lista[0]["por_horizonte"].items()}}
        entrada = {
            "familia": familia,
            "hiperparametros": hiperparametros,
            "prueba": metricas,
            "a_un_paso": metricas["por_horizonte"]["1"]["modelo"],
            **extra,
        }
        if semillas:
            entrada["semillas"] = list(semillas)
            entrada["prueba_por_semilla"] = lista
            entrada["detalles_entrenamiento"] = detalles
        if estudio is not None and estudio in self.estudios:
            entrada["optuna"] = self.estudios[estudio]["resumen"]
        self.resultados[nombre] = entrada
        self.registros[nombre] = partes[0]
        self.ultimo_modelo = modelo
        return entrada

    def tabla(self, horizonte: str | None = None) -> pd.DataFrame:
        """RMSE, MAE, MAPE y R2 de cada modelo (global o de un horizonte), con la
        desviacion entre semillas en las redes."""
        filas = []
        for nombre, entrada in self.resultados.items():
            bloque = entrada["prueba"]["global"] if horizonte is None else entrada["prueba"]["por_horizonte"][horizonte]
            valores = bloque["modelo"]
            fila = {"Modelo": nombre, "Familia": entrada["familia"]}
            for metrica in ("RMSE", "MAE", "MAPE", "R2"):
                fila[metrica] = valores[metrica]
                if f"{metrica}_sd" in valores:
                    fila[f"{metrica} sd"] = valores[f"{metrica}_sd"]
            filas.append(fila)
        if self.persistencia is not None:
            bloque = self.persistencia["global"] if horizonte is None else self.persistencia["por_horizonte"][horizonte]
            filas.append({"Modelo": "Persistencia", "Familia": "control",
                          **{m: bloque[m] for m in ("RMSE", "MAE", "MAPE", "R2")}})
        return pd.DataFrame(filas)

    def tabla_multipaso(self) -> pd.DataFrame:
        filas = []
        for nombre, entrada in self.resultados.items():
            for horizonte, bloque in entrada["prueba"]["por_horizonte"].items():
                filas.append({"Modelo": nombre, "H": int(horizonte),
                              **{m: bloque["modelo"][m] for m in ("RMSE", "MAE", "MAPE", "R2")}})
        if self.persistencia is not None:
            for horizonte, bloque in self.persistencia["por_horizonte"].items():
                filas.append({"Modelo": "Persistencia", "H": int(horizonte),
                              **{m: bloque[m] for m in ("RMSE", "MAE", "MAPE", "R2")}})
        return pd.DataFrame(filas)
