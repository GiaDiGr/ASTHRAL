# B. Space Computing / Optimization v0.9.0

Entrega: 22-10-2026, America/Lima. Medición en computadora de escritorio portátil, sin extrapolar a hardware de vuelo. Configuración original de Ollama, modelo, direcciones loopback y Norton conservados. No se descargaron modelos nuevos.

## Hardware observado

- CPU: Intel Core i9-13900HX, 24 núcleos físicos, 32 procesadores lógicos.
- RAM física informada por Windows: 34,029,125,632 bytes, aproximadamente 31.69 GiB.
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB de VRAM; controlador 617.42 observado. Windows también informa gráficos Intel y un monitor virtual; no se presupone que se utilicen para inferencia.
- Sistema: Windows 11 Home, versión 10.0.26300. Python 3.13.16.
- Runtime: Ollama 0.40.6; modelo local `vigile-qwen3-4b:latest`, Qwen3 4B, Q4_K_M. Digest de manifiesto: `f7b39a48ac98f35a1c5f030ed3543d34e0cbeb5fff525096c3a8ab94e03d4b00`.
- Almacenamiento medido: almacén de modelos 2,497,287,544 bytes; archivo de modelo informado por API 2,497,280,596 bytes; índice 485,696 bytes. La base de referencia v0.8 ocupaba 3,252,224 bytes al medirla. Se conservaron copias y versiones anteriores; no se eliminaron pesos ni historiales para ahorrar espacio.

Datos crudos: `hardware.json`. Las dependencias exactas están en `change-manifest.json`. No se añadió una dependencia para telemetría; se usan API de Windows, nvidia-smi y la API local de Ollama.

## Mejoras implementadas

`space_compute.py` define políticas acotadas, comprobación de RAM disponible, telemetría por proceso, estadísticas con tamaño muestral y una operación explícita de liberación del modelo. La capa conversacional limita una generación concurrente por instancia; el portal limita una conversación a la vez y rechaza saturación con 429. Los fallos y las respuestas no verificables dejan accesibles los resultados deterministas.

La búsqueda cachea exclusivamente el parseo del manifiesto y términos de documentos públicos, con caché de términos limitada a 1024 entradas. Cada consulta vuelve a leer y verificar bytes del índice y las fuentes. No cachea resultados de astronautas ni respuestas entre sujetos. También evita resolver la misma ruta cientos de veces en una búsqueda. Un índice alterado no se oculta tras la caché.

La admisión de inferencia comprueba memoria disponible y la omite por debajo del umbral técnico de 512 MiB. Es una protección inicial de escritorio, no una garantía de memoria suficiente para el modelo ni una política validada de hardware espacial. La presión se probó mediante un valor simulado, sin agotar RAM real. Un `MemoryError` de recuperación documental o explicación produce degradación explícita. CRITICAL conserva motor y recuperación esencial.

## Políticas comparadas

| Modo | Contexto de Ollama | Hilos solicitados | Límite de salida | Fragmentos documentales longitudinales | Permanencia solicitada |
|---|---:|---:|---:|---:|---|
| FULL | 6144 tokens | 8 | 700 tokens | 3 | 5 min |
| LOW_POWER | 2048 tokens | 4 | 300 tokens | 1 | 30 s |
| CRITICAL | Sin llamada | 0 | 0 | 1 | No modifica memoria ya cargada |

Se conserva la política anterior de cantidad de bloques y texto acotado; no se modifica ningún criterio médico. Los hilos son parámetros solicitados al runtime, no medición de CPU realmente utilizada. El contexto efectivo se verificó en `/api/ps`.

Se compararon: configuración v0.8 preservada en ZIP, FULL v0.9, LOW_POWER y CRITICAL; dos solicitudes nativas concurrentes; una prueba limitada de colocación CPU con `num_gpu:0`. No hay otra cuantización local comparable registrada; se mantuvo Q4_K_M. No se modificó el paralelismo global del daemon ni variables de GPU del sistema. Las opciones se solicitan por petición. La prueba CPU de ocho tokens es una comprobación de colocación, no una evaluación equivalente de calidad o rendimiento clínico.

