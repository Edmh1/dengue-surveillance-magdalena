"""Utilidades comunes de los notebooks de modelado (03, 05, 06 y 07).

- Modo de ejecucion y carpetas de salida (las del modo rapido van a _rapido).
- Estilo y guardado de figuras (300 dpi, ancho de documento Word).
- Metricas con las mismas formulas del tablero (RMSE, MAE, MAPE sin ceros, R2),
  globales sobre todos los registros y por horizonte.
- Registros walk-forward con el mismo formato que el CSV de la prueba del tablero.
- Semillas y determinismo de TensorFlow y PyTorch.
- Busqueda con Optuna (TPE con semilla fija), historiales e importancias.
- Reglas de seleccion de la metodologia (secciones 6 y 7).
- Lectura y escritura de los JSON de resultados.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]

HORIZONTES = [1, 2, 3, 4, 5, 6]
H_MAX = max(HORIZONTES)

ANCHO_FIGURA = 6.5
DPI_FIGURAS = 300

SEMILLA_OPTUNA = 42
SEMILLAS_REDES = [42, 43, 44, 45, 46]

UMBRAL_EMPATE = 0.02        # seccion 7: candidatos a menos de un 2 % de RMSE global
UMBRAL_ESTABILIDAD = 0.05   # seccion 6: configuraciones a menos de un 5 % del mejor RMSE medio

FRACCION_BLOQUE = 0.15      # cada corte evalua el 15 % final de la serie que termina en el
CORTES_VALIDACION = 3

COLUMNAS_REGISTROS = [
    "fecha_origen",
    "horizonte_semanas",
    "fecha_objetivo",
    "casos_reales",
    "pronostico_modelo",
    "error_absoluto",
    "error_porcentual",
    "pronostico_persistencia",
    "error_absoluto_persistencia",
    "error_porcentual_persistencia",
]


# ---------------------------------------------------------------------------
# Modo de ejecucion y salidas
# ---------------------------------------------------------------------------

@dataclass
class Salidas:
    """Carpetas de salida de un notebook. En modo rapido todo cuelga de _rapido."""

    modo_rapido: bool
    figuras: Path
    resultados: Path
    optuna: Path
    paquetes: Path
    informe: Path
    registros: Path

    def relativa(self, ruta: Path) -> str:
        return Path(ruta).resolve().relative_to(RAIZ).as_posix()


def modo_sensibilidad() -> bool:
    """Analisis de sensibilidad de la busqueda de las redes (variable de entorno
    SENSIBILIDAD=1): rangos y presupuesto ampliados en produccion.espacio_lstm,
    espacio_nbeats y PRUEBAS, con todas las salidas en subcarpetas _sensibilidad.
    No cambia la corrida oficial."""
    return os.environ.get("SENSIBILIDAD") == "1"


def configurar_salidas(carpeta_figuras: str, modo_rapido: bool) -> Salidas:
    sufijo = "_rapido" if modo_rapido else ("_sensibilidad" if modo_sensibilidad() else "")
    salidas_base = RAIZ / "outputs"
    figuras = salidas_base / "figures" / carpeta_figuras
    resultados = salidas_base / "resultados"
    paquetes = salidas_base / "paquetes"
    informe = salidas_base
    if sufijo:
        figuras = figuras / sufijo
        resultados = resultados / sufijo
        paquetes = paquetes / sufijo
        informe = informe / sufijo
    optuna_dir = resultados / "optuna"
    registros = resultados / "registros"
    for carpeta in (figuras, resultados, optuna_dir, paquetes, informe, registros):
        carpeta.mkdir(parents=True, exist_ok=True)
    return Salidas(modo_rapido, figuras, resultados, optuna_dir, paquetes, informe, registros)


class Cronometro:
    """Mide el tiempo de cada etapa del notebook para el JSON de resultados."""

    def __init__(self) -> None:
        self.inicio = time.time()
        self.etapas: dict[str, float] = {}
        self._actual: tuple[str, float] | None = None

    def etapa(self, nombre: str) -> None:
        ahora = time.time()
        if self._actual is not None:
            anterior, desde = self._actual
            self.etapas[anterior] = round(ahora - desde, 1)
        self._actual = (nombre, ahora)

    def resumen(self) -> dict[str, Any]:
        self.etapa("_fin")
        self.etapas.pop("_fin", None)
        return {"total_segundos": round(time.time() - self.inicio, 1), "etapas_segundos": dict(self.etapas)}


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

COLORES_FAMILIA = {
    "estadistico": "#185FA5",
    "aprendizaje_automatico": "#1D9E75",
    "aprendizaje_profundo": "#D85A30",
    "persistencia": "#333333",
}


def estilo_figuras() -> None:
    """Tamanos de letra pensados para una figura de 6,5 pulgadas en Word."""
    import matplotlib as mpl

    mpl.rcParams.update({
        "figure.figsize": (ANCHO_FIGURA, 3.2),
        "figure.dpi": 110,
        "savefig.dpi": DPI_FIGURAS,
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "figure.titlesize": 10,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 1.2,
    })


class RegistroFiguras:
    """Guarda cada figura a 300 dpi y anota su ruta y lo que muestra, para el
    JSON de resultados y para RESULTADOS_PARA_INFORME.md."""

    def __init__(self, salidas: Salidas, notebook: str) -> None:
        self.salidas = salidas
        self.notebook = notebook
        self.figuras: list[dict[str, str]] = []

    def guardar(self, fig, nombre: str, descripcion: str) -> Path:
        ruta = self.salidas.figuras / nombre
        fig.savefig(ruta, dpi=DPI_FIGURAS, bbox_inches="tight")
        relativa = self.salidas.relativa(ruta)
        self.figuras = [f for f in self.figuras if f["ruta"] != relativa]
        self.figuras.append({"notebook": self.notebook, "ruta": relativa, "descripcion": descripcion})
        return ruta


def figura_pronosticos(registros: pd.DataFrame, titulo: str, horizontes=(1, 4), alto: float = 2.6,
                       contexto: pd.DataFrame | None = None):
    """Casos reales de las semanas objetivo contra los pronosticos a los
    horizontes indicados (por defecto 1 y 4 semanas)."""
    import matplotlib.pyplot as plt

    colores = {1: "#185FA5", 2: "#1D9E75", 3: "#8c564b", 4: "#D85A30", 5: "#9467bd", 6: "#7f7f7f"}
    fig, ax = plt.subplots(figsize=(ANCHO_FIGURA, alto))
    if contexto is not None:
        ax.plot(contexto["fecha_semana"], contexto["casos"], color="#9a9a9a", lw=0.9, label="Casos previos")
    reales = registros[registros["horizonte_semanas"] == 1].sort_values("fecha_objetivo")
    ax.plot(reales["fecha_objetivo"], reales["casos_reales"], color="black", lw=1.3, label="Casos reales")
    for horizonte in horizontes:
        parte = registros[registros["horizonte_semanas"] == horizonte].sort_values("fecha_objetivo")
        etiqueta = "semana" if horizonte == 1 else "semanas"
        ax.plot(parte["fecha_objetivo"], parte["pronostico_modelo"], color=colores.get(horizonte, "#D85A30"),
                lw=1.0, ls="--" if horizonte > 1 else "-", label=f"Pronóstico a {horizonte} {etiqueta}")
    ax.set_title(titulo)
    ax.set_ylabel("Casos por semana")
    ax.legend(ncol=4, loc="upper left")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Metricas y registros
# ---------------------------------------------------------------------------

def calcular_metricas(reales, pronosticos) -> dict[str, float | int | None]:
    """Mismas formulas que pathologies.dengue.pronostico.evaluacion.calcular_metricas."""
    reales = np.asarray(reales, dtype=float)
    pronosticos = np.asarray(pronosticos, dtype=float)
    cantidad = len(reales)
    if cantidad == 0:
        return {"RMSE": None, "MAE": None, "MAPE": None, "R2": None, "n": 0, "n_mape": 0}
    errores = reales - pronosticos
    rmse = float(np.sqrt(np.mean(errores ** 2)))
    mae = float(np.mean(np.abs(errores)))
    con_casos = reales != 0
    cantidad_mape = int(con_casos.sum())
    mape = float(np.mean(np.abs(errores[con_casos]) / np.abs(reales[con_casos])) * 100) if cantidad_mape else None
    r2 = None
    if cantidad >= 2:
        total = float(np.sum((reales - reales.mean()) ** 2))
        r2 = float(1 - np.sum(errores ** 2) / total) if total > 0 else None
    return {"RMSE": rmse, "MAE": mae, "MAPE": mape, "R2": r2, "n": cantidad, "n_mape": cantidad_mape}


def construir_registros(
    fechas: list,
    casos: np.ndarray,
    origenes: list[int],
    trayectorias: np.ndarray,
    primera: int,
    ultima: int,
) -> pd.DataFrame:
    """Un registro por origen y horizonte cuya semana objetivo cae en [primera,
    ultima]. Mismo recorrido y mismas columnas que evaluacion.evaluar_en_prueba
    del tablero (el notebook 06 comprueba que coinciden)."""
    casos = np.asarray(casos, dtype=float)
    filas = []
    for fila, origen in enumerate(origenes):
        for horizonte in range(1, trayectorias.shape[1] + 1):
            objetivo = origen + horizonte
            if objetivo < primera or objetivo > ultima:
                continue
            filas.append({
                "fecha_origen": fechas[origen],
                "horizonte_semanas": horizonte,
                "fecha_objetivo": fechas[objetivo],
                "casos_reales": casos[objetivo],
                "pronostico_modelo": float(trayectorias[fila, horizonte - 1]),
                "pronostico_persistencia": float(casos[origen]),
            })
    registros = pd.DataFrame(filas)
    reales = registros["casos_reales"].to_numpy(dtype=float)
    for columna, sufijo in (("pronostico_modelo", ""), ("pronostico_persistencia", "_persistencia")):
        pronosticos = registros[columna].to_numpy(dtype=float)
        registros[f"error_absoluto{sufijo}"] = np.abs(reales - pronosticos)
        porcentual = np.full(len(reales), np.nan)
        con_casos = reales != 0
        porcentual[con_casos] = np.abs(reales[con_casos] - pronosticos[con_casos]) / np.abs(reales[con_casos]) * 100
        registros[f"error_porcentual{sufijo}"] = porcentual
    return registros[COLUMNAS_REGISTROS]


def origenes_del_bloque(primera: int, ultima: int, h_max: int = H_MAX, paso: int = 1) -> list[int]:
    """Origenes que cubren cada semana del bloque [primera, ultima] en todos los
    horizontes: empiezan h_max semanas antes del bloque (convencion del tablero).
    paso > 1 solo se usa en modo rapido para abaratar la validacion cruzada."""
    return list(range(primera - h_max, ultima, paso))


def metricas_de_registros(registros: pd.DataFrame, horizontes: list[int] = HORIZONTES) -> dict[str, Any]:
    """{'global': {'modelo', 'persistencia'}, 'por_horizonte': {'1': {...}, ...}}.
    Globales sobre todos los registros a la vez, como el manifest del tablero."""
    resultado: dict[str, Any] = {"global": {}, "por_horizonte": {}}
    for nombre, columna in (("modelo", "pronostico_modelo"), ("persistencia", "pronostico_persistencia")):
        resultado["global"][nombre] = calcular_metricas(registros["casos_reales"], registros[columna])
    for horizonte in horizontes:
        parte = registros[registros["horizonte_semanas"] == horizonte]
        resultado["por_horizonte"][str(horizonte)] = {
            nombre: calcular_metricas(parte["casos_reales"], parte[columna])
            for nombre, columna in (("modelo", "pronostico_modelo"), ("persistencia", "pronostico_persistencia"))
        }
    return resultado


def tabla_por_horizonte(metricas: dict[str, Any], pronosticador: str = "modelo") -> pd.DataFrame:
    filas = []
    for horizonte, valores in metricas["por_horizonte"].items():
        filas.append({"H": int(horizonte), **{k: valores[pronosticador][k] for k in ("RMSE", "MAE", "MAPE", "R2")}})
    filas.append({"H": "global", **{k: metricas["global"][pronosticador][k] for k in ("RMSE", "MAE", "MAPE", "R2")}})
    return pd.DataFrame(filas)


def resumir_semillas(lista_metricas: list[dict[str, Any]]) -> dict[str, Any]:
    """Media y desviacion entre semillas de las metricas globales y por horizonte
    (desviacion muestral, ddof=1; 0 con una sola semilla)."""

    def media_sd(valores):
        valores = [v for v in valores if v is not None]
        if not valores:
            return None, None
        arreglo = np.asarray(valores, dtype=float)
        sd = float(arreglo.std(ddof=1)) if len(arreglo) > 1 else 0.0
        return float(arreglo.mean()), sd

    def resumir(bloques):
        salida = {}
        for metrica in ("RMSE", "MAE", "MAPE", "R2"):
            media, sd = media_sd([b[metrica] for b in bloques])
            salida[metrica] = media
            salida[f"{metrica}_sd"] = sd
        salida["n"] = bloques[0]["n"]
        return salida

    resultado = {"semillas": len(lista_metricas), "global": {}, "por_horizonte": {}}
    for pronosticador in ("modelo", "persistencia"):
        resultado["global"][pronosticador] = resumir([m["global"][pronosticador] for m in lista_metricas])
    for horizonte in lista_metricas[0]["por_horizonte"]:
        resultado["por_horizonte"][horizonte] = {
            pronosticador: resumir([m["por_horizonte"][horizonte][pronosticador] for m in lista_metricas])
            for pronosticador in ("modelo", "persistencia")
        }
    return resultado


def cortes_validacion_cruzada(
    semanas_entrenamiento: int, cantidad: int = CORTES_VALIDACION, fraccion: float = FRACCION_BLOQUE
) -> list[dict[str, int]]:
    """Cortes sucesivos dentro del entrenamiento. Cada corte reproduce la
    particion de la prueba sobre la serie que termina en el: entrena con su
    primer 85 % y evalua el 15 % final. Los bloques evaluados son contiguos y no
    se solapan. Devuelve del mas antiguo al mas reciente:
    [{'largo', 'inicio_bloque', 'fin_bloque'}] con fin_bloque exclusivo."""
    cortes = []
    largo = semanas_entrenamiento
    for _ in range(cantidad):
        semanas_bloque = int(round(largo * fraccion))
        cortes.append({"largo": largo, "inicio_bloque": largo - semanas_bloque, "fin_bloque": largo})
        largo -= semanas_bloque
    return list(reversed(cortes))


def diferenciaciones(valores: np.ndarray, periodo: int = 52, maximo: int = 2) -> dict[str, Any]:
    """d: la menor diferenciacion con la que ADF (p < 0,05) y KPSS (p >= 0,05)
    coinciden en que la serie es estacionaria. D: el mayor de los que indican las
    pruebas estacionales OCSB y Canova-Hansen."""
    import warnings

    from pmdarima.arima import nsdiffs
    from statsmodels.tsa.stattools import adfuller, kpss

    pruebas = []
    d_elegida = None
    serie = np.asarray(valores, dtype=float)
    for d in range(maximo + 1):
        actual = np.diff(serie, n=d) if d else serie
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p_adf = float(adfuller(actual, autolag="AIC")[1])
            p_kpss = float(kpss(actual, regression="c", nlags="auto")[1])
        estacionaria = p_adf < 0.05 and p_kpss >= 0.05
        pruebas.append({"d": d, "ADF p-valor": p_adf, "KPSS p-valor": p_kpss, "estacionaria (ambas)": estacionaria})
        if estacionaria and d_elegida is None:
            d_elegida = d
    if d_elegida is None:
        d_elegida = 1
    ocsb = int(nsdiffs(serie, m=periodo, test="ocsb"))
    ch = int(nsdiffs(serie, m=periodo, test="ch"))
    return {"d": d_elegida, "D": max(ocsb, ch), "pruebas_regulares": pruebas, "D_ocsb": ocsb, "D_ch": ch}


# ---------------------------------------------------------------------------
# Semillas y determinismo
# ---------------------------------------------------------------------------

def preparar_entorno_determinista() -> None:
    """Variables de entorno que deben fijarse ANTES de importar TensorFlow o
    PyTorch (CUDA lee CUBLAS_WORKSPACE_CONFIG al iniciar)."""
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    os.environ.setdefault("PYTHONHASHSEED", "0")


def activar_determinismo_tensorflow() -> None:
    import tensorflow as tf

    try:
        tf.config.experimental.enable_op_determinism()
    except AttributeError:
        os.environ["TF_DETERMINISTIC_OPS"] = "1"


def fijar_semilla_tensorflow(semilla: int) -> None:
    import keras

    keras.utils.set_random_seed(int(semilla))


def activar_determinismo_torch() -> None:
    import torch

    torch.use_deterministic_algorithms(True, warn_only=True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False


def describir_dispositivos() -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        import tensorflow as tf

        info["tensorflow_gpu"] = [d.name for d in tf.config.list_physical_devices("GPU")]
    except Exception as error:  # pragma: no cover - informativo
        info["tensorflow_gpu"] = f"no disponible ({error})"
    try:
        import torch

        info["torch_cuda"] = bool(torch.cuda.is_available())
    except Exception:
        info["torch_cuda"] = None
    return info


# ---------------------------------------------------------------------------
# Optuna
# ---------------------------------------------------------------------------

def silenciar_registros() -> None:
    import logging
    import warnings

    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    for nombre in ("cmdstanpy", "prophet", "lightning", "pytorch_lightning", "lightning.pytorch", "darts"):
        logging.getLogger(nombre).setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")


def crear_estudio(nombre: str, podador=None):
    """Estudio de Optuna con TPE y semilla fija (busqueda reproducible)."""
    import optuna

    muestreador = optuna.samplers.TPESampler(seed=SEMILLA_OPTUNA)
    return optuna.create_study(study_name=nombre, direction="minimize", sampler=muestreador, pruner=podador)


def podador_por_semilla():
    """Poda por mediana despues de cada semilla: una configuracion cuyo RMSE
    medio parcial es peor que la mediana de las anteriores en ese mismo punto se
    descarta sin entrenar las semillas restantes."""
    import optuna

    return optuna.pruners.MedianPruner(n_startup_trials=4, n_warmup_steps=0, interval_steps=1)


class CacheDePruebas:
    """TPE puede proponer una combinacion ya evaluada (espacios discretos, como
    los ordenes de ARIMA): en ese caso se devuelve el valor guardado en lugar de
    volver a entrenar."""

    def __init__(self) -> None:
        self._vistos: dict[str, tuple[float, dict]] = {}

    @staticmethod
    def _clave(params: dict) -> str:
        return json.dumps(params, sort_keys=True, default=str)

    def buscar(self, params: dict):
        return self._vistos.get(self._clave(params))

    def registrar(self, params: dict, valor: float, atributos: dict) -> None:
        self._vistos[self._clave(params)] = (valor, atributos)


def _a_json(valor):
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (np.floating,)):
        valor = float(valor)
    if isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor)):
        return None
    if isinstance(valor, np.ndarray):
        return [_a_json(v) for v in valor.tolist()]
    if isinstance(valor, (pd.Timestamp,)):
        return valor.strftime("%Y-%m-%d")
    if isinstance(valor, dict):
        return {str(k): _a_json(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_a_json(v) for v in valor]
    if isinstance(valor, Path):
        return valor.as_posix()
    return valor


def historial_estudio(estudio) -> list[dict[str, Any]]:
    filas = []
    for trial in estudio.trials:
        filas.append({
            "numero": trial.number,
            "estado": trial.state.name,
            "valor": trial.value,
            "parametros": trial.params,
            "atributos": trial.user_attrs,
            "valores_intermedios": {str(k): v for k, v in trial.intermediate_values.items()},
            "duracion_segundos": trial.duration.total_seconds() if trial.duration else None,
        })
    return _a_json(filas)


def guardar_historial(estudio, salidas: Salidas, nombre: str) -> dict[str, str]:
    """Guarda el historial completo de un estudio (JSON y CSV) en
    outputs/resultados/optuna/. Devuelve las rutas relativas."""
    ruta_json = salidas.optuna / f"{nombre}.json"
    ruta_csv = salidas.optuna / f"{nombre}.csv"
    contenido = {
        "estudio": estudio.study_name,
        "muestreador": "TPESampler",
        "semilla_muestreador": SEMILLA_OPTUNA,
        "podador": type(estudio.pruner).__name__ if estudio.pruner is not None else None,
        "pruebas": historial_estudio(estudio),
    }
    ruta_json.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        estudio.trials_dataframe().to_csv(ruta_csv, index=False)
    except Exception:
        pd.DataFrame(contenido["pruebas"]).to_csv(ruta_csv, index=False)
    return {"json": salidas.relativa(ruta_json), "csv": salidas.relativa(ruta_csv)}


def resumen_estudio(estudio) -> dict[str, Any]:
    import optuna

    completas = [t for t in estudio.trials if t.state == optuna.trial.TrialState.COMPLETE]
    podadas = [t for t in estudio.trials if t.state == optuna.trial.TrialState.PRUNED]
    resumen = {
        "pruebas": len(estudio.trials),
        "completas": len(completas),
        "podadas": len(podadas),
        "mejor_valor": None,
        "mejores_parametros": None,
        "mejor_prueba": None,
    }
    if completas:
        mejor = min(completas, key=lambda t: t.value)
        resumen.update({
            "mejor_valor": mejor.value,
            "mejores_parametros": mejor.params,
            "mejor_prueba": mejor.number,
            "atributos_mejor": mejor.user_attrs,
        })
    return _a_json(resumen)


def importancias(estudio) -> dict[str, float]:
    """Importancia de cada hiperparametro (fANOVA de Optuna). Vacio si no hay
    pruebas suficientes para calcularla."""
    import optuna

    try:
        return {k: float(v) for k, v in optuna.importance.get_param_importances(estudio).items()}
    except Exception:
        return {}


def figura_importancias(estudio, titulo: str):
    import matplotlib.pyplot as plt

    valores = importancias(estudio)
    fig, ax = plt.subplots(figsize=(ANCHO_FIGURA, 2.6))
    if valores:
        serie = pd.Series(valores).sort_values()
        ax.barh(serie.index, serie.values, color="#185FA5", alpha=0.85)
        ax.set_xlabel("Importancia relativa (fANOVA)")
    else:
        ax.text(0.5, 0.5, "Pruebas insuficientes para estimar la importancia", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_axis_off()
    ax.set_title(titulo)
    fig.tight_layout()
    return fig, valores


# ---------------------------------------------------------------------------
# Reglas de seleccion (metodologia, secciones 6 y 7)
# ---------------------------------------------------------------------------

def elegir_configuracion_estable(pruebas: list[dict[str, Any]], umbral: float = UMBRAL_ESTABILIDAD) -> dict[str, Any]:
    """Seccion 6: entre las configuraciones (completas, con todas sus semillas)
    cuyo RMSE global medio esta a menos de un 5 % del mejor, la de menor
    desviacion entre semillas. pruebas: [{'numero', 'rmse_media', 'rmse_sd', ...}]."""
    if not pruebas:
        raise ValueError("No hay configuraciones completas para elegir.")
    mejor = min(p["rmse_media"] for p in pruebas)
    cercanas = [p for p in pruebas if p["rmse_media"] <= mejor * (1 + umbral)]
    elegida = min(cercanas, key=lambda p: (p["rmse_sd"], p["rmse_media"]))
    return {"elegida": elegida, "mejor_rmse_media": mejor, "cercanas": [p["numero"] for p in cercanas]}


def elegir_ganador(candidatos: dict[str, dict[str, float]], umbral: float = UMBRAL_EMPATE) -> dict[str, Any]:
    """Seccion 7. candidatos: {nombre: {'RMSE', 'MAE', opcional 'RMSE_sd'}} con
    las metricas globales de la prueba (en las redes, medias de las semillas).

    1. Gana el menor RMSE global.
    2. Si hay candidatos a menos de un 2 % de ese RMSE, entre ellos gana el menor MAE.
    3. Si ademas sus MAE quedan a menos de un 2 % entre si y hay desviacion entre
       semillas (redes), gana la menor desviacion.
    """
    nombres = list(candidatos)
    mejor_rmse = min(candidatos[n]["RMSE"] for n in nombres)
    empatados = [n for n in nombres if candidatos[n]["RMSE"] <= mejor_rmse * (1 + umbral)]
    if len(empatados) == 1:
        return {"ganador": empatados[0], "criterio": "RMSE global", "empatados_rmse": empatados}
    mejor_mae = min(candidatos[n]["MAE"] for n in empatados)
    empatados_mae = [n for n in empatados if candidatos[n]["MAE"] <= mejor_mae * (1 + umbral)]
    con_sd = all(candidatos[n].get("RMSE_sd") is not None for n in empatados_mae)
    if len(empatados_mae) > 1 and con_sd:
        ganador = min(empatados_mae, key=lambda n: candidatos[n]["RMSE_sd"])
        criterio = "desviación entre semillas (RMSE y MAE a menos de un 2 %)"
    else:
        ganador = min(empatados, key=lambda n: candidatos[n]["MAE"])
        criterio = "MAE global (RMSE a menos de un 2 %)"
    return {"ganador": ganador, "criterio": criterio, "empatados_rmse": empatados, "empatados_mae": empatados_mae}


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def guardar_json(contenido: dict[str, Any], ruta: Path) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(_a_json(contenido), ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def leer_json(ruta: Path) -> dict[str, Any]:
    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe {ruta}. Ejecuta antes el notebook que lo genera, en el mismo modo (MODO_RAPIDO)."
        )
    return json.loads(ruta.read_text(encoding="utf-8"))


def versiones_librerias(nombres: list[str]) -> dict[str, str]:
    import importlib

    versiones = {}
    for nombre in nombres:
        try:
            modulo = importlib.import_module(nombre)
            versiones[nombre] = str(getattr(modulo, "__version__", "desconocida"))
        except Exception:
            versiones[nombre] = "no instalada"
    return versiones
