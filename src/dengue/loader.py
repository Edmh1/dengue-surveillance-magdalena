from pathlib import Path
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed


def _leer_archivo(ruta: Path) -> pd.DataFrame:
    """
    Lee un archivo SIVIGILA completo según su extensión.
    Soporta: xlsx, xls, csv, parquet.
    """
    ext = ruta.suffix.lower()

    if ext == '.xlsx':
        return pd.read_excel(ruta, engine='calamine', dtype=str)
    elif ext == ".xls":
        return pd.read_excel(ruta, engine="xlrd", dtype=str)
    elif ext == ".csv":
        return pd.read_csv(ruta, engine="c", dtype=str)
    elif ext == ".parquet":
        return pd.read_parquet(ruta)
    else:
        raise ValueError(f"Formato no soportado: {ext}")
    


def cargar_sivigila(directorio: str | Path) -> pd.DataFrame:
    """
    Carga en paralelo todos los archivos SIVIGILA de un directorio
    y los une en un único DataFrame.
    Soporta: xlsx, xls, csv, parquet.
    """
    directorio = Path(directorio)
    extensiones = {".xlsx", ".xls", ".csv", ".parquet"}
    archivos = [f for f in directorio.iterdir() if f.suffix.lower() in extensiones]

    if not archivos:
        raise FileNotFoundError(f"No se encontraron archivos en {directorio}")

    resultados: list[pd.DataFrame | None] = [None] * len(archivos)

    with ThreadPoolExecutor() as executor:
        futuros = {executor.submit(_leer_archivo, ruta): i for i, ruta in enumerate(archivos)}
        
        for futuro in as_completed(futuros):
            i = futuros[futuro]
            resultados[i] = futuro.result()

    return pd.concat([df for df in resultados if df is not None], ignore_index=True)