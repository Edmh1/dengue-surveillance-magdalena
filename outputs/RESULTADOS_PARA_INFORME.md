# Resultados para el informe

Generado por el notebook 07 desde los JSON de outputs/resultados el 2026-11-07 17:12. Las cifras de los notebooks 03 y 05 son de la serie de investigación y las de 06 y 07 de la serie del tablero: no se comparan entre sí.

# 1. Figuras

| Figura | Notebook | Qué muestra |
|---|---|---|
| outputs/figures/model/serie_casos.png | 03 | Serie semanal de casos de dengue del Magdalena, 2007 a 2024 (serie de investigación) |
| outputs/figures/model/varianza_movil.png | 03 | Serie observada y su varianza móvil de 12 semanas: la dispersión crece con el nivel de casos |
| outputs/figures/model/comparacion_cv_movil.png | 03 | Serie original y log1p con su coeficiente de variación móvil: log1p estabiliza la dispersión |
| outputs/figures/model/descomposicion_serie.png | 03 | Descomposición STL de log1p(casos): tendencia-ciclo, estacionalidad anual y ruido |
| outputs/figures/model/acf_pacf.png | 03 | Serie log1p diferenciada con su ACF y PACF hasta 104 semanas |
| outputs/figures/model/train_val_test_split.png | 03 | División 70/15/15 de la serie de investigación: entrenamiento, validación y prueba |
| outputs/figures/model/distribucion_variables.png | 03 | Distribución de los casos y de las variables climáticas candidatas (train más val) |
| outputs/figures/model/correlacion_spearman.png | 03 | Correlación de Spearman entre las variables climáticas candidatas |
| outputs/figures/model/correlacion_spearman_final.png | 03 | Correlación de Spearman del conjunto climático reconstruido |
| outputs/figures/model/exogenas_climaticas.png | 03 | Series de las variables climáticas exógenas del SARIMAX |
| outputs/figures/model/sarimax_pred.png | 03 | SARIMAX con clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/model/prophet_pred.png | 03 | Prophet con clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/model/xgb_feature_importance.png | 03 | XGBoost con clima: importancia (ganancia) de las 10 variables principales |
| outputs/figures/model/xgb_pred.png | 03 | XGBoost con clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/model/lgbm_feature_importance.png | 03 | LightGBM con clima: importancia (ganancia) de las 10 variables principales |
| outputs/figures/model/lgbm_pred.png | 03 | LightGBM con clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/model/lstm_pred.png | 03 | LSTM con clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas (semilla 42) |
| outputs/figures/model/nbeats_pred.png | 03 | N-BEATS con clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas (semilla 42) |
| outputs/figures/model/comparacion_modelos.png | 03 | Métricas a un paso (H1) de cada modelo con clima y de la persistencia en la prueba |
| outputs/figures/model/multistep_heatmaps.png | 03 | R2, RMSE y MAE por modelo con clima y horizonte (1 a 6 semanas) en la prueba, con la persistencia |
| outputs/figures/model/multistep_horizontes.png | 03 | R2 y RMSE de cada modelo con clima según el horizonte, frente a la persistencia |
| outputs/figures/ablacion/acf_pacf_sin_clima.png | 05 | Serie log1p diferenciada de train más val con su ACF y PACF hasta 104 semanas |
| outputs/figures/ablacion/arima_pred.png | 05 | ARIMA sin clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/ablacion/sarima_pred.png | 05 | SARIMA sin clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/ablacion/prophet_ar_pred.png | 05 | Prophet-AR sin clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/ablacion/xgb_pred.png | 05 | XGBoost sin clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/ablacion/lgbm_pred.png | 05 | LightGBM sin clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas |
| outputs/figures/ablacion/lstm_pred.png | 05 | LSTM sin clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas (semilla 42) |
| outputs/figures/ablacion/nbeats_pred.png | 05 | N-BEATS sin clima: casos reales de la prueba contra los pronósticos a 1 y 4 semanas (semilla 42) |
| outputs/figures/ablacion/comparacion_un_paso.png | 05 | R2 y RMSE a un paso (H1) de cada modelo con clima (notebook 03) y sin clima, con la persistencia |
| outputs/figures/ablacion/multipaso_sin_clima.png | 05 | R2 y RMSE de cada modelo sin clima por horizonte (1 a 6 semanas) en la prueba, con la persistencia |
| outputs/figures/ablacion/delta_r2_horizonte.png | 05 | Diferencia de R2 (sin clima menos con clima) por modelo y horizonte en la prueba |
| outputs/figures/ablacion/r2_con_sin_horizonte.png | 05 | R2 por horizonte de cada familia con clima (notebook 03) y sin clima, frente a la persistencia |
| outputs/figures/produccion_estadisticos_ml/prueba_ganadores.png | 06 | Ganadores estadístico y de aprendizaje automático: casos reales de la prueba (abril de 2022 a diciembre de 2024) contra los pronósticos a 1 y 4 semanas |
| outputs/figures/produccion_estadisticos_ml/prueba_final_2025.png | 06 | Prueba final 2025 de los ganadores estadístico y de aprendizaje automático: casos reales contra los pronósticos a 1 y 4 semanas |
| outputs/figures/produccion_estadisticos_ml/importancia_hiperparametros_prophet_ar.png | 06 | Importancia de los hiperparámetros (fANOVA de Optuna) del ganador Prophet-AR |
| outputs/figures/produccion_estadisticos_ml/importancia_hiperparametros_xgboost.png | 06 | Importancia de los hiperparámetros (fANOVA de Optuna) del ganador XGBoost |
| outputs/figures/produccion_deep_learning/importancia_hiperparametros_lstm.png | 07 | Importancia de los hiperparámetros (fANOVA de Optuna) del ganador LSTM |
| outputs/figures/produccion_deep_learning/linea_de_tiempo_periodos.png | 07 | Línea de tiempo de los periodos: entrenamiento 85 %, cortes de validación cruzada, validación de las redes (70/15/15), prueba, prueba final 2025 y la partición 85/15 con que el tablero evalúa el paquete exportado |
| outputs/figures/produccion_deep_learning/metricas_por_horizonte_candidatos.png | 07 | RMSE, MAE, MAPE y R2 por horizonte de los siete candidatos y la persistencia en la prueba; las redes con la media de las semillas |
| outputs/figures/produccion_deep_learning/degradacion_r2_horizonte.png | 07 | R2 según el horizonte: los siete candidatos en la prueba y los tres ganadores en 2025, con la persistencia |
| outputs/figures/produccion_deep_learning/ganadores_contra_persistencia.png | 07 | Razón entre el RMSE de cada ganador y el de la persistencia por horizonte, en la prueba y en 2025 |
| outputs/figures/produccion_deep_learning/prueba_final_2025_ganadores.png | 07 | Casos reales de 2025 contra los pronósticos a 1 y 4 semanas de los tres ganadores (la red con la semilla exportada y el rango de sus semillas) |

# 2. Notebook 03: modelos con clima

Pronóstico a un paso (H1) en la prueba de la serie de investigación, modelos con clima. En las redes, media ± desviación entre semillas.

| Modelo | Familia | RMSE | MAE | MAPE (%) | R² |
|---|---|---|---|---|---|
| SARIMAX | Estadística | 13,05 | 9,16 | 22,28 | 0,851 |
| Prophet | Estadística | 11,67 | 8,47 | 22,65 | 0,881 |
| XGBoost | Aprendizaje automático | 13,64 | 9,92 | 24,51 | 0,838 |
| LightGBM | Aprendizaje automático | 17,20 | 11,51 | 26,52 | 0,742 |
| LSTM | Aprendizaje profundo | 16,11 ± 1,90 | 10,83 ± 1,28 | 22,80 ± 1,54 | 0,771 ± 0,052 |
| N-BEATS | Aprendizaje profundo | 12,36 ± 0,62 | 8,72 ± 0,31 | 21,30 ± 0,52 | 0,867 ± 0,014 |
| Persistencia | control | 13,21 | 9,95 | 26,11 | 0,848 |

Pronóstico multipaso, RMSE por horizonte (semanas) y global (todos los registros de H1 a H6).

| Modelo | H1 | H2 | H3 | H4 | H5 | H6 | Global |
|---|---|---|---|---|---|---|---|
| SARIMAX | 13,05 | 14,49 | 16,60 | 18,76 | 20,82 | 22,78 | 18,08 |
| Prophet | 11,67 | 13,07 | 14,86 | 16,40 | 18,03 | 19,64 | 15,85 |
| XGBoost | 13,64 | 14,84 | 16,42 | 18,49 | 20,81 | 22,79 | 18,12 |
| LightGBM | 17,20 | 18,99 | 20,65 | 22,32 | 24,47 | 26,48 | 21,91 |
| LSTM | 16,11 ± 1,90 | 18,85 ± 2,00 | 22,16 ± 2,17 | 25,18 ± 2,38 | 27,98 ± 2,52 | 30,51 ± 2,60 | 24,00 ± 2,21 |
| N-BEATS | 12,36 ± 0,62 | 13,99 ± 0,93 | 16,09 ± 0,92 | 17,65 ± 1,07 | 19,37 ± 1,16 | 21,08 ± 1,30 | 17,02 ± 1,02 |
| Persistencia | 13,21 | 14,01 | 17,54 | 19,94 | 22,21 | 24,93 | 19,11 |

Pronóstico multipaso, R² por horizonte (semanas) y global (todos los registros de H1 a H6).

| Modelo | H1 | H2 | H3 | H4 | H5 | H6 | Global |
|---|---|---|---|---|---|---|---|
| SARIMAX | 0,851 | 0,817 | 0,760 | 0,693 | 0,622 | 0,547 | 0,715 |
| Prophet | 0,881 | 0,851 | 0,807 | 0,765 | 0,716 | 0,663 | 0,781 |
| XGBoost | 0,838 | 0,808 | 0,765 | 0,702 | 0,622 | 0,547 | 0,713 |
| LightGBM | 0,742 | 0,685 | 0,628 | 0,565 | 0,478 | 0,388 | 0,581 |
| LSTM | 0,771 ± 0,052 | 0,687 ± 0,066 | 0,568 ± 0,084 | 0,443 ± 0,105 | 0,313 ± 0,124 | 0,183 ± 0,140 | 0,494 ± 0,093 |
| N-BEATS | 0,867 ± 0,014 | 0,829 ± 0,023 | 0,773 ± 0,026 | 0,727 ± 0,033 | 0,672 ± 0,040 | 0,611 ± 0,048 | 0,746 ± 0,031 |
| Persistencia | 0,848 | 0,829 | 0,731 | 0,653 | 0,569 | 0,458 | 0,681 |

# 3. Notebook 05: aporte del clima por horizonte

Diferencia de R² por horizonte, sin clima menos con clima (negativa: el clima ayuda). Mismos espacios de búsqueda y número de pruebas con y sin clima.

| Modelo | H1 | H2 | H3 | H4 | H5 | H6 |
|---|---|---|---|---|---|---|
| ARIMA (con clima: SARIMAX) | -0,001 | -0,019 | -0,032 | -0,047 | -0,065 | -0,087 |
| SARIMA (con clima: SARIMAX) | -0,001 | -0,019 | -0,032 | -0,047 | -0,065 | -0,087 |
| Prophet-AR (con clima: Prophet) | -0,026 | -0,051 | -0,086 | -0,094 | -0,149 | -0,221 |
| XGBoost (con clima: XGBoost) | 0,004 | 0,007 | -0,025 | -0,044 | -0,120 | -0,111 |
| LightGBM (con clima: LightGBM) | 0,035 | 0,043 | 0,047 | 0,058 | 0,055 | 0,089 |
| LSTM (con clima: LSTM) | 0,088 | 0,112 | 0,135 | 0,175 | 0,215 | 0,251 |
| N-BEATS (con clima: N-BEATS) | -0,019 | -0,042 | -0,082 | -0,124 | -0,174 | -0,223 |

R² con clima / sin clima por horizonte.

| Modelo | H1 | H2 | H3 | H4 | H5 | H6 |
|---|---|---|---|---|---|---|
| ARIMA | 0,851 / 0,850 | 0,817 / 0,798 | 0,760 / 0,728 | 0,693 / 0,646 | 0,622 / 0,557 | 0,547 / 0,460 |
| SARIMA | 0,851 / 0,850 | 0,817 / 0,798 | 0,760 / 0,728 | 0,693 / 0,646 | 0,622 / 0,557 | 0,547 / 0,460 |
| Prophet-AR | 0,881 / 0,855 | 0,851 / 0,800 | 0,807 / 0,721 | 0,765 / 0,671 | 0,716 / 0,568 | 0,663 / 0,443 |
| XGBoost | 0,838 / 0,842 | 0,808 / 0,815 | 0,765 / 0,740 | 0,702 / 0,658 | 0,622 / 0,502 | 0,547 / 0,436 |
| LightGBM | 0,742 / 0,777 | 0,685 / 0,729 | 0,628 / 0,675 | 0,565 / 0,624 | 0,478 / 0,532 | 0,388 / 0,477 |
| LSTM | 0,771 / 0,859 | 0,687 / 0,799 | 0,568 / 0,704 | 0,443 / 0,617 | 0,313 / 0,527 | 0,183 / 0,434 |
| N-BEATS | 0,867 / 0,848 | 0,829 / 0,787 | 0,773 / 0,691 | 0,727 / 0,603 | 0,672 / 0,498 | 0,611 / 0,388 |

# 4. Producción: candidatos y ganadores en la prueba

Métricas globales de la prueba (abril de 2022 a diciembre de 2024), sobre todos los registros de H1 a H6 a la vez. Las redes, media ± desviación entre semillas.

| Familia | Modelo | RMSE | MAE | MAPE (%) | R² | RMSE / persistencia | Ganador |
|---|---|---|---|---|---|---|---|
| Estadística | ARIMA | 18,70 | 12,75 | 27,57 | 0,691 | 1,032 | no |
| Estadística | SARIMA | 18,27 | 12,91 | 30,80 | 0,705 | 1,008 | no |
| Estadística | Prophet-AR | 16,21 | 11,65 | 29,29 | 0,768 | 0,894 | sí |
| Aprendizaje automático | XGBoost | 20,15 | 13,47 | 31,29 | 0,641 | 1,112 | sí |
| Aprendizaje automático | LightGBM | 20,90 | 14,45 | 34,48 | 0,613 | 1,153 | no |
| Aprendizaje profundo | LSTM | 18,86 ± 0,38 | 12,93 ± 0,12 | 28,50 ± 0,40 | 0,685 ± 0,013 | 1,041 | sí |
| Aprendizaje profundo | N-BEATS | 20,41 ± 1,60 | 13,43 ± 0,97 | 27,39 ± 1,30 | 0,629 ± 0,058 | 1,127 | no |
| control | Persistencia | 18,12 | 12,96 | 31,84 | 0,709 | 1,000 |  |

RMSE de la prueba por horizonte.

| Modelo | H1 | H2 | H3 | H4 | H5 | H6 |
|---|---|---|---|---|---|---|
| ARIMA | 12,01 | 14,52 | 17,03 | 19,58 | 21,86 | 24,32 |
| SARIMA | 11,55 | 14,10 | 16,60 | 19,12 | 21,38 | 23,91 |
| Prophet-AR | 11,20 | 13,15 | 15,09 | 16,82 | 18,57 | 20,55 |
| XGBoost | 12,08 | 15,71 | 17,71 | 20,60 | 23,71 | 27,27 |
| LightGBM | 11,96 | 15,60 | 18,80 | 21,97 | 24,46 | 28,28 |
| LSTM | 12,56 ± 0,26 | 14,61 ± 0,27 | 17,08 ± 0,32 | 19,66 ± 0,39 | 22,02 ± 0,47 | 24,51 ± 0,51 |
| N-BEATS | 12,62 ± 1,04 | 15,76 ± 1,29 | 18,72 ± 1,52 | 21,50 ± 1,77 | 23,96 ± 1,92 | 26,56 ± 2,01 |
| Persistencia | 11,19 | 13,89 | 16,44 | 19,31 | 21,12 | 23,72 |

R² de la prueba por horizonte.

