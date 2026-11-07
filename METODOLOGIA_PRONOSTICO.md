# Metodología de pronóstico de casos de dengue (Magdalena)

Documento de referencia de la metodología con la que se eligen, evalúan y exportan los modelos de pronóstico semanal de casos de dengue que usa el tablero SIVIDEM.

# 1. Notebooks de investigación y de producción

Los notebooks de este repositorio cumplen dos papeles que se complementan. La investigación toma las decisiones de diseño del pronóstico: qué es un caso, qué transformación y qué entradas usan los modelos, qué familias son viables, cómo se evalúan y si se usa el clima. La producción aplica esas decisiones a la serie y al código del sistema: elige el modelo concreto de cada familia, ajusta sus hiperparámetros, lo evalúa y exporta lo que el tablero ejecuta.

Notebooks de investigación (01 a 05). Trabajan con la serie de investigación 2007 a 2024 y con las variables climáticas.

Notebooks de producción (06 y 07). Usan el mismo código de pronóstico del tablero (pathologies/dengue/pronostico del repositorio public-health-surveillance-system) y la misma serie que el tablero pronostica. Así, lo que se evalúa aquí es exactamente lo que el tablero ejecuta.

| Pregunta | Notebook que la responde | Decisión que sustenta |
|---|---|---|
| Qué es un caso y cómo se depuran los microdatos | 01 Análisis exploratorio | definición de caso y reglas de depuración que aplica el pipeline de limpieza del tablero |
| Qué fuente climática usar para cada variable | 02 Variables climáticas | fuente ganadora por variable, validada contra las estaciones del IDEAM |
| Cómo se transforma la serie, qué entradas reciben los modelos, qué familias son viables y cómo se evalúan | 03 Modelado con clima | transformación log1p; entradas autorregresivas, con los rezagos de 1, 2, 4 y 8 semanas y la ventana de 12 semanas como configuración de partida; las familias estadística, de aprendizaje automático y de aprendizaje profundo como candidatas; evaluación multipaso, porque la evaluación a un paso no distingue entre modelos |
| Cómo se agrupan los municipios según su clima y sus condiciones sociales | 04 Agrupamiento de municipios | caracterización territorial; no entra en el pronóstico |
| Cuánto aporta el clima frente a los rezagos de casos en cada horizonte | 05 Clima contra rezagos | el pronóstico se hace sin clima, porque su aporte en el rango operativo de 1 a 6 semanas no compensa el costo de adquirir, actualizar y validar series climáticas cada semana |
| Qué modelo concreto y qué hiperparámetros ocupan cada familia, y cómo se comporta en un año no visto | 06 y 07 Producción | con las decisiones anteriores fijas, el ganador de cada familia y sus hiperparámetros, evaluados en la serie que el tablero pronostica y con su propio código; la prueba final en 2025 y la exportación de los paquetes |

Los notebooks 06 y 07 ajustan de nuevo los hiperparámetros en lugar de reutilizar los del 03 y el 05, por tres razones. Primero, cambian las entradas: sin clima, el conjunto de predictores es otro y su óptimo también. Segundo, cambia la serie: el tablero pronostica los casos notificados, con otra asignación de la semana epidemiológica y con datos hasta 2025 (sección 2), y un óptimo encontrado en otra serie no tiene por qué serlo en esta. Tercero, el tablero ejecuta su propio código: para que lo evaluado sea exactamente lo que corre, la búsqueda, la evaluación y la exportación se hacen con las clases de pathologies/dengue/pronostico, cuyo espacio de hiperparámetros es el que esas clases aceptan.

# 2. Series de datos

Hay dos series y sus cifras no son comparables entre sí.

Serie de investigación (notebooks 03 y 05): dataset_modelado_magdalena.parquet, construido en el notebook 02. Casos con código de evento 210 o 220, municipio válido, ocurrencia en el Magdalena (cod_dpto_o 47) y tipo de caso 2, 3 o 5. La semana epidemiológica se calcula a partir de la fecha de notificación (fec_not). Periodo 2007 a 2024, con covariables climáticas.

Serie del tablero (notebooks 06 y 07): consolidado de dengue del tablero. Casos notificados con código de evento 210 o 220 (probables y confirmados, la misma definición que usan los indicadores del tablero y del protocolo de vigilancia del INS), ocurrencia en el Magdalena, por semana epidemiológica según las columnas año y semana de SIVIGILA (convención CDC), sin covariables climáticas. Periodo 2007 a 2025. Las semanas sin casos notificados se completan con cero. No se filtra por casos confirmados: el pronóstico es una herramienta de alerta temprana sobre lo que observa la vigilancia, la confirmación de laboratorio llega con retraso y su proporción varía entre años (13 % en 2010, 97 % en 2025), lo que introduciría en la serie variaciones que no son epidemiológicas.

