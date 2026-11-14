# A. Auditoría computacional v0.9.0

Mediciones iniciales: 23 de octubre de 2026 (America/Lima). Cierre documental: 24 de octubre de 2026. Prototipo de investigación, exclusivamente sintético.

## Alcance y separación del desarrollo

Comprobación con un protocolo nuevo sobre los servicios y la base v0.9, antes de desplegar los cambios Python v0.10. No es una revisión clínica independiente ni una certificación por un auditor externo. Se conserva el benchmark anterior y sus mediciones. No se repitió la auditoría clínica ni el banco LLM/RAG; las 12 preguntas reservadas permanecen sin ejecutar, comprobadas solamente por hash.

Código original: `before-v010.zip`; código de recolección v0.9 anterior a la corrección: `benchmark_compute-v09-original.py`. Informe crudo: `compute-audit/audit.json`. Corrección de atribución de procesos: `audit_resources_corrected.py`, `compute-audit/corrected-resources.json` y `resource-summary.json`.

## Equipo y configuración

Intel Core i9-13900HX, 24 núcleos / 32 procesadores lógicos; RAM instalada 34 029 125 632 bytes. Windows 11 Home, compilación 26300. NVIDIA RTX 4060 Laptop, 8188 MiB, controlador 617.42. Ollama portable 0.40.6 en 127.0.0.1:8891; modelo `vigile-qwen3-4b:latest`, Q4_K_M, digest `f7b39a48ac98f35a1c5f030ed3543d34e0cbeb5fff525096c3a8ab94e03d4b00`.

FULL: contexto 6144, 8 hilos, salida máxima 700. LOW_POWER: contexto 2048, 4 hilos, salida máxima 300. CRITICAL: ninguna solicitud de inferencia. No se cambiaron esos presupuestos ni criterios biomédicos.

## Método

Tres sesiones independientes de descarga/carga del modelo, 1 consulta de carga y 20 repeticiones calientes por modo y sesión; secuencia FULL → LOW_POWER → CRITICAL → FULL. Pregunta fija nueva sobre baselines, 5 bloques sintéticos del ciclo A-cycle-14, sin casos reservados. Las cargas son frías para el proceso del modelo, no para la caché del sistema operativo.

FULL y LOW_POWER miden la misma generación directa sobre los mismos bloques. CRITICAL mide el recorrido reader + recuperación + respuesta extractiva: su latencia no es una comparación del mismo trabajo de inferencia. Las respuestas y sus rechazos se conservan; una respuesta técnicamente aceptada no ha sido adjudicada clínicamente.

60 recuperaciones documentales con tres consultas fijas nuevas; 601,073 segundos de carga sostenida, salud cada aproximadamente 0,5 s y lotes de 3 consultas concurrentes aproximadamente cada 5 s. Saturación controlada por el bloqueo existente del asistente. La suite original y preparación de archivos coexistieron durante parte de la prueba sostenida: este escritorio no es un banco físicamente aislado.

Diez lotes adicionales de adquisición, 15 ciclos, reglas, persistencia y reproducción en SQLite en memoria. La duración incluye todo ese lote; no es la latencia de un criterio individual. Lectura clínica HTTP y reproducción medidas por separado. Telemetría nativa de memoria/proceso y `nvidia-smi`; GPU global incluye otros procesos y pantalla.

## Latencias observadas

20 repeticiones por fila; segundos. p95 según rango inferior utilizado por el recolector, no intervalo de confianza.

| Sesión | Modo | Mediana s | p95 s | VRAM asignada al modelo GiB |
|---|---|---:|---:|---:|
| 1 | FULL | 2.821 | 2.918 | 3.326 |
| 1 | LOW_POWER | 2.833 | 2.898 | 2.679 |
| 1 | CRITICAL | 0.573 | 0.630 | 2.679 |
| 2 | FULL | 2.856 | 3.022 | 3.326 |
| 2 | LOW_POWER | 2.312 | 2.368 | 2.679 |
| 2 | CRITICAL | 0.382 | 0.433 | 2.679 |
| 3 | FULL | 2.207 | 2.390 | 3.326 |
| 3 | LOW_POWER | 2.151 | 2.299 | 2.679 |
| 3 | CRITICAL | 0.395 | 0.464 | 2.679 |

La menor VRAM asignada en LOW_POWER se repitió en las tres sesiones: 3 571 386 941 → 2 876 160 081 bytes, aproximadamente 19,5 %. **No equivale a energía ni potencia ahorrada.** La latencia varió entre sesiones; LOW_POWER no fue más rápido en todos los ensayos.

Recuperación documental: mediana 0.121 s (60 muestras). Lectura clínica HTTP: mediana 0,0266 s (20 lecturas). Lote sintético completo: mediana 3.176 s (10 lotes; todos sus replays coincidentes). Datos por observación en `clinical-and-storage.json` y `post-load-checks.json`.

## Defecto descubierto: reutilización de PID

El recolector anterior recorría ParentProcessId sin verificar CreationDate. Windows reutilizó el PID 1776 para conhost de Ollama; procesos antiguos del sistema conservaban ese número como padre. En la segunda expansión el recolector incluyó procesos ajenos. **Las sumas de RAM/CPU de ese conjunto original no son atribuibles a VIGILE y quedan invalidadas.** Las latencias, GPU global y `/api/ps` no dependen de esa atribución.

Se conservó el archivo anterior y se corrigió el recolector de `docs/v09/benchmark_compute.py`: un hijo solo se incorpora si existe su padre seleccionado y su creación no es anterior a la del padre. Se repitieron tres sesiones por modo, 5 generaciones por sesión, con muestreo durante inferencia. Ahora se obtienen 4 procesos de Ollama y 1 del recolector, en vez de cientos. El recolector se excluye de los agregados siguientes.