## Latencias reales

Datos crudos y respuestas completas: `compute-benchmark.json`, `endtoend-benchmark.json`, `measurement-benchmark.json`, `rag-benchmark-before.json`.

| Medición | Referencia | v0.9 FULL | LOW_POWER | CRITICAL |
|---|---:|---:|---:|---:|
| Recuperación top-5, mediana de 48 consultas | 287.86 ms | 28.96 ms | Mismo algoritmo; límite menor | Mismo algoritmo; extracto esencial |
| Explicación aislada, modelo cargado, mediana de 5 peticiones | 1.708 s | 1.715 s | 1.692 s | No inferencia |
| Primera explicación tras descarga del modelo, n=1 | 5.66 s | 5.78 s | 5.85 s | No carga |
| Respuesta longitudinal directa con reader/RAG, mediana de 5, pregunta fija | No comparable | — | — | 0.230 s |
| Portal completo, mediana de 5 tras primera petición | Sin referencia equivalente | 2.299 s | 2.207 s | 0.322 s |

La recuperación conservó exactamente los primeros cinco IDs en las 48 consultas comparadas. La reducción observada es de aproximadamente 9.94 veces en la mediana, sin una mejora de cobertura semántica.

La primera llamada tras descargar pesos no equivale a un arranque frío de Windows: la caché de archivos del SO no se limpió. Cada configuración tiene un único caso frío; no se calculan percentiles de esos valores. Las cinco muestras calientes permiten una mediana descriptiva, pero no caracterizan colas de latencia. El código solo calcula p95 cuando n>=20 y usa rango inferior más cercano; esto es una regla conservadora del benchmark, no una garantía estadística universal.

Ingesta sintética en SQLite en memoria: n=57, mediana 0.0762 ms, p95 0.2053 ms; incluye ámbito, dispositivo, control de calidad, persistencia y auditoría. Excluye muestreo físico y transmisión de sensores. También se midieron cinco lotes nuevos de 15 ciclos con evaluaciones y reproducción; ver `performance-summary.json`. No confundir latencia por lote con latencia por medición ni SQLite en memoria con persistencia de vuelo.

## Memoria y utilización

Ollama informó por modelo:

| Configuración | `size_vram`, bytes | Contexto efectivo |
|---|---:|---:|
| v0.8 / FULL v0.9 | 3,571,386,941 | 6144 |
| LOW_POWER | 2,876,160,081 | 2048 |
| Prueba CPU | 0 | 2048 |

La reducción observada de VRAM en LOW_POWER es 695,226,860 bytes, aproximadamente 19.5%. Las diferencias pequeñas de latencia no justifican declarar una aceleración general. Tampoco se ha medido ahorro energético: **consumo de energía NO MEDIDO**.

`resources-profiles.json` conserva nueve muestras por modo durante seis consultas calientes. Incluye daemon, descendientes nativos de Ollama y observador. El proceso de mayor working set observado alcanzó 8,635,297,792 bytes en FULL y 1,010,204,672 en LOW_POWER; sus máximos de memoria privada fueron 12,529,500,160 y 4,206,804,992 bytes. Son observaciones de una sesión por configuración, con historia de asignaciones distinta; no son memoria física única del modelo ni una estimación repetida de ahorro de RAM. No se deben sumar working sets como si no compartieran páginas.

En esas muestras se observaron máximos de CPU normalizada a los 32 procesadores de aproximadamente 3.28% y 3.38%, y utilización global de GPU de hasta 94% en ambos modos. La GPU global incluye Windows y otras aplicaciones. Los valores por proceso y tiempos de CPU crudos permiten revisar el cálculo. No se demuestra reducción de CPU o potencia con esta carga, aunque sí menor memoria de modelo.

El observador preliminar `resources-low-audit.json` solo seleccionaba nombres de ejecutable y podía omitir el runner nativo. Se conserva como referencia incompleta; la selección se corrigió para incluir descendientes y se repitió el perfil. El benchmark general también advierte sobre PIDs creados después de iniciar el muestreo. `resources-profiles.json` utiliza runners ya cargados y estables para la comparación por proceso.