En los años recientes los totales anuales coinciden; en los primeros años difieren hasta en un 4 % y algunos casos caen en semanas distintas por la forma de asignar la semana. Por eso las métricas de los notebooks 03 y 05 no se comparan con las de 06 y 07 ni con las que muestra el tablero.

# 3. Familias y modelos candidatos

El tablero muestra el mejor modelo de cada familia. Ninguno usa variables climáticas.

| Familia | Candidatos |
|---|---|
| Estadística | ARIMA, SARIMA, Prophet-AR |
| Aprendizaje automático | XGBoost, LightGBM |
| Aprendizaje profundo | LSTM, N-BEATS |

ARIMA y SARIMA trabajan sobre log1p(casos). Prophet-AR usa la estacionalidad anual de Prophet y como regresores rezagos de log1p(casos). XGBoost y LightGBM usan rezagos de casos, en escala original o log1p según un hiperparámetro. El conjunto de rezagos parte de 1, 2, 4 y 8 semanas y se ajusta como hiperparámetro (sección 6). LSTM y N-BEATS reciben una ventana de semanas de log1p(casos) escalada entre 0 y 1, cuyo largo también es un hiperparámetro. N-BEATS está implementado en Keras, en su versión genérica.

# 4. Periodos

Los periodos se definen sobre la serie del tablero y son los mismos para las tres familias.

| Periodo | Fechas aproximadas | Uso |
|---|---|---|
| Entrenamiento | primera semana de 2007 a abril de 2022 (85 % de 2007 a 2024) | aprender y elegir hiperparámetros |
| Prueba | abril de 2022 a diciembre de 2024 (15 % de 2007 a 2024) | comparar candidatos y elegir el ganador de cada familia |
| Prueba final | semanas de 2025 | reportar el desempeño en un año no visto; no se usa para ninguna decisión |

Cada periodo tiene un solo uso. Un periodo que sirve para decidir deja de servir como prueba, porque su resultado queda sesgado a favor de lo que se eligió con él.

2025 se reserva porque sus datos se publicaron después del cierre de la investigación (en el informe se usó para probar la carga de datos al tablero) y porque fue un año atípico: el pico llegó a 267 casos por semana, contra un máximo previo de 177 en 2018. Evaluar ahí muestra cómo se comporta cada modelo ante un brote mayor que todo lo que conocía.

# 5. Evaluación multipaso

Todas las evaluaciones (validación cruzada, prueba, prueba final y validación de la exportación) usan el mismo procedimiento walk-forward, implementado en pathologies/dengue/pronostico/evaluacion.py.

El modelo se entrena una vez con los datos anteriores al periodo evaluado y sus parámetros quedan fijos. Desde cada semana del periodo (semana de origen), el modelo recibe los casos reales hasta esa semana y pronostica las 6 semanas siguientes. Dentro de esas 6 semanas el pronóstico es recursivo: los valores de entrada que caen dentro del horizonte se completan con la propia predicción del modelo. En la semana de origen siguiente se descarta lo pronosticado y se parte otra vez de los casos reales. El error no se acumula de una semana de origen a otra; solo crece dentro de las 6 semanas, y eso es lo que mide el error por horizonte.

Se evalúan todos los horizontes: 1, 2, 3, 4, 5 y 6 semanas. Cada horizonte se mide por separado, comparando cada pronóstico con el caso real de su semana objetivo, y solo cuentan las semanas objetivo que caen dentro del periodo evaluado.

Métricas por horizonte: RMSE, MAE, MAPE (excluyendo semanas con cero casos reales) y R². Métricas globales: las mismas fórmulas aplicadas a todos los registros de los horizontes 1 a 6 a la vez, igual que el tablero (no son el promedio de las seis métricas por horizonte). La persistencia (pronosticar que todas las semanas siguientes repiten la última observada) se mide en las mismas semanas como línea base.

# 6. Ajuste de hiperparámetros

Los hiperparámetros se eligen solo dentro del periodo de entrenamiento; el periodo de prueba nunca se usa para elegirlos.

Búsqueda. Se hace con Optuna, con el muestreador TPE y una semilla fija, de modo que la búsqueda se repite igual en cada corrida. Los rangos son continuos donde el hiperparámetro lo es, en escala logarítmica para las magnitudes que varían en órdenes de magnitud (tasa de aprendizaje, regularización, escalas previas de Prophet, número de árboles), y categóricos solo para las elecciones que de verdad lo son (optimizador, modo de la estacionalidad, transformación, conjunto de rezagos). En producción el espacio de cada modelo se limita a los hiperparámetros que acepta su clase en el código del tablero. Cada notebook muestra, por modelo, el hiperparámetro, su rango, la escala y el motivo, el número de pruebas según el costo del modelo, y guarda el historial completo de cada búsqueda.

Objetivo. Optuna minimiza el RMSE global de los horizontes 1 a 6 dentro del entrenamiento, calculado sobre todos los registros de H1 a H6 a la vez. Es el mismo criterio con que se elige el ganador de cada familia (sección 7), así que el ajuste y la selección persiguen lo mismo. El MAE se registra siempre.

Estadísticos y aprendizaje automático (esquema 85/15). Dentro del 85 % de entrenamiento se usa validación cruzada temporal con tres cortes sucesivos. Cada corte reproduce la partición de la prueba sobre la serie que termina en él: entrena con su primer 85 % y evalúa el 15 % final con el procedimiento de la sección 5. Los tres bloques evaluados son contiguos y no se solapan: mayo de 2016 a enero de 2018, enero de 2018 a diciembre de 2019 y diciembre de 2019 a abril de 2022, y cubren años de baja transmisión y los brotes de 2018 y 2019. El valor que se optimiza es el promedio del RMSE global de los tres cortes. En ARIMA y SARIMA la diferenciación estacional D sale de las pruebas OCSB y Canova-Hansen, que indican D = 0. La diferenciación regular d se explora entre 0 y 1 porque las pruebas no la fijan: dentro del entrenamiento ADF y KPSS coinciden en que log1p(casos) es estacionaria sin diferenciar, y sobre 2007 a 2024 completo coinciden recién con una diferencia. Con d = 0 el modelo lleva una constante, que es el nivel medio de log1p(casos). Se buscan además los órdenes p, q, P y Q, y el AIC de cada configuración se registra como referencia.

Aprendizaje profundo (esquema 70/15/15). El 85 % se divide en entrenamiento (2007 a agosto de 2019, 70 %) y validación (agosto de 2019 a abril de 2022, 15 %). La validación cumple dos funciones: decide cuándo detener el entrenamiento (parada temprana, restaurando los mejores pesos) y es el periodo con el que Optuna compara configuraciones, con el mismo procedimiento de la sección 5. Las redes necesitan este bloque aparte porque la parada temprana no puede usar el periodo de prueba. Para que las configuraciones malas no consuman el presupuesto, la búsqueda usa poda por mediana: si después de una semilla el RMSE de una configuración es peor que la mediana de las anteriores en ese mismo punto, se descarta sin entrenar las demás.

Estabilidad de las redes. Una misma configuración da resultados distintos según la semilla aleatoria: con N-BEATS se observaron RMSE de 16,6 y 23,2 con la misma configuración y los mismos datos. Por eso cada configuración se entrena con 5 semillas, con el determinismo de TensorFlow activado, y se registran la media y la dispersión. Regla de elección: entre las configuraciones cuyo RMSE global medio está a menos de un 5 % del mejor, se elige la de menor dispersión entre semillas. No se usan ensambles.

# 7. Selección del ganador de cada familia

Se realiza en el periodo de prueba. Cada candidato, con su mejor configuración, se entrena con el 85 % y se evalúa con el procedimiento de la sección 5 en los horizontes 1 a 6.

1. Métrica principal. El RMSE global de la prueba, calculado sobre todos los registros de H1 a H6 a la vez. Es la misma métrica global que el tablero guarda en el manifest de cada versión (evaluacion.metricas_desde_registros) y que muestra en la fila global de la pestaña Pronóstico. No es el promedio de los seis RMSE por horizonte.
2. Desempate. Si dos candidatos de una familia quedan a menos de un 2 % de RMSE global entre sí, gana el de menor MAE global. En aprendizaje profundo el RMSE de cada candidato es la media de sus 5 semillas y, si el empate persiste (los MAE también quedan a menos de un 2 %), gana el de menor desviación entre semillas.
3. Comparación contra la persistencia. Se comprueba si el ganador supera a la persistencia, para saber si la complejidad adicional está justificada. La persistencia es un control: no decide la elección.
4. Reporte completo. MAE, RMSE, MAPE y R² globales y en cada horizonte de 1 a 6, junto con la persistencia.

El tablero ofrece pronósticos de 1 a 6 semanas, así que el modelo se elige por su desempeño en todo el rango que se le muestra al usuario. Los horizontes largos pesan más en el RMSE global porque sus errores son mayores, y es deliberado: la evaluación a un paso muestra que los modelos se parecen a corto plazo y se separan al alejarse el horizonte, que es donde la elección importa. El RMSE manda sobre el MAE porque castiga más los errores grandes, y en vigilancia el error más costoso es subestimar un brote. El horizonte recomendado (sección 9) es una decisión aparte: se fija después, con los resultados, y no cambia qué modelo ganó.

# 8. Prueba final con 2025

Los tres ganadores se entrenan con 2007 a 2024 y se evalúan en cada semana de 2025 con el procedimiento de la sección 5 (unas 52 semanas de origen por 6 horizontes). Las redes se evalúan con sus 5 semillas.

