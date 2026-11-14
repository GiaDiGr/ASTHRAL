# B. VIGILE v0.11.0 — Integrated Mission

Demostración sintética de software, sin validación clínica, operativa o espacial. Se conservan las siete rutas, sus umbrales y la prohibición terapéutica. No se reconstruye el proyecto. Ollama sigue en 127.0.0.1:8891 con vigile-qwen3-4b:latest.

## Arquitectura y secuencia

mission_demo orquesta la API existente: adquisición operator → validación → baselines → MonitoringService → ClinicalService → eventos/hallazgos → episodios/planes → reader/BFF/asistente. mission_context añade fases sintéticas append-only; mission_frames congela proyecciones por recepción; mission_review comprueba replays y ocho consultas. El modelo no tiene credenciales de escritura ni autoridad clínica.

La base nueva es engine/data/mission-v011-final. Backend/portal nuevos: 8897/8898. Los anteriores 8895/8896 y portal-v0100-integrated se conservan. Carpetas nuevas: docs/v011, work/v011 y las copias en engine/data/backups/mission-v011-final*.

Tiempo virtual: día 0 = 01/08/2026 12:00 UTC (07:00 PET). Son fechas de simulación con conocimiento actual, no reconstrucción del conocimiento clínico disponible en esas fechas. No se cambia el reloj Windows.

| Días | Escenario |
|---|---|
| −7, −5, −3 | Dos astronautas sintéticos distintos; tres muestras por variable de baseline. |
| −2 | Seis baselines personales: capacidad aeróbica, fuerza y sueño por persona. |
| 0 | PRE_MISSION/EARTH → IN_MISSION/MICROGRAVITY bajo la misma misión. |
| 7, 14 | A desarrolla cambios progresivos; B evoluciona de forma distinta. A tiene sueño no medido el día 14. |
| 18 | B: diabetes conocida, glucosa 180 mg/dL, beta-OHB 4,2 mmol/L, pH venoso 7,22. DKA cumple el árbol existente. Bicarbonato/cetonas urinarias no bloquean. Falta potasio para seguridad y faltan recursos/autorización. |
| 18,1 | Nuevas mediciones y potasio; reevaluación enlazada. DKA sigue cumpliendo criterios. Resolver potasio no autoriza protocolo ni tratamiento. |
| 21 | A: fuerza inválida; sueño de otra fase; frecuencias cardíacas contradictorias; llegada de VO₂ fechado en día 11; SpO₂ antiguo. Ninguna ausencia/invalidez se convierte en normalidad. |
| 28, 35 | Tendencias, comparaciones y eventos normativos/descriptivos con fuentes, sin convertir estadísticas en diagnósticos. |
| 42, 47 | POST_MISSION/EARTH; seguimiento y variaciones numéricas. Sin recuperación clínica ni cierre automáticos. |

Total: 54 días desde la primera muestra; 26 ciclos, 50 evaluaciones clínicas, 6 baselines, 129 mediciones y 17 dispositivos sintéticos. Los dispositivos, TTL, rangos técnicos y muestreo son fixtures de software, no disponibilidad de hardware o umbrales clínicos de vuelo. Unidades originales y conversiones del motor se conservan.

La ruta aguda es DKA. OH/POTS/hipoglucemia se evalúan donde el motor actual determina aplicabilidad o insuficiencia. Un episodio puede representar un hallazgo por datos insuficientes, no una enfermedad. DM, AKI y anafilaxia conservan sus pruebas anteriores; no se inventan episodios nuevos para ellas.

## Historia y reproducción

Cada frame se captura después del ciclo recibido, con fecha, fase, ID y hash. No se reconstruye filtrando timestamps de la base final. La muestra del día 11 recibida en el día 21 no aparece en día 14. Se excluyen adicionalmente muestras fechadas después del instante. Baselines, episodios, planes y evaluaciones quedan congelados juntos. Fechas futuras de un plan ya conocido no son observaciones futuras.

El selector ofrece checkpoints completos; elegir un ciclo con frame cambia todo el contexto. El índice muestra fechas/fases neutrales, no eventos médicos futuros. No hay reconstrucción arbitraria de instantes sin checkpoint ni backfill histórico de bases anteriores.

- Semilla igual reproduce solicitudes y vector semántico clínico/descriptivo. La suite repite toda la misión sin conexiones de aplicación.
- Cada snapshot se reejecuta con la misma implementación y conocimiento: 26 replays de ciclo y 50 clínicos coinciden.
- No se promete identidad binaria de bases. UUID de almacenamiento, credenciales aleatorias y tiempos reales de auditoría difieren. Los hashes completos incluyen referencias de almacenamiento; el hash semántico no los reemplaza.

mission-report.json contiene solicitudes, salidas, frames, hashes y replays. summary.json no contiene credenciales. OpenAPI se genera en esa carpeta. Código de versión anterior conservado para reproducir sus bases.

## Asistente, recursos y fallos

assistant-final-offline.json: ocho consultas con cero solicitudes al modelo. assistant-final-real.json: Ollama real, intentos, causas y aceptación por consulta. RESULTS.json resume las salidas exactas. En la ejecución final las ocho preguntas no tuvieron generación aceptada; tres devolvieron suficiencia, pruebas o documentos deterministas. Una ejecución anterior sí aceptó la reevaluación. No se presenta un fallback como generación.

FULL → LOW_POWER → CRITICAL afecta sólo al asistente; hashes clínicos permanecen iguales. CRITICAL no solicita inferencia. La indisponibilidad se inyecta sólo en el adaptador de demostración: no se detiene Ollama. Al restaurar el adaptador se vuelve a FULL; puede seguir habiendo fallback. No inferir no equivale a liberar RAM/VRAM.

Fallos de desarrollo conservados: ejecución de sandbox interrumpida al crear sólo el corpus; fixture DKA enviaba unidad 1 en vez de pH (se corrigió el simulador, no el criterio); aserción comparaba Z/+00:00 como texto (se comparan datetimes); bloqueo de red antes de inicializar asyncio impedía su self-pipe Windows (se bloquean todas las conexiones durante la misión después de inicializar el harness). Los XML de fallos no cuentan como pruebas aprobadas.

## Resultados, uso y límites

Entrega: 582 pruebas, 164,37 s, una advertencia Starlette/httpx. Comandos: README.md. Contratos: INTEGRATION_CONTRACTS.md. Guion verificado de cinco minutos: DEMO.md. Cifras reales, modos, latencia/CPU/memoria/almacenamiento: RESULTS.json. Capturas: screenshots/.

Pendientes prioritarios: revisión clínica independiente y aplicabilidad espacial; cifrado SQLite/backups y aislamiento; retención de snapshots con conservación de replays; revisión de seguridad/accesibilidad; evaluación independiente de abstención/generación; validación de calibración, método y disponibilidad de cualquier sensor real.

Listo para integración local de investigación y demostración reproducible, con esos límites. Ningún tratamiento habilitado. Las pruebas sintéticas no validan decisiones clínicas ni funcionamiento espacial.
## Medición inicial real

Misión final: 39,07 s en escritorio incluyendo adquisición, snapshots y replays; CPU del proceso durante preparación 32,16 s. Ciclos ASGI+SQLite: media 608,65 ms, máximo 2094,83 ms. Working set observado al final 164155392 bytes; privado 148414464 bytes; base 37879808 bytes. No se midió energía ni se usó GPU en la misión offline. La latencia aumenta al crecer el historial congelado: queda pendiente retención/compactación compatible con replays. No extrapolar a hardware de vuelo ni confundir con latencia de red o LLM.