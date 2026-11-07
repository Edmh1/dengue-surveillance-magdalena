"""Genera outputs/RESULTADOS_PARA_INFORME.md desde los JSON de resultados de
los notebooks 03, 05, 06 y 07 (lo llama la ultima celda del 07). Nada se copia
a mano: si cambia un resultado, se vuelve a generar."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dengue.experimentacion import HORIZONTES, Salidas

FAMILIAS = {
    "estadistico": "Estadística",
    "aprendizaje_automatico": "Aprendizaje automático",
    "aprendizaje_profundo": "Aprendizaje profundo",
}


def _numero(valor, decimales: int = 2) -> str:
    if valor is None:
        return "no definido"
    return f"{valor:.{decimales}f}".replace(".", ",")


def _con_sd(bloque: dict, metrica: str, decimales: int = 2) -> str:
    texto = _numero(bloque.get(metrica), decimales)
    sd = bloque.get(f"{metrica}_sd")
    if sd is not None and bloque.get(metrica) is not None:
        texto += f" ± {_numero(sd, decimales)}"
    return texto


def _tabla(encabezados: list[str], filas: list[list[str]]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in fila) + " |" for fila in filas]
    return "\n".join(lineas)


def _leer(ruta: Path) -> dict[str, Any] | None:
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def _seccion_figuras(resultados: dict[str, dict | None]) -> str:
    filas = []
    for clave in ("03", "05", "06", "07"):
        datos = resultados.get(clave)
        if not datos:
            continue
        for figura in datos.get("figuras", []):
            filas.append([figura["ruta"], figura["notebook"], figura["descripcion"]])
    return _tabla(["Figura", "Notebook", "Qué muestra"], filas)


def _seccion_03(r03: dict) -> str:
    partes = []
    filas = []
    for nombre, entrada in r03["modelos"].items():
        h1 = entrada["prueba"]["por_horizonte"]["1"]["modelo"]
        filas.append([nombre, FAMILIAS[entrada["familia"]], _con_sd(h1, "RMSE"), _con_sd(h1, "MAE"),
                      _con_sd(h1, "MAPE"), _con_sd(h1, "R2", 3)])
    p = r03["persistencia"]["por_horizonte"]["1"]
    filas.append(["Persistencia", "control", _numero(p["RMSE"]), _numero(p["MAE"]), _numero(p["MAPE"]), _numero(p["R2"], 3)])
    partes.append("Pronóstico a un paso (H1) en la prueba de la serie de investigación, modelos con clima. En las redes, media ± desviación entre semillas.\n\n"
                  + _tabla(["Modelo", "Familia", "RMSE", "MAE", "MAPE (%)", "R²"], filas))
    for metrica, decimales in (("RMSE", 2), ("R2", 3)):
        filas = []
        for nombre, entrada in r03["modelos"].items():
            por_h = entrada["prueba"]["por_horizonte"]
            filas.append([nombre] + [_con_sd(por_h[str(h)]["modelo"], metrica, decimales) for h in HORIZONTES]
                         + [_con_sd(entrada["prueba"]["global"]["modelo"], metrica, decimales)])
        per = r03["persistencia"]
        filas.append(["Persistencia"] + [_numero(per["por_horizonte"][str(h)][metrica], decimales) for h in HORIZONTES]
                     + [_numero(per["global"][metrica], decimales)])
        etiqueta = "R²" if metrica == "R2" else metrica
        partes.append(f"Pronóstico multipaso, {etiqueta} por horizonte (semanas) y global (todos los registros de H1 a H6).\n\n"
                      + _tabla(["Modelo"] + [f"H{h}" for h in HORIZONTES] + ["Global"], filas))
    return "\n\n".join(partes)


def _seccion_05(r05: dict) -> str:
    filas_delta, filas_r2 = [], []
    for modelo, datos in r05["ablacion"].items():
        por_h = datos["por_horizonte"]
        nombre = f"{modelo} (con clima: {datos['referencia_con_clima']})"
        filas_delta.append([nombre] + [_numero(por_h[str(h)]["diferencia_R2"], 3) for h in HORIZONTES])
        filas_r2.append([modelo] + [f"{_numero(por_h[str(h)]['R2_con_clima'], 3)} / {_numero(por_h[str(h)]['R2_sin_clima'], 3)}"
                                    for h in HORIZONTES])
    return ("Diferencia de R² por horizonte, sin clima menos con clima (negativa: el clima ayuda). Mismos espacios de búsqueda y número de pruebas con y sin clima.\n\n"
            + _tabla(["Modelo"] + [f"H{h}" for h in HORIZONTES], filas_delta)
            + "\n\nR² con clima / sin clima por horizonte.\n\n"
            + _tabla(["Modelo"] + [f"H{h}" for h in HORIZONTES], filas_r2))


def _seccion_candidatos(r06: dict, r07: dict) -> str:
    candidatos = {**r06["candidatos"], **r07["candidatos"]}
    ganadores = r07["ganadores_por_familia"]
    criterios = {g["clave"]: g["criterio"] for g in r06["ganadores"].values()}
    criterios[r07["ganador"]["clave"]] = r07["ganador"]["criterio"]
    filas = []
    for clave, cand in candidatos.items():
        g = cand["prueba"]["global"]
        razon = g["modelo"]["RMSE"] / g["persistencia"]["RMSE"]
        filas.append([FAMILIAS[cand["familia"]], cand["nombre"], _con_sd(g["modelo"], "RMSE"), _con_sd(g["modelo"], "MAE"),
                      _con_sd(g["modelo"], "MAPE"), _con_sd(g["modelo"], "R2", 3), _numero(razon, 3),
                      "sí" if clave in ganadores.values() else "no"])
    p = r07["persistencia_prueba"]["global"]
    filas.append(["control", "Persistencia", _numero(p["RMSE"]), _numero(p["MAE"]), _numero(p["MAPE"]), _numero(p["R2"], 3), "1,000", ""])
    partes = ["Métricas globales de la prueba (abril de 2022 a diciembre de 2024), sobre todos los registros de H1 a H6 a la vez. Las redes, media ± desviación entre semillas.\n\n"
              + _tabla(["Familia", "Modelo", "RMSE", "MAE", "MAPE (%)", "R²", "RMSE / persistencia", "Ganador"], filas)]
    for metrica, decimales in (("RMSE", 2), ("R2", 3)):
        filas = []
        for clave, cand in candidatos.items():
            por_h = cand["prueba"]["por_horizonte"]
            filas.append([cand["nombre"]] + [_con_sd(por_h[str(h)]["modelo"], metrica, decimales) for h in HORIZONTES])
        per = r07["persistencia_prueba"]["por_horizonte"]
        filas.append(["Persistencia"] + [_numero(per[str(h)][metrica], decimales) for h in HORIZONTES])
        etiqueta = "R²" if metrica == "R2" else metrica
        partes.append(f"{etiqueta} de la prueba por horizonte.\n\n" + _tabla(["Modelo"] + [f"H{h}" for h in HORIZONTES], filas))
    lineas = []
    for familia, clave in ganadores.items():
        cand = candidatos[clave]
        lineas.append(f"- {FAMILIAS[familia]}: {cand['nombre']}, por {criterios[clave]}. Hiperparámetros: "
                      + json.dumps(cand["hiperparametros"], ensure_ascii=False) + ".")
    partes.append("Ganadores de cada familia y criterio que decidió:\n\n" + "\n".join(lineas))
    return "\n\n".join(partes)


def _seccion_2025(r06: dict, r07: dict) -> str:
    candidatos = {**r06["candidatos"], **r07["candidatos"]}
    finales = dict(r06["prueba_final_2025"])
    finales[r07["ganador"]["clave"]] = r07["prueba_final_2025"]["resumen"]
    partes = []
    for clave, metricas in finales.items():
        filas = []
        for h in HORIZONTES:
            bloque = metricas["por_horizonte"][str(h)]
            filas.append([f"H{h}", _con_sd(bloque["modelo"], "RMSE"), _con_sd(bloque["modelo"], "MAE"),
                          _con_sd(bloque["modelo"], "MAPE"), _con_sd(bloque["modelo"], "R2", 3),
                          _numero(bloque["persistencia"]["RMSE"]), _numero(bloque["modelo"]["RMSE"] / bloque["persistencia"]["RMSE"], 3)])
        g = metricas["global"]
        filas.append(["Global", _con_sd(g["modelo"], "RMSE"), _con_sd(g["modelo"], "MAE"), _con_sd(g["modelo"], "MAPE"),
                      _con_sd(g["modelo"], "R2", 3), _numero(g["persistencia"]["RMSE"]),
                      _numero(g["modelo"]["RMSE"] / g["persistencia"]["RMSE"], 3)])
        partes.append(f"{candidatos[clave]['nombre']}\n\n"
                      + _tabla(["Horizonte", "RMSE", "MAE", "MAPE (%)", "R²", "RMSE persistencia", "RMSE / persistencia"], filas))
    return "Prueba final en 2025: entrenamiento con 2007 a 2024 y un registro por semana de 2025 y horizonte.\n\n" + "\n\n".join(partes)


def _seccion_paquetes(r06: dict, r07: dict) -> str:
    filas = []
    paquetes = dict(r06.get("paquetes", {}))
    paquetes[r07["ganador"]["clave"]] = r07["paquete"]
    for clave, datos in paquetes.items():
        g = datos["metricas_prueba"]["global"]["modelo"]
        filas.append([clave, datos["zip"], datos["revision_tablero"],
                      f"{datos['rango']['fecha_primera_semana']} a {datos['rango']['fecha_ultima_semana']}",
                      f"{datos['prueba']['inicio_prueba']} a {datos['prueba']['fin_prueba']}", _numero(g["RMSE"]), _numero(g["MAE"])])
    return ("Paquetes para subir en Gestión. Las métricas son las del manifest: evaluación en el 15 % final de 2007-2025, la referencia de error que muestra el tablero.\n\n"
            + _tabla(["Modelo", "Archivo", "Revisión (paquete.revisar_paquete)", "Rango del modelo definitivo", "Prueba del manifest",
                      "RMSE global", "MAE global"], filas))


def _seccion_horizonte(r07: dict) -> str:
    propuesta = r07["horizonte_recomendado_propuesto"]
    valor = propuesta["horizonte_semanas"]
    inicio = (f"Horizonte propuesto: {valor} semanas." if valor is not None
              else "Ningún horizonte cumple la regla, ni siquiera el de 1 semana.")
    texto = (f"{inicio} Regla: {propuesta['regla'].replace('0.5', '0,5')}. Valor actual en el tablero "
             f"(HORIZONTE_RECOMENDADO_SEMANAS): {propuesta['valor_actual_tablero']}. La propuesta no modifica el tablero.")
    detalle = propuesta["detalle"]

    def celda(valor):
        if isinstance(valor, bool):
            return "sí" if valor else "no"
        if isinstance(valor, float):
            return _numero(valor, 3)
        return str(valor).replace("True", "sí").replace("False", "no")

    if detalle:
        columnas = list(detalle[0].keys())
        filas = [[celda(fila[c]) for c in columnas] for fila in detalle]
        texto += "\n\n" + _tabla(columnas, filas)
    return texto


def escribir(salidas: Salidas) -> Path:
    resultados = {clave: _leer(salidas.resultados / f"{clave}_resultados.json") for clave in ("03", "05", "06", "07")}
    rapido = any(r and r.get("modo_rapido") for r in resultados.values())
    lineas = [
        "# Resultados para el informe",
        "",
        f"Generado por el notebook 07 desde los JSON de outputs/resultados el {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
        "Las cifras de los notebooks 03 y 05 son de la serie de investigación y las de 06 y 07 de la serie del tablero: no se comparan entre sí.",
    ]
    if rapido:
        lineas += ["", "Estas cifras son del modo rápido, que solo comprueba que los notebooks corren de punta a punta: no son resultados del estudio."]
    secciones = [("1. Figuras", lambda: _seccion_figuras(resultados))]
    if resultados["03"]:
        secciones.append(("2. Notebook 03: modelos con clima", lambda: _seccion_03(resultados["03"])))
    if resultados["05"]:
        secciones.append(("3. Notebook 05: aporte del clima por horizonte", lambda: _seccion_05(resultados["05"])))
    if resultados["06"] and resultados["07"]:
        secciones += [
            ("4. Producción: candidatos y ganadores en la prueba", lambda: _seccion_candidatos(resultados["06"], resultados["07"])),
            ("5. Prueba final 2025", lambda: _seccion_2025(resultados["06"], resultados["07"])),
            ("6. Paquetes exportados", lambda: _seccion_paquetes(resultados["06"], resultados["07"])),
            ("7. Horizonte recomendado propuesto", lambda: _seccion_horizonte(resultados["07"])),
        ]
    faltan = [clave for clave, r in resultados.items() if r is None]
    if faltan:
        lineas += ["", "Faltan los resultados de los notebooks " + ", ".join(faltan) + " en este modo de ejecución."]
    for titulo, generar in secciones:
        lineas += ["", f"# {titulo}", "", generar()]
    ruta = salidas.informe / "RESULTADOS_PARA_INFORME.md"
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta
