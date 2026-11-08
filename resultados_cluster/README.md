# Resultados de la máquina B (clúster)

Corrida completa e independiente de los notebooks 03, 05, 06 y 07 en la máquina B
(Rocky Linux, NVIDIA RTX 6000 Ada, TensorFlow en GPU), más el análisis de
sensibilidad de la búsqueda de las redes del notebook 07 (SENSIBILIDAD=1,
METODOLOGIA_PRONOSTICO.md sección 6).

Los resultados oficiales, los que usan el tablero, los notebooks y el informe, son
los de la máquina A y están en notebooks/ y outputs/ de la raíz del repositorio.
Esta carpeta guarda los de la máquina B completos y sin modificar, con la misma
estructura, para compararlos de forma transparente: si se mantienen los ganadores
de cada familia, el horizonte recomendado y el aporte del clima, y cuánto varían
las métricas entre equipos.

| Qué | Máquina A (oficial) | Máquina B (esta carpeta) |
|---|---|---|
| Notebooks ejecutados | notebooks/ | resultados_cluster/notebooks/ |
| Resultados JSON, registros, Optuna | outputs/resultados/ | resultados_cluster/outputs/resultados/ |
| Figuras | outputs/figures/ | resultados_cluster/outputs/figures/ |
| Paquetes | outputs/paquetes/ (los que se suben al tablero) | resultados_cluster/outputs/paquetes/ (no se suben) |
| Sensibilidad de las redes | — | subcarpetas _sensibilidad y notebooks/07_produccion_deep_learning_sensibilidad.ipynb |
| Hardware | METODOLOGIA_PRONOSTICO.md, sección 13 | HARDWARE_MAQUINA_B.txt |
| Registros de ejecución | logs de la máquina A | logs_cluster/ |

Esta carpeta se llena con plan_b_cluster/empaquetar.sh en el clúster, que solo
incluye lo generado allí después de lanzar la corrida y lo pone todo bajo
resultados_cluster/: al descomprimir resultados_cluster.zip en la raíz del
repositorio no se sobrescribe ningún archivo de la máquina A. Para leer los
resultados de las dos máquinas en un notebook o script, basta con las dos rutas
(por ejemplo outputs/resultados/07_resultados.json y
resultados_cluster/outputs/resultados/07_resultados.json).

El 06_resultados.json de outputs/resultados/_sensibilidad/ es la copia que usó la
sensibilidad para su tabla final de los siete candidatos (el que había al lanzarla).

Pendiente: COMPARACION.md, la comparación de las dos máquinas y de la sensibilidad
con la corrida oficial.
