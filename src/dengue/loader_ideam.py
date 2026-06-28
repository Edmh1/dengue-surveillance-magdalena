import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import time
import json
from io import StringIO, BytesIO
import zipfile
import base64
from pathlib import Path


# Configuracion
BASE_URL      = "http://modulopersonalizado.ideam.gov.co/DhimeServicePortal"
TOKEN_URL     = f"{BASE_URL}/token"
DATA_URL      = f"{BASE_URL}/api/Listas/ConsultarListaSeriesTiempoEstacionesPorFiltroString"

MAPSERVER_BUSQUEDA_URL = "http://dhime.ideam.gov.co/server/rest/services/CNE/Estaciones/MapServer/8/query"
MAPSERVER_DETALLE_URL = "http://dhime.ideam.gov.co/server/rest/services/CNE/Estaciones/MapServer/0/query"

ID_DEPARTAMENTO = "47"  # Magdalena

CREDENTIALS = {
    "username"   : "apiuser_sgdhm",
    "password"   : "mvm2017*",
    "grant_type" : "password",
}

FECHA_INICIO = "2007-1-1T05:00:00.000Z"
FECHA_FIN    = "2024-12-31T05:00:00.000Z"

VARIABLES = {
    "temperatura_maxima" : ("TEMPERATURA", "TMX_CON"),
    "temperatura_minima" : ("TEMPERATURA", "TMN_CON"),
    "temperatura_media"  : ("TEMPERATURA", "TSSM_MEDIA_D"),
    "precipitacion"      : ("PRECIPITACION", "PTPM_CON"),
    "humedad_relativa"   : ("HUM RELATIVA", "HRA2_MEDIA_D"), 
}

DIR_RAW  = Path("data/external/ideam/raw")
DIR_CONS = Path("data/external/ideam/consolidado")


# Sesion con reintentos automaticos
def _crear_sesion() -> requests.Session:
    sesion     = requests.Session()
    reintentos = Retry(
        total            = 3,
        backoff_factor   = 2,
        status_forcelist = [500, 502, 503, 504],
        allowed_methods  = ["POST", "GET"],
        raise_on_status  = False,
    )
    sesion.mount("http://", HTTPAdapter(max_retries=reintentos))
    return sesion

SESION = _crear_sesion()

def obtener_detalle_estacion(id_estacion: str) -> dict:
    """
    Consulta una estación específica en la capa 0
    para obtener geometría real y atributos.
    """

    params = {
        "f": "json",
        "where": f"idestacion = '{id_estacion}'",
        "returnGeometry": "true",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "nombre",
    }

    r = SESION.get(MAPSERVER_DETALLE_URL, params=params, timeout=30)
    r.raise_for_status()

    features = r.json().get("features", [])

    if not features:
        return {}

    feature = features[0]

    attr = feature.get("attributes", {})
    geom = feature.get("geometry", {})

    return {
        "id_estacion": id_estacion,
        "nombre": attr.get("nombre"),
        "lat": geom.get("y"),
        "lon": geom.get("x"),
    }


# Consulta dinamica de estaciones
def obtener_estaciones_magdalena(etiqueta: str) -> list[dict]:
    """
    Consulta el MapServer del IDEAM para obtener las estaciones
    del Magdalena disponibles para la etiqueta dada, con sus
    coordenadas geograficas reales (lat, lon en WGS84).
    """
    params = {
        "f"                   : "json",
        "where"               : f"etiqueta = '{etiqueta}' and iddepartamento='{ID_DEPARTAMENTO}'",
        "returnGeometry"      : "false",
        "spatialRel"          : "esriSpatialRelIntersects",
        "outFields"           : "idestacion,nombre,municipio,idmunicipio",
        "returnDistinctValues": "false",
        "orderByFields"       : "nombre ASC",
    }
    r = SESION.get(MAPSERVER_BUSQUEDA_URL, params=params, timeout=30)
    r.raise_for_status()

    estaciones = []
    for feature in r.json().get("features", []):
        attr = feature.get("attributes", {})
        id_est = attr.get("idestacion")
        if not id_est:
            continue
        id_mun = attr.get("idmunicipio")
        if isinstance(id_mun, dict):
            id_mun = id_mun.get("parsedValue", id_mun.get("source", ""))

        detalle = obtener_detalle_estacion(str(id_est))

        estaciones.append({
            "id_estacion" : str(id_est),
            "nombre"      : attr.get("nombre", ""),
            "municipio"   : attr.get("municipio", ""),
            "id_municipio": int(float(str(id_mun))) if id_mun else None,
            "lat"         : detalle.get("lat"),
            "lon"         : detalle.get("lon"),
        })

        time.sleep(0.2)

    return estaciones