| Modelo | H1 | H2 | H3 | H4 | H5 | H6 |
|---|---|---|---|---|---|---|
| ARIMA | 0,872 | 0,814 | 0,743 | 0,661 | 0,577 | 0,477 |
| SARIMA | 0,882 | 0,824 | 0,756 | 0,676 | 0,595 | 0,494 |
| Prophet-AR | 0,889 | 0,847 | 0,798 | 0,750 | 0,695 | 0,626 |
| XGBoost | 0,871 | 0,782 | 0,722 | 0,624 | 0,502 | 0,342 |
| LightGBM | 0,873 | 0,785 | 0,687 | 0,573 | 0,470 | 0,292 |
| LSTM | 0,860 ± 0,006 | 0,811 ± 0,007 | 0,742 ± 0,010 | 0,658 ± 0,014 | 0,571 ± 0,018 | 0,468 ± 0,022 |
| N-BEATS | 0,858 ± 0,024 | 0,779 ± 0,037 | 0,688 ± 0,051 | 0,589 ± 0,068 | 0,489 ± 0,082 | 0,373 ± 0,096 |
| Persistencia | 0,889 | 0,829 | 0,761 | 0,670 | 0,605 | 0,502 |

Ganadores de cada familia y criterio que decidió:

- Estadística: Prophet-AR, por RMSE global. Hiperparámetros: {"rezagos": [1, 2, 3, 4, 6, 8], "estacionalidad_anual": 8, "modo_estacionalidad": "additive", "changepoint_prior_scale": 0.002040954252588629, "seasonality_prior_scale": 0.0327103624585865}.
- Aprendizaje automático: XGBoost, por RMSE global. Hiperparámetros: {"rezagos": [1, 2, 4, 8], "transformacion": "ninguna", "learning_rate": 0.010996981647089267, "max_depth": 5, "min_child_weight": 4.312965121208432, "n_estimators": 1213, "subsample": 0.5175676440133128, "colsample_bytree": 0.7753065139358523, "reg_lambda": 0.03128990601615032, "random_state": 42}.
- Aprendizaje profundo: LSTM, por RMSE global. Hiperparámetros: {"ventana_semanas": 18, "unidades": [90, 126], "activacion": "tanh", "dropout": 0.3681465439943041, "optimizador": {"class_name": "adam", "config": {"learning_rate": 0.00036531236053328293}}, "perdida": "mean_absolute_error", "batch_size": 32, "epocas_maximas": 200, "fraccion_validacion": 0.17647058823529413, "paciencia": 20, "paciencia_tasa_aprendizaje": 10, "semilla": 42}.

# 5. Prueba final 2025

Prueba final en 2025: entrenamiento con 2007 a 2024 y un registro por semana de 2025 y horizonte.

Prophet-AR

| Horizonte | RMSE | MAE | MAPE (%) | R² | RMSE persistencia | RMSE / persistencia |
|---|---|---|---|---|---|---|
| H1 | 23,16 | 13,24 | 14,41 | 0,871 | 16,52 | 1,402 |
| H2 | 30,21 | 16,87 | 17,32 | 0,781 | 26,99 | 1,119 |
| H3 | 37,42 | 19,98 | 19,77 | 0,664 | 35,39 | 1,057 |
| H4 | 43,88 | 23,61 | 22,98 | 0,537 | 42,08 | 1,043 |
| H5 | 50,62 | 28,35 | 27,35 | 0,384 | 47,39 | 1,068 |
| H6 | 55,82 | 31,97 | 31,07 | 0,251 | 52,24 | 1,069 |
| Global | 41,74 | 22,34 | 22,15 | 0,581 | 38,73 | 1,078 |

XGBoost

| Horizonte | RMSE | MAE | MAPE (%) | R² | RMSE persistencia | RMSE / persistencia |
|---|---|---|---|---|---|---|
| H1 | 34,77 | 20,27 | 20,40 | 0,710 | 16,52 | 2,105 |
| H2 | 36,41 | 21,62 | 21,56 | 0,681 | 26,99 | 1,349 |
| H3 | 39,44 | 25,27 | 25,85 | 0,626 | 35,39 | 1,114 |
| H4 | 44,12 | 28,93 | 29,80 | 0,532 | 42,08 | 1,048 |
| H5 | 49,83 | 31,94 | 32,06 | 0,403 | 47,39 | 1,051 |
| H6 | 56,80 | 34,85 | 35,36 | 0,225 | 52,24 | 1,087 |
| Global | 44,24 | 27,15 | 27,51 | 0,530 | 38,73 | 1,142 |

