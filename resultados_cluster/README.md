# Resultados de la máquina B (clúster)

Corrida completa e independiente de los notebooks 03, 05, 06 y 07 en la máquina B
(Rocky Linux, NVIDIA RTX 6000 Ada, TensorFlow en GPU), más el análisis de
sensibilidad de la búsqueda de las redes del notebook 07 (SENSIBILIDAD=1,
METODOLOGIA_PRONOSTICO.md sección 6).

Los resultados oficiales, los que usan el tablero, los notebooks y el informe, son
los de la máquina A y están en outputs/. Esta carpeta guarda los de la máquina B
completos y sin modificar, para compararlos de forma transparente: si se mantienen
los ganadores de cada familia, el horizonte recomendado y el aporte del clima, y
cuánto varían las métricas entre equipos.

Contenido esperado (pendiente de la corrida):

- notebooks/: los notebooks 03, 05, 06 y 07 ejecutados en la máquina B, y
  07_produccion_deep_learning_sensibilidad.ipynb.
- outputs/: resultados, registros, historiales de Optuna, figuras y paquetes de la
  máquina B; la sensibilidad, en sus subcarpetas _sensibilidad.
- logs_cluster/: registros de ejecución.
- COMPARACION.md: comparación con la máquina A.

Los paquetes de esta carpeta no se suben al tablero: los del tablero salen de la
máquina A.