# Autenticacion
def obtener_token() -> str:
    """Obtiene Bearer token del portal IDEAM."""
    time.sleep(1)
    r = SESION.post(TOKEN_URL, data=CREDENTIALS, timeout=30)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise ValueError(f"No se obtuvo token. Respuesta: {r.text[:200]}")
    print("Token obtenido.")
    return token


# Descarga por bloque de estaciones
def _construir_filtro(ids: list[str], parametro: str, etiqueta: str) -> str:
    condiciones = [
        f"(IdParametro~eq~'{parametro}'~and~Etiqueta~eq~'{etiqueta}'~and~IdEstacion~eq~'{i}')"
        for i in ids
    ]
    return "(" + "~or~".join(condiciones) + ")"


def _construir_body(ids: list[str], parametro: str, etiqueta: str) -> list[dict]:
    """Array JSON requerido en el body del POST, una entrada por estacion."""
    return [
        {
            "Calculo"    : "",
            "EsEjeY1"    : False,
            "EsEjeY2"    : False,
            "EsTipoBarra": False,
            "EsTipoLinea": False,
            "Etiqueta"   : etiqueta,
            "IdParametro": parametro,
            "TipoSerie"  : "Estandard",
        }
        for _ in ids
    ]


def _request_bloque(token: str, filtro: str, body: list[dict]) -> requests.Response | str:
    """
    POST con params en query string, body JSON array y Bearer en header.
    Retorna Response o la cadena 'TOKEN_EXPIRADO'.
    """
    params = {
        "sort"                  : "",
        "filter"                : filtro,
        "group"                 : "",
        "fechaInicio"           : FECHA_INICIO,
        "fechaFin"              : FECHA_FIN,
        "mostrarGrado"          : "true",
        "mostrarCalificador"    : "true",
        "mostrarNivelAprobacion": "true",
        "tipoReporte"           : "csv",
    }
    headers = {"Authorization": f"Bearer {token}"}
    r = SESION.post(DATA_URL, params=params, json=body, headers=headers, timeout=180)
    if r.status_code == 401:
        return "TOKEN_EXPIRADO"
    r.raise_for_status()
    return r


def _parsear_respuesta(r: requests.Response) -> pd.DataFrame | None:
    """
    El portal devuelve JSON con clave 'zip' cuyo valor es el ZIP en base64.
    El CSV interno usa coma como separador y UTF-8.
    """
    data = r.json()
    zip_b64 = data.get("zip")
    if not zip_b64:
        return None
    zf = zipfile.ZipFile(BytesIO(base64.b64decode(zip_b64 + "==")))
    csv = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
    df  = pd.read_csv(StringIO(csv), sep=",", decimal=".",
                      parse_dates=["Fecha"], dayfirst=False)
    return df if not df.empty else None


def descargar_bloque(
    token: str,
    ids: list[str],
    parametro: str,
    etiqueta: str,
    tam_bloque: int = 10,
) -> pd.DataFrame | None | str:
    """
    Intenta descargar todas las estaciones en un solo request.
    Si falla cae automaticamente a bloques de tam_bloque estaciones.
    """
    # Intento 1: todas las estaciones en un solo request
    try:
        filtro = _construir_filtro(ids, parametro, etiqueta)
        body = _construir_body(ids, parametro, etiqueta)
        r = _request_bloque(token, filtro, body)
        if isinstance(r, str) and r == "TOKEN_EXPIRADO":
            return "TOKEN_EXPIRADO"
        df = _parsear_respuesta(r) #type:ignore
        if df is not None:
            print(f"    Descargadas {len(ids)} estaciones en un solo request.")
            return df
    except Exception as e:
        print(f"    Request unico fallo ({e}). Cambiando a bloques de {tam_bloque}...")

    # Intento 2: bloques de tam_bloque con pausa entre bloques
    dfs = []
    for i in range(0, len(ids), tam_bloque):
        bloque = ids[i:i + tam_bloque]
        try:
            filtro = _construir_filtro(bloque, parametro, etiqueta)
            body = _construir_body(bloque, parametro, etiqueta)
            r  = _request_bloque(token, filtro, body)
            if isinstance(r, str) and r == "TOKEN_EXPIRADO":
                return "TOKEN_EXPIRADO"
            df = _parsear_respuesta(r) #type:ignore
            if df is not None:
                dfs.append(df)
            print(f"    Bloque {i//tam_bloque + 1} OK ({len(bloque)} estaciones)")
            time.sleep(1)
        except Exception as e:
            print(f"    Error en bloque {i//tam_bloque + 1}: {e}")

    if not dfs:
        return None
    return pd.concat(dfs, ignore_index=True)