LSTM

| Horizonte | RMSE | MAE | MAPE (%) | R² | RMSE persistencia | RMSE / persistencia |
|---|---|---|---|---|---|---|
| H1 | 25,76 ± 1,15 | 14,88 ± 0,61 | 15,96 ± 0,40 | 0,840 ± 0,014 | 16,52 | 1,559 |
| H2 | 32,18 ± 0,92 | 18,24 ± 0,54 | 18,42 ± 0,35 | 0,751 ± 0,014 | 26,99 | 1,192 |
| H3 | 39,75 ± 0,70 | 22,54 ± 0,38 | 21,70 ± 0,23 | 0,620 ± 0,013 | 35,39 | 1,123 |
| H4 | 47,03 ± 0,62 | 25,74 ± 0,43 | 24,23 ± 0,40 | 0,469 ± 0,014 | 42,08 | 1,117 |
| H5 | 53,75 ± 0,61 | 30,11 ± 0,52 | 27,61 ± 0,50 | 0,306 ± 0,016 | 47,39 | 1,134 |
| H6 | 59,53 ± 0,59 | 34,04 ± 0,52 | 30,72 ± 0,55 | 0,149 ± 0,017 | 52,24 | 1,139 |
| Global | 44,58 ± 0,65 | 24,26 ± 0,47 | 23,11 ± 0,39 | 0,522 ± 0,014 | 38,73 | 1,151 |

# 6. Paquetes exportados

Paquetes para subir en Gestión. Las métricas son las del manifest: evaluación en el 15 % final de 2007-2025, la referencia de error que muestra el tablero.

| Modelo | Archivo | Revisión (paquete.revisar_paquete) | Rango del modelo definitivo | Prueba del manifest | RMSE global | MAE global |
|---|---|---|---|---|---|---|
| prophet_ar | outputs/paquetes/prophet_ar.zip | aceptado | 2006-12-31 a 2025-12-28 | 2023-02-26 a 2025-12-28 | 28,32 | 16,11 |
| xgboost | outputs/paquetes/xgboost.zip | aceptado | 2006-12-31 a 2025-12-28 | 2023-02-26 a 2025-12-28 | 33,23 | 19,52 |
| lstm | outputs/paquetes/lstm.zip | aceptado | 2006-12-31 a 2025-12-28 | 2023-02-26 a 2025-12-28 | 31,53 | 18,20 |

# 7. Horizonte recomendado propuesto

Ningún horizonte cumple la regla, ni siquiera el de 1 semana. Regla: mayor h tal que en todos los horizontes de 1 a h los tres ganadores tienen RMSE menor que la persistencia en la prueba y en 2025 y R2 >= 0,5 en la prueba. Valor actual en el tablero (HORIZONTE_RECOMENDADO_SEMANAS): 4. La propuesta no modifica el tablero.

| H | Prophet-AR: supera persistencia (prueba / 2025) | Prophet-AR: R2 prueba | XGBoost: supera persistencia (prueba / 2025) | XGBoost: R2 prueba | LSTM: supera persistencia (prueba / 2025) | LSTM: R2 prueba | cumple |
|---|---|---|---|---|---|---|---|
| 1 | no / no | 0,889 | no / no | 0,871 | no / no | 0,860 | no |
| 2 | sí / no | 0,847 | no / no | 0,782 | no / no | 0,811 | no |
| 3 | sí / no | 0,798 | no / no | 0,722 | no / no | 0,742 | no |
| 4 | sí / no | 0,750 | no / no | 0,624 | no / no | 0,658 | no |
| 5 | sí / no | 0,695 | no / no | 0,502 | no / no | 0,571 | no |
| 6 | sí / no | 0,626 | no / no | 0,342 | no / no | 0,468 | no |
