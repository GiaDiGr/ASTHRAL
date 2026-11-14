# ASTHRAL Computer Vision: pruebas y benchmarks

## Qué miden estos resultados

ASTHRAL separa tres medidas que no son intercambiables:

1. **Pruebas del software:** validan entradas, transformaciones, exportación, límites y errores previsibles.
2. **Rendimiento local:** mide carga e inferencia en esta computadora con patrones sintéticos reproducibles.
3. **Desempeño biomédico:** requiere predicciones y referencias clínicas válidas, una partición independiente por persona, protocolos comparables y revisión de sesgos. Los resultados de las dos primeras categorías no prueban la tercera.

No se aplica una meta artificial de “más de 90% en todo”. Optimizar un número con píxeles sintéticos, umbrales elegidos después de ver los resultados o datos reutilizados puede inflar una cifra sin mejorar la validez. Los informes dejan las métricas indefinidas cuando faltan etiquetas o una clase necesaria.

## Ejecución reproducible

Desde `engine/` en Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest tests/test_computer_vision_metrics.py -q --cov=vigile.computer_vision_metrics --cov-report=term-missing --cov-fail-under=90
.\.venv\Scripts\python.exe -m pytest tests/test_computer_vision.py tests/test_skinguard.py tests/test_computer_vision_metrics.py tests/test_benchmark_computer_vision.py -q --cov=vigile.computer_vision --cov=vigile.skinguard --cov=vigile.computer_vision_metrics --cov-fail-under=90
.\.venv\Scripts\python.exe tools/benchmark_computer_vision.py --warmup 1 --repeats 5 --output ..\artifacts\benchmarks\asthral-cv-benchmark.json
```

El benchmark crea gradientes y patrones geométricos deterministas, no usa fotos, OCT ni ecocardiogramas de personas. Registra versiones, hashes de pesos instalados, tiempo de carga, latencia mediana/media/p95, rendimiento por segundo y formas/salidas de control. Los conteos de clases o la ocupación de una máscara con esos patrones describen únicamente la salida observada en esos patrones; no son exactitud, Dice, IoU ni evidencia clínica. SkinGuard informa `MODEL_NOT_CONFIGURED` si no encuentra pesos compatibles.

### Corrida local del 14 de noviembre de 2026

Se usaron 2 calentamientos y 10 mediciones por modelo, CPU con 4 hilos y entradas sintéticas. El JSON completo con versiones y hashes está en [`artifacts/benchmarks/asthral-cv-benchmark-2026-11-14.json`](../../artifacts/benchmarks/asthral-cv-benchmark-2026-11-14.json).

| Módulo | Carga del modelo | Latencia mediana / p95 | Rendimiento al valor mediano |
|---|---:|---:|---:|
| OcularVision | 0.068 s | 0.839 / 0.855 s por imagen | 1.192 imágenes/s |
| EchoVision | 1.686 s | 0.093 / 0.100 s por fotograma | 10.771 fotogramas/s |
| MotionGuard | 1.001 s | 0.021 / 0.023 s por fotograma | 48.074 fotogramas/s |
| SkinGuard | No se ejecutó | Sin pesos configurados | No disponible |

En el patrón sintético MotionGuard no encontró landmarks; esto solo confirma que procesó el patrón y reportó salida vacía. EchoVision produjo una máscara para ese patrón, y OcularVision emitió etiquetas para el gradiente sintético. Ninguno de estos resultados sirve para comparar exactitud.

La batería dirigida de CV, SkinGuard, métricas y benchmark pasó **130/130 pruebas**. El calculador de métricas pasó **34/34 pruebas** y alcanzó **99% de cobertura de líneas**, medido únicamente sobre `vigile.computer_vision_metrics.py`.

La última suite completa pasó **894 pruebas**, omitió **2** por dependencias/modelos opcionales y no tuvo fallos, en 264.86 s. En la corrida completa, la cobertura fue **92%** para `computer_vision.py`, **100%** para `skinguard.py`, **99%** para `computer_vision_metrics.py` y **95% combinada** entre los tres. Quedó una advertencia de compatibilidad futura en `starlette.testclient` con `httpx`; no afecta el resultado de las pruebas. Cuatro pruebas independientes del sincronizador verifican el avance rápido con respaldo, cambios locales sin commit, eliminaciones remotas y ramas divergentes.

La utilidad `vigile.computer_vision_metrics` permite calcular Dice, IoU, exactitud por píxel, precisión, sensibilidad, especificidad, F1, AUROC, mAP@.50 y mAP@.50:.95. Para usarla en evaluación de un modelo hay que pasar predicciones y referencias de una partición retenida documentada. El cálculo no crea datos de referencia ni valida un modelo. La evaluación de detección implementada es de una sola clase, incluye imágenes negativas en el conjunto y no sustituye una evaluación COCO completa.

## Referencias publicadas: contexto, no resultados de ASTHRAL

| Área | Resultado informado por la fuente | Límite de comparación |
|---|---:|---|
| OCT retinal U-Net | Dice medio 83.28%, IoU medio 72.33%, exactitud por píxel 97.11% | Reporte del repositorio del modelo y su conjunto pequeño; no evaluación independiente ni resultado de ASTHRAL. Etiquetas y partición deben revisarse antes de comparar. |
| Lesiones cutáneas | En el benchmark ISIC/TBP de MICCAI 2026, el mejor resultado citado es mAP@.50 67.4%, precisión 70.7%, sensibilidad 58.3% y F1 64.0% | Es otro benchmark, anotación y modelo. ASTHRAL no tiene un detector SkinGuard compatible instalado; esas cifras no se transfieren. |
| Ecocardiografía | El artículo EchoNet-Dynamic informa Dice de ventrículo izquierdo 0.92, error absoluto medio de FE de 4.1 puntos y AUC 0.97 para las tareas evaluadas por el artículo | Son resultados del estudio EchoNet-Dynamic, con sus datos, protocolo y modelos. El adaptador de ASTHRAL no ha sido evaluado en su partición etiquetada y no calcula FE. |
| Movimiento | MediaPipe Holistic documenta detección de landmarks de pose, rostro y manos | La documentación técnica no ofrece una exactitud clínica de rehabilitación aplicable a ejercicios de ASTHRAL. Los ángulos de ASTHRAL son proyecciones 2D y no mediciones clínicas calibradas. |

Fuentes: [repositorio OCT y métricas del autor](https://github.com/Strange-Philip/oct-retinal-layer-segmentation), [benchmark MICCAI 2026 ISIC](https://papers.miccai.org/miccai-2026-sat/ISIC_016.html), [artículo EchoNet-Dynamic](https://www.nature.com/articles/s41586-020-2145-8), [documentación oficial de MediaPipe Holistic Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/holistic_landmarker).

## Criterio de interpretación

Un 100% en una prueba unitaria significa que el código satisface el caso de control creado para esa prueba. El 99% de cobertura del calculador de métricas significa que las pruebas ejecutaron el 99% de sus líneas de Python. Ninguna de esas cifras mide clasificación de cáncer, detección de anomalías retinianas, segmentación ecocardiográfica válida o eficacia de rehabilitación. Los porcentajes clínicos de ASTHRAL quedan pendientes hasta disponer de conjuntos autorizados, etiquetas y protocolo de evaluación adecuados.