# Descarga completa por variable
def descargar_variable(nombre_var: str, parametro: str, etiqueta: str) -> None:
    """
    Consulta dinamicamente las estaciones del Magdalena para la etiqueta,
    intenta descargar todas en un solo request y si falla cae a bloques de 10.
    """
    dir_var = DIR_RAW / nombre_var
    dir_var.mkdir(parents=True, exist_ok=True)
    DIR_CONS.mkdir(parents=True, exist_ok=True)

    archivo_meta = dir_var / "_estaciones.json"
    parquet_out  = DIR_CONS / f"{nombre_var}.parquet"

    print(f"\nConsultando estaciones para {nombre_var} ({etiqueta})...")
    estaciones = obtener_estaciones_magdalena(etiqueta)
    print(f"  Estaciones encontradas en Magdalena: {len(estaciones)}")

    if not estaciones:
        print("  Sin estaciones disponibles. Saltando.")
        return

    with open(archivo_meta, "w", encoding="utf-8") as f:
        json.dump(estaciones, f, ensure_ascii=False, indent=2)

    if parquet_out.exists():
        print("  Parquet ya existe. Saltando.")
        return

    ids   = [e["id_estacion"] for e in estaciones]
    token = obtener_token()

    resultado = descargar_bloque(token, ids, parametro, etiqueta)

    if isinstance(resultado, str) and resultado == "TOKEN_EXPIRADO":
        print("  Token expirado. Renovando y reintentando...")
        token = obtener_token()
        resultado = descargar_bloque(token, ids, parametro, etiqueta)

    if resultado is None or (isinstance(resultado, str) and resultado == "TOKEN_EXPIRADO"):
        print(f"  Sin datos para {nombre_var}.")
        return
    
    print("\n=== DIAGNOSTICO ===")
    print(f"Estaciones solicitadas: {len(ids)}")

    ids_descargados = resultado["CodigoEstacion"].astype(str).unique()  #type:ignore

    print(f"Estaciones con datos: {len(ids_descargados)}")

    faltantes = set(ids) - set(ids_descargados)

    print(f"Estaciones sin datos: {len(faltantes)}")

    for est in sorted(faltantes):
        print(est)

    _consolidar(nombre_var, dir_var, parquet_out, estaciones, resultado) #type:ignore

    time.sleep(2)


# Consolidacion
def _consolidar(
    nombre_var : str,
    dir_var    : Path,
    parquet_out: Path,
    estaciones : list[dict],
    df_raw     : pd.DataFrame,
) -> None:
    """Renombra columnas, agrega municipio e id_municipio y guarda el Parquet."""
    meta_map = {e["id_estacion"]: e for e in estaciones}

    df = df_raw.copy()
    df = df.rename(columns={
        "CodigoEstacion"  : "id_estacion",
        "NombreEstacion"  : "nombre_estacion",
        "Variable"        : "variable",
        "Parametro"       : "parametro",
        "Fecha"           : "fecha",
        "Unidad"          : "unidad",
        "Valor"           : "valor",
        "NivelAprobacion" : "nivel_aprobacion",
    })

    df["id_estacion"] = df["id_estacion"].astype(str)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["municipio"] = df["id_estacion"].map(
        lambda x: meta_map.get(x, {}).get("municipio", ""))
    df["id_municipio"] = df["id_estacion"].map(
        lambda x: meta_map.get(x, {}).get("id_municipio"))

    df.to_parquet(parquet_out, index=False)
    print(f"  Consolidado: {parquet_out} ({len(df):,} registros, {df['id_estacion'].nunique()} estaciones)")


if __name__ == "__main__":
    print("Descarga automatica IDEAM - Magdalena 2007-2024")
    print(f"Departamento: {ID_DEPARTAMENTO} (Magdalena)")
    print(f"Variables: {list(VARIABLES.keys())}")
    print(f"Periodo: {FECHA_INICIO[:10]} -> {FECHA_FIN[:10]}")


    for nombre_var, (parametro, etiqueta) in VARIABLES.items():
        descargar_variable(nombre_var, parametro, etiqueta)

    print("\nDescarga completa.")
    print("Archivos en data/external/ideam/consolidado/")