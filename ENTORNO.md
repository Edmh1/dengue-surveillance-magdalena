# Entorno de ejecución

Instalación del entorno de los notebooks, en Windows y en Linux con GPU NVIDIA, y cómo ejecutarlos.

# 1. Requisitos

- Python 3.12.
- Una copia del repositorio del tablero (public-health-surveillance-system) con su consolidado de dengue en data/dengue/consolidado/dengue_consolidado.parquet. Los notebooks 06 y 07 importan su código de pronóstico (pathologies/dengue/pronostico) y leen esa serie.
- Para el modo completo de 03, 05 y 07, conviene una GPU NVIDIA en Linux o en WSL2.

# 2. Instalación en Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

En Windows TensorFlow funciona solo con CPU: la LSTM del 03 y el 05 y las redes del 07 se entrenan en CPU. PyTorch sí puede usar la GPU en Windows; para que darts entrene N-BEATS en la GPU (notebooks 03 y 05), reinstala torch con CUDA después del requirements:

```bash
pip install torch==2.12.1+cu126 --index-url https://download.pytorch.org/whl/cu126
```

Las GPU de la serie RTX 50 (arquitectura Blackwell) no funcionan con las builds cu126 de PyTorch: necesitan CUDA 12.8 o superior. En la corrida oficial (RTX 5050) se usó:

```bash
pip install torch==2.14.1+cu130 --index-url https://download.pytorch.org/whl/cu130
```

Para ejecutar los notebooks con papermill (guarda el notebook después de cada celda y deja ver el avance en un log), además de nbconvert: `pip install papermill`.

# 3. Instalación en Linux con GPU NVIDIA