Se calcula el reporte completo: MAE, RMSE, MAPE y R² en los horizontes 1 a 6 y la comparación contra la persistencia, más una gráfica de los casos reales de 2025 contra lo pronosticado a 1 y 4 semanas. Ningún resultado de esta prueba modifica las decisiones anteriores.

# 9. Horizonte recomendado

Se decide con los resultados de la prueba y de la prueba final: el horizonte máximo en el que el error sigue siendo útil y el ganador supera a la persistencia. En el tablero se configura en HORIZONTE_RECOMENDADO_SEMANAS (pathologies/dengue/pronostico/configuracion.py).

# 10. Exportación al tablero

Cada ganador se exporta con la función entrenar_evaluar_y_guardar de pathologies/dengue/pronostico/paquete.py, con el rango completo 2007 a 2025, una semilla fija y el determinismo activado. La función ejecuta, en este orden:

1. Entrena el modelo de evaluación con el 85 % del rango (2007 a febrero de 2023).
2. Desde cada semana de origen pronostica las 6 semanas siguientes con el procedimiento de la sección 5 y conserva los registros cuya semana objetivo pertenece al 15 % restante (febrero de 2023 a diciembre de 2025).
3. Guarda esos resultados individuales en pronosticos_prueba.csv (casos reales, pronóstico, errores y persistencia) y calcula desde ellos las métricas globales y por horizonte del manifest, con la cantidad de registros de cada una.
4. Entrena el modelo definitivo con todo el rango 2007 a 2025 y lo guarda en el formato nativo de su librería. El modelo de evaluación se descarta; quedan sus métricas y sus registros.

El resultado se empaqueta con exportar_zip en un archivo .zip por familia, que el perfil de administración sube desde Gestión. El tablero lo revisa sin entrenar: formato, serie, librerías y versiones, archivos, que las métricas del manifest se reconstruyan desde el CSV, y que el modelo cargue y pronostique. La estructura del paquete, los formatos nativos de cada modelo y un script completo de exportación están en docs/pronostico.md del repositorio del tablero.

El modelo definitivo se entrena con 2025 porque el tablero pronostica a partir de hoy y debe conocer el nivel reciente de casos y el brote de 2025. Sus hiperparámetros son los elegidos en la sección 7; solo cambia la cantidad de datos.

# 11. Qué muestra el tablero y de dónde sale cada cifra

| Lugar | Origen | Qué dice |
|---|---|---|
| Documento técnico y pestaña Estudio de modelado | secciones 7 y 8 | por qué se eligió cada modelo y cómo le fue en 2025 |
| Pestaña Pronóstico en vivo, rango orientativo y métricas de la prueba | métricas del manifest calculadas en el paso 3 de la sección 10 | rendimiento histórico del modelo de evaluación en la prueba, por horizonte y global; referencia del error esperado, no el error de los pronósticos futuros |
| Pestaña Pronóstico, modo de semana pasada | pronosticos_prueba.csv (sección 10) | pronóstico individual que hizo el modelo de evaluación sin haber visto esas semanas, contra lo que pasó |
| Fundamentación, comparación con la persistencia | manifest de cada versión activa | si el modelo activo supera a la persistencia en cada horizonte |

# 12. Notebooks y orden de ejecución

| Notebook | Serie | Contenido | Requiere GPU |
|---|---|---|---|
| 01 Análisis exploratorio | investigación | limpieza y consolidación de los microdatos SIVIGILA | no |
| 02 Variables climáticas | investigación | variables climáticas por fuente, validación contra estaciones del IDEAM y dataset semanal de modelado | no |
| 04 Agrupamiento de municipios | investigación | agrupación de municipios según su clima | no |
| 03 Modelado con clima | investigación | comparación de modelos con covariables climáticas, horizontes 1 a 6, redes con 5 semillas; guarda sus resultados en JSON | sí |
| 05 Clima contra rezagos | investigación | aporte del clima frente a los rezagos de casos por horizonte (1 a 6), redes con 5 semillas; lee los resultados del 03 | sí |
| 06 Producción: estadísticos y aprendizaje automático | tablero | secciones 6 a 8 para ARIMA, SARIMA, Prophet-AR, XGBoost y LightGBM; exporta 2 paquetes | no |
| 07 Producción: aprendizaje profundo | tablero | secciones 6 a 8 para LSTM y N-BEATS, tabla final de los 7 candidatos y horizonte recomendado; exporta 1 paquete | sí |

Todas las gráficas se guardan en outputs/figures a 300 dpi, con un ancho pensado para el documento técnico.

Orden: 01, 02, 04, 03, 05, 06, 07. Las instrucciones de instalación para Windows y Linux están en ENTORNO.md.