## Liberación y fallos

CRITICAL no invoca Ollama y no descarga implícitamente un modelo anterior. El benchmark confirmó que un modelo de LOW_POWER seguía presente en `/api/ps` durante CRITICAL. La operación explícita `python -m vigile.space_compute release` solicita `keep_alive:0` y comprueba que el modelo desaparezca de `/api/ps`; no detiene el daemon ni garantiza que Windows haya liberado todas sus cachés o que la VRAM global sea cero.

Se probaron:

- FULL → LOW_POWER → CRITICAL → FULL por portal, con mismo estado clínico y registros persistidos invariantes.
- Saturación: solicitudes simultáneas, respuesta 429 a las excedentes, backend clínico accesible durante la inferencia.
- Dos solicitudes nativas reales concurrentes al runtime, con datos y tiempos crudos; no se concluye escalabilidad a muchos usuarios.
- Fuente ausente/manipulada, MemoryError simulado, presión de RAM simulada, fallos de comunicación y modelo no disponible: mantienen fallback o error explícito, sin transformar ausencias en normalidad.
- Pérdida física y reinicio del daemon seleccionado, con descarga previa del modelo y verificación de PID/ruta. El backend permanece disponible; FULL y CRITICAL entregan resultados sin inferencia durante la pérdida. El servicio se reinicia con el mismo ejecutable/configuración y se restaura FULL. Datos exactos en `runtime-failure-recovery.json`.
- Reinicio de backend y portal con una base nueva; las sesiones del portal necesitan autenticación de nuevo y las historias anteriores permanecen en sus directorios.
- Soak corto: 119/119 respuestas de salud HTTP 200 durante 120.68 s. No demuestra estabilidad prolongada ni de una misión; debe ampliarse a horas/días bajo un protocolo independiente.

La computadora no fue un laboratorio aislado: observadores y otras consultas/pruebas coexistieron en partes del desarrollo. Conservar tiempos crudos y repetir bajo carga controlada antes de escoger una configuración definitiva. No se provocó agotamiento real de RAM, fallo del SO ni corrupción de archivos.

## Resultados y límites de integración

Suite final: 545 aprobadas, cero fallos/errores/omitidas, una advertencia de deprecación Starlette/httpx. Se verificaron 15/15 reproducciones de ciclos y 20/20 evaluaciones por HTTP, mismos vectores clínicos que v0.8, reader sin escritura y auditoría válida. Los 105 archivos científicos y ocho JSON clínicos originales siguen intactos. La base activa nueva es `engine/data/portal-v090-release`; las anteriores y el código previo se conservan.

El núcleo se integra experimentalmente con el equipo, sujeto a las limitaciones de RAG/LLM del informe A y revisión humana pendiente. SQLite sigue sin cifrado; la cadena de auditoría local es vulnerable a quien controle almacenamiento y código. Se requiere aislamiento de procesos, gestión de secretos y anclaje externo para un despliegue más fuerte. No se ha validado este diseño en hardware espacial, con sensores reales ni bajo condiciones operativas.

Referencias de API consultadas para las opciones del runtime: [API oficial de Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md) y [configuración oficial](https://github.com/ollama/ollama/blob/main/docs/faq.mdx). La compatibilidad efectiva se comprobó en el runtime local 0.40.6; no se presupone que coincida con toda versión futura de esas páginas.

## Soak adicional completado

Se completaron 300.37 segundos de carga periódica: 256/256 peticiones de salud HTTP 200 y 13/13 peticiones al asistente HTTP 200; registros clínicos invariantes. Ver `stability-300s.json`. La carga fue intermitente, con una consulta al asistente aproximadamente cada 20 segundos, y coexistieron probes documentales. No es inferencia continua ni prueba de horas/días.

La pérdida física de Ollama y recuperación se verificaron: backend disponible y reinicio del runtime en 8.90 s (n=1, cachés del SO no limpiadas). Se restauró FULL y contexto efectivo 6144 al cerrar; ver `final-state.json`.