TensorFlow solo usa la GPU en Linux o en WSL2. Con el controlador de NVIDIA instalado (nvidia-smi debe responder):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install "tensorflow[and-cuda]>=2.16,<3"
pip install torch==2.12.1+cu126 --index-url https://download.pytorch.org/whl/cu126
```

tensorflow[and-cuda] trae las librerías de CUDA y cuDNN que necesita TensorFlow. torch con CUDA hace falta para que darts entrene N-BEATS en la GPU en el 03 y el 05.

Comprobación:

```bash
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
python -c "import torch; print(torch.cuda.is_available())"
```

La primera línea debe listar la GPU y la segunda imprimir True. Cada notebook pesado imprime además los dispositivos que ve al empezar.

# 4. Versiones compatibles con el tablero

El tablero rechaza un paquete exportado con otra versión mayor de la librería de su modelo (paquete.comprobar_compatibilidad compara el campo librerias del manifest con lo instalado en el servidor). Por eso requirements.txt fija la versión mayor de cada librería que se exporta:

| Librería | Modelos | Versión mayor | Instalada en este repositorio | Instalada en el tablero |
|---|---|---|---|---|
| statsmodels | ARIMA, SARIMA | 0 | 0.15.0 | 0.15.0 |
| prophet | Prophet-AR | 1 | 1.5.0 | 1.4.0 |
| xgboost | XGBoost | 3 | 3.4.1 | 3.4.1 |
| lightgbm | LightGBM | 4 | 4.7.0 | 4.7.0 |
| tensorflow | LSTM, N-BEATS | 2 | 2.21.0 | 2.22.0rc0 |
| keras | LSTM, N-BEATS | 3 | 3.15.1 | 3.16.0.dev |

La columna de este repositorio corresponde al entorno de la corrida oficial del 7 de noviembre de 2026 (METODOLOGIA_PRONOSTICO.md, sección 13), con la que se exportaron los paquetes.

Las columnas de versiones instaladas corresponden a los entornos locales de los dos repositorios; las versiones menores pueden diferir, y el tablero las acepta y las registra. El servidor del tablero instala sus librerías al construir la imagen Docker, sin versiones fijas: antes de subir un paquete conviene revisar que la imagen tenga la misma versión mayor. Los notebooks 06 y 07 revisan cada paquete exportado con paquete.revisar_paquete, la misma revisión que hace el tablero al subirlo, contra las versiones instaladas en el equipo donde se exportó.

# 5. Ruta del repositorio del tablero

Los notebooks 06 y 07 leen la ruta del tablero en un solo lugar, la celda de configuración del inicio:

```python
RUTA_TABLERO = os.environ.get("RUTA_TABLERO", r"C:\Users\edavi\PROYECTOS\public-health-surveillance-system")
```

En otro equipo basta con definir la variable de entorno antes de abrir Jupyter o de ejecutar nbconvert, sin tocar el notebook:

```bash
export RUTA_TABLERO=/home/usuario/public-health-surveillance-system      # Linux
set RUTA_TABLERO=C:\ruta\a\public-health-surveillance-system              # Windows (cmd)
```

El notebook comprueba que la ruta tenga pathologies/dengue/pronostico y el consolidado, y la agrega a sys.path. Ninguna otra celda usa rutas del tablero.

USUARIO_TABLERO (opcional) define el usuario que queda en el manifest de los paquetes; por defecto es el usuario del sistema.

# 6. Modo rápido y modo completo

Los notebooks 03, 05, 06 y 07 empiezan con una celda de configuración con MODO_RAPIDO.

| | MODO_RAPIDO = True | MODO_RAPIDO = False |
|---|---|---|
| Para qué | comprobar que el notebook corre de punta a punta y produce todos sus archivos | la metodología completa |
| Pruebas de Optuna | 3 por modelo | las de la tabla de cada notebook (de 20 a 80 según el costo del modelo) |
| Semillas de las redes | 1 | 5 |
| Épocas de las redes | 4, paciencia 2 | hasta 200, paciencia 20 |
| Validación cruzada | un corte (en 03 y 05, además, un origen de cada tres) | tres cortes, todos los orígenes |
| Salidas | subcarpetas _rapido de outputs | outputs |

Las salidas del modo rápido nunca pisan las definitivas. El 05 lee el JSON del 03 y el 07 lee el del 06 en el mismo modo, así que el orden de ejecución es el mismo en los dos modos.

La variable de entorno MODO_RAPIDO, con valor 0 o 1, tiene prioridad sobre el valor escrito en la celda, para poder elegir el modo desde la línea de comandos.

# 7. Ejecución

Orden: 01, 02, 04, 03, 05, 06, 07. El 01, el 02 y el 04 no dependen del modo. El 02 descarga datos climáticos (Open-Meteo, NASA POWER, Earth Engine), así que necesita red y credenciales de Earth Engine.

Ejecución desde la línea de comandos, en el modo completo y en orden, desde la carpeta notebooks:

```bash
cd notebooks
export MODO_RAPIDO=0
export RUTA_TABLERO=/ruta/a/public-health-surveillance-system
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 03_dengue_modeling.ipynb
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 05_dengue_ablacion_clima_vs_lags.ipynb
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 06_produccion_estadisticos_ml.ipynb
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 07_produccion_deep_learning.ipynb
```

timeout=-1 quita el límite de tiempo por celda: las búsquedas de las redes duran horas. Para una corrida larga en un servidor conviene lanzarla dentro de tmux o screen, o con nohup, para que no se corte si se cierra la sesión.

Dependencias entre notebooks: el 05 lee el JSON del 03 y el 07 lee el del 06; no hay otras. Las dos cadenas (03 y luego 05; 06 y luego 07) pueden correr en paralelo, en dos sesiones de tmux, y así el tiempo total es el de la cadena más larga. El 06 no usa GPU.

Duración del modo completo. La estimación previa salió del modo rápido (una época de una red de tamaño medio cuesta del orden de medio segundo en CPU); la última columna es lo que tardó la corrida oficial (i7-13650HX con 14 núcleos, TensorFlow en CPU, las dos cadenas en paralelo):

| Notebook | Parte más cara | Estimación | Corrida oficial |
|---|---|---|---|
| 03 | búsquedas de LSTM y N-BEATS (20 pruebas de 5 semillas cada una) y SARIMA con s = 52 | 3 a 7 horas | 94 minutos |
| 05 | búsquedas de LSTM y N-BEATS | 2 a 6 horas | 154 minutos |
| 06 | SARIMA (25 pruebas de 1 a 4 minutos) | 1 a 2 horas | 67 minutos |
| 07 | búsquedas de LSTM y N-BEATS (30 pruebas de 5 semillas cada una) | 2 a 6 horas | 150 minutos |

El modo de sensibilidad del 07 (SENSIBILIDAD=1, METODOLOGIA_PRONOSTICO.md sección 6) sube el presupuesto de las redes (80 pruebas LSTM, 60 N-BEATS) y permite redes más profundas y anchas, así que tarda bastante más. Antes de lanzarlo en el clúster conviene la prueba de humo (bash plan_b_cluster/correr.sh humo, de 5 a 10 minutos), que comprueba la GPU, los espacios, el determinismo de las redes más grandes y una búsqueda corta.

El rango depende de cuántas configuraciones pode Optuna y del tamaño de las redes que proponga; en redes tan pequeñas la GPU acelera poco frente a una CPU moderna. El número de pruebas de cada modelo está en PRUEBAS de src/dengue/investigacion.py (03 y 05) y de src/dengue/produccion.py (06 y 07).

Avisos para el equipo con GPU:

- Si TensorFlow no ve la GPU, el notebook corre igual en CPU; la línea de dispositivos del inicio lo muestra.
- Con el determinismo activado, TensorFlow lanza un error si una operación no tiene versión determinista en GPU. Las capas que usan estas redes (LSTM, densas, dropout, suma y resta) la tienen; si apareciera ese error, el mensaje nombra la operación.
- Los resultados de las redes en GPU no son idénticos bit a bit a los de una corrida en CPU; dentro del mismo equipo sí se repiten.
- USUARIO_TABLERO queda en el manifest de los paquetes; conviene definirlo antes de correr el 06 y el 07.

Determinismo. Las redes se entrenan con keras.utils.set_random_seed y tf.config.experimental.enable_op_determinism; darts, con random_state y torch.use_deterministic_algorithms. La celda de configuración fija CUBLAS_WORKSPACE_CONFIG antes de importar las librerías, como pide CUDA para que sus operaciones sean deterministas. Con una misma semilla, el mismo equipo y las mismas versiones, una red da el mismo resultado; entre CPU y GPU, o entre equipos distintos, los resultados pueden diferir en los últimos decimales.

# 8. Salidas

| Ruta | Contenido |
|---|---|
| outputs/figures/carpeta del notebook | figuras a 300 dpi y 6,5 pulgadas de ancho (eda, climate, clustering, model, ablacion, produccion_estadisticos_ml, produccion_deep_learning) |
| outputs/resultados/NN_resultados.json | métricas, hiperparámetros, figuras y tiempos de cada notebook |
| outputs/resultados/optuna | historial completo de cada búsqueda de Optuna, en JSON y CSV |
| outputs/resultados/registros | registros walk-forward de la prueba y de 2025 (mismo formato que pronosticos_prueba.csv del tablero) |
| outputs/paquetes | paquetes .zip para subir en Gestión, sus carpetas de trabajo y la copia revisada |
| outputs/RESULTADOS_PARA_INFORME.md | tablas y lista de figuras para el informe, generado por el 07 desde los JSON |
