# Demostración reproducible v0.10.0

Arrancar servicios según README. Datos exclusivamente sintéticos. Un resultado esperado es una expectativa de software, no de diagnóstico clínico.

## Recorrido visual

1. **Estado general**: Tripulación clínica sintética / Misión terrestre sintética. DKA inicial: urgencia del motor Emergencia, datos sintéticos y ejecución bloqueada. Ausencia de ciclos no oculta la evaluación clínica.
2. **Evaluación clínica**: diabetes conocida, glucosa 180 mg/dL, beta-hidroxibutirato 4,2 mmol/L, pH 7,22. Árbol y alternativas visibles. Bicarbonato y cetonas urinarias ausentes no son requisitos para resolver este árbol; potasio sigue pendiente para seguridad. Recursos y autorización bloquean el protocolo; no hay tratamiento iniciado. Ver fuente y requisitos del protocolo en detalles.
3. **Monitorización**: Astronauta A / Misión A, ciclo A-cycle-14. VO₂ 39 mL/min/kg, baseline 50 y cambio descriptivo -11; puntos previos 48 y 44. No equivale a deterioro clínico validado. Seleccionar Capacidad aeróbica en el gráfico y abrir su tabla, baseline y vigilancia espacial si se desea.
4. Cambiar A-cycle-16: la muestra inválida no se sustituye por normalidad ni por el valor válido anterior. Volver a A-cycle-14 recupera su snapshot, no la muestra posterior.
5. **Seguimiento**: abrir el ciclo del 15/9/2026 y Reproducir ciclo. Abrir Resultado verificable: matches=true, FULL_FROZEN_CYCLE_REEXECUTION, clinical_validation=false. Referencias, hashes y árboles completos siguen desplegables.
6. Cambiar a Astronauta B / Misión B: aparecen episodios y planes humanos propios, fechas de revisión, estados y datos de origen; no recuperación automática. El replay A anterior debe desaparecer. Las reevaluaciones mantienen sus enlaces parent_id.
7. **Asistente**: para vigilancia, seleccionar un ciclo en Monitorización y luego Ciclo de vigilancia seleccionado en el asistente. El texto de contexto debe coincidir con ese selector; para clínica elegir Evaluación clínica seleccionada. Cambiar de contexto borra conversación y descarta respuestas pendientes.
8. Seleccionar LOW_POWER y consultar `How are baselines selected and validated?`. La prueba real aceptó una explicación y recuperó un extracto cuya pertinencia no está adjudicada. Mostrar por separado resultados ENGINE, explicación y documentación. Abrir Extractos recuperados y Ver fuente exacta: fuente, hash, offsets, autoridad y versión. Una coincidencia lexical puede ser ajena a la pregunta; no usarla como evidencia definitiva.
9. Seleccionar CRITICAL y consultar: sin solicitudes al modelo; la memoria puede continuar cargada. GET /api/runtime es observación explícita sin inferencia. Volver a FULL cambia el presupuesto para próximas inferencias, no garantiza una recarga instantánea del modelo.
10. Para DKA, Datos pendientes devuelve clasificación determinista: alternativas no medidas y potasio de seguridad se mantienen separados. Ningún modo del asistente modifica esos estados.

Se verificó anchura de escritorio 1280 y pantalla estrecha 390, además de una comprobación a 319 CSS px durante la sesión anterior. La tabla de criterios dejó de desbordar la página; el menú estrecho se desplaza dentro de su propia barra. Se conservaron capturas y resultados de DOM, no solo una maqueta.

## Comandos de la demostración técnica

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' '..\docs\v010\client_example.py'
& '.\.venv\Scripts\python.exe' '..\docs\v010\live_assistant_demo.py' --mode LOW_POWER
& '.\.venv\Scripts\python.exe' '..\docs\v010\live_assistant_demo.py' --mode CRITICAL
& '.\.venv\Scripts\python.exe' '..\docs\v010\verify_release.py'
& '.\.venv\Scripts\python.exe' -m pytest -q
```

No ejecutar el cambio global de modo mientras otra persona consulta o administra el portal. El script restaura FULL al salir y no cambia configuración de Ollama. La explicación puede rechazarse o caer a extractiva: no forzar generación ni relajar verificaciones para reproducir una captura. Guardar respuesta real y examinar inference_trace; intento HTTP, inferencia completada y explicación aceptada no son equivalentes.

## Interrupciones y recuperación ya comprobadas

- Interrupción real de Ollama después de verificar proceso y ausencia de conexiones activas: lectura clínica 200 y EXTRACTIVE_ONLY. Runtime UNAVAILABLE; ningún cambio en estados del motor. Se reinició el ejecutable portable existente, sin Norton ni cambios globales.
- Interrupción real del backend y reinicio: acceso nuevo rechazado 502; no credencial ni traceback en respuesta. Reinicio del portal invalida sesiones en memoria, seguido de acceso normal con el código existente.
- SQLite 503 y biblioteca alterada 503: fallos controlados mediante tests; no se corrompió ni eliminó una base activa para obtenerlos.
- Caducidad/renovación: reloj inyectado en las pruebas. Saturación 429: carga real de 601 segundos y regresiones de límites.
- Recuperación de Ollama: respuesta aceptada en LOW_POWER; FULL produjo fallback en la consulta de recuperación registrada. No se oculta el rechazo.

Archivos de interrupción corresponden a la preparación v0.10 inicial; ver `ollama-outage.json`, `backend-outage.json` y `recovery-and-modes.json`. Las verificaciones de la base final están en `release-verification.json`. No son validación clínica, operativa ni espacial.

## Capturas

- [Resumen de escritorio](screenshots/desktop-overview.png)
- [DKA de escritorio](screenshots/desktop-dka.png)
- [Pruebas y protocolo bloqueado](screenshots/desktop-dka-criteria.png)
- [Monitorización de escritorio](screenshots/desktop-monitoring.png)
- [Monitorización estrecha](screenshots/narrow-monitoring.png)
- [DKA estrecha](screenshots/narrow-dka.png)
- [Reproducción estrecha](screenshots/narrow-history-replay.png)
- [Caída de IA y clasificación determinista](screenshots/narrow-assistant-outage.png)
- [Fuente exacta en pantalla estrecha](screenshots/narrow-assistant-sources.png)

Las capturas muestran distintos momentos del recorrido. La de fuente exacta es el detalle técnico abierto deliberadamente; JSON y documentos técnicos están colapsados por defecto en la interfaz final. La captura de caída procede de la prueba controlada de servicios, conservada como evidencia histórica.

Capturas adicionales de cierre: [episodios y planes](screenshots/narrow-episodes.png), [tabla sincronizada con el gráfico](screenshots/narrow-chart-table.png), [respuesta final de suficiencia DKA](screenshots/narrow-dka-assistant.png). Verificar al cambiar de VO2 a frecuencia cardíaca que la tabla abierta cambia de mL/min/kg a bpm. El primer intento de inspección de la tabla cerrada no mostraba sus unidades en innerText; tras abrir el desplegable se confirmaron los valores correctos.