| Sesión | Modo | Pico working set GiB | Pico private bytes GiB | CPU s / intervalo s | GPU global % mín./máx. |
|---|---|---:|---:|---|---|
| 1 | FULL | 1.050 | 4.684 | 11.266 / 12.199 | [0, 89] |
| 1 | LOW_POWER | 1.037 | 4.001 | 11.891 / 12.857 | [0, 85] |
| 2 | FULL | 1.068 | 4.685 | 12.109 / 13.174 | [0, 86] |
| 2 | LOW_POWER | 1.038 | 4.002 | 12.219 / 13.727 | [0, 89] |
| 3 | FULL | 1.067 | 4.685 | 12.688 / 14.089 | [0, 87] |
| 3 | LOW_POWER | 1.038 | 3.999 | 12.953 / 14.381 | [0, 83] |

Working set es residencia por proceso; private bytes es memoria privada comprometida, no RAM física residente. Su suma no deduplica páginas compartidas. CPU es tiempo acumulado durante el intervalo, no porcentaje de toda la máquina. GPU global: 3519 MiB en FULL y 2851 MiB en LOW_POWER en estas muestras; no atribuir todo ese valor a VIGILE. Disponibilidad mínima de RAM en los ensayos corregidos: aproximadamente 10,1 GiB. No se provocó presión extrema de memoria en el equipo.

## Estabilidad, transiciones y recuperación

- 740 consultas de salud HTTP 200; 225 solicitudes de asistente: 75 HTTP 200 y 150 HTTP 429 de saturación esperada. No se observaron fallos de transporte, aplicación o base de datos en esa carga. Un 200 del asistente puede contener fallback, no necesariamente generación aceptada.
- Registros exactos sin cambios después de cada modo y al finalizar; cadena de auditoría válida.
- Después de la carga: 39 replays coincidentes, 24 clínicos y 15 de monitorización; escritura reader y acceso fuera de alcance rechazados con 403. `final-post-soak-replays.json`.
- CRITICAL: contador de solicitudes del modelo igual a cero en 60 consultas. El modelo permaneció cargado después de LOW_POWER. Se corrigió la presentación del portal para diferenciar instalado, cargado, no observado e indisponible. CRITICAL no es una orden de descarga.
- Caída real controlada de Ollama: backend clínico HTTP 200, respuesta extractiva sin generación. Caída del backend: acceso nuevo al portal rechazado con 502, sin secretos. Recuperación y cambios de modo conservados en `ollama-outage.json`, `backend-outage.json`, `recovery-and-modes.json`.
- Tras recuperar Ollama, la consulta de demostración obtuvo generación aceptada en LOW_POWER y fallback por rechazo/fallo en FULL. No se ocultaron esos fallos ni se relajaron validadores para obtener más respuestas.
- `inference_executed` histórico no es un contador de ejecución: algunas rutas lo dejan falso cuando se rechaza una salida después de solicitarla. La API del portal añade `inference_trace.model_requests_attempted` y `explanation_accepted`; una solicitud intentada tampoco prueba que la inferencia haya terminado.

## Almacenamiento y límites

Tamaños lógicos iniciales: demostración aproximadamente 4,16 MB; almacén del modelo 2 497 287 544 bytes; runtime portable 1 942 921 587 bytes. No incluyen todas las bases históricas, copias ni asignación física del disco.

`energy = NOT_MEASURED`. No se instrumentó potencia válida. No se demuestra ausencia de fugas durante horas, comportamiento de hardware espacial, consumo de vuelo, latencia bajo presión extrema, resiliencia a radiación ni corrección clínica del lenguaje generado.

**Conclusión:** apto para integración experimental de software dentro de los límites medidos. El rechazo explícito y los resultados deterministas se conservan al reducir recursos. Quedan pruebas prolongadas, aislamiento de procesos y validación humana; no existe certificación clínica, operativa o espacial.

## Desglose de respuestas y fallos conservados

| Recorrido | Resultado real |
|---|---|
| FULL directo, 60 repeticiones calientes | 60 sin excepción del recorrido medido |
| LOW_POWER directo, 60 repeticiones calientes | 60 sin excepción del recorrido medido |
| CRITICAL extractivo, 60 repeticiones | 60 sin excepción, 0 solicitudes al modelo |
| Carga sostenida, HTTP 200 | **75 EXTRACTIVE_FALLBACK; 0 explicaciones generadas aceptadas** |
| Carga sostenida, HTTP 429 | 150 ASSISTANT_BUSY |

La generación directa sobre cinco bloques y el asistente completo son trabajos distintos. El éxito del primero no demuestra calidad del segundo. La carga sostenida demuestra admisión, salud y preservación de datos; **no demuestra disponibilidad de explicaciones generadas aceptadas bajo esa carga**. No se puede atribuir causalmente el fallback a LOW_POWER, saturación o una regla de soporte solo con este ensayo. Los fallos internos no se publican como secretos en la API. Las mediciones originales conservan respuestas completas; la traza aditiva v0.10 distingue intentos de aceptación.

La demostración final separada sobre la base integrada obtuvo ANSWERED en LOW_POWER, con 2 solicitudes intentadas (generación/verificación), y EXTRACTIVE_ONLY en CRITICAL, con 0 solicitudes. Datos reales de esas consultas sintéticas: `live-assistant-demo-LOW_POWER.json` y `live-assistant-demo-CRITICAL.json`. No sustituyen la revisión humana del contenido ni cambian el resultado de la prueba sostenida.
