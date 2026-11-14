# Guion reproducible · aproximadamente cinco minutos

Preparación fuera del tiempo de exposición: servidor iniciado según README, código privado obtenido, abrir http://127.0.0.1:8912/, entrar. Cerrar cualquier captura que muestre credenciales. Son registros ficticios; la fecha del checkpoint no es la salud actual del usuario. No hay que consultar al LLM ni usar voz para realizar este recorrido.

| Tiempo | Acción | Mensaje para el jurado |
|---|---|---|
| 0:00–0:30 | Seleccionar Astronauta sintético A / misión-v011. Elegir checkpoint A ciclo 35; confirmar fase/gravedad/fecha. | “Cada vista pertenece a un astronauta, misión y momento recibido. Trabajamos con datos sintéticos.” |
| 0:30–1:20 | Tu recorrido → 1. Mediciones y tendencias. Elegir capacidad aeróbica. Abrir tabla y baselines. | “Estos puntos son muestras observadas; la comparación procede del baseline realmente usado por el motor. No son predicciones.” |
| 1:20–2:00 | Tu recorrido → 2. Hallazgos; después → 3. Prevención documentada. Abrir Cardiovascular y Musculoesquelético. | “Un incumplimiento normativo no es una enfermedad. La biblioteca describe prevención y limitaciones; no inventa una rutina ni acredita recursos o autorización.” |
| 2:00–2:30 | Cambiar a checkpoint A ciclo 21 y revisar músculo/sueño/frecuencia cardíaca. | “Datos inválidos, incompatibles o contradictorios no se convierten en normales. La comparación y orientación quedan limitadas.” |
| 2:30–3:30 | Seleccionar Astronauta sintético B y checkpoint B ciclo 18. Pulsar Ver DKA de este ciclo; revisar criterios y prioridad. | “La lógica de alternativas ya satisface DKA. Bicarbonato y cetonas urinarias ausentes son alternativas no bloqueantes; potasio falta para seguridad del protocolo.” |
| 3:30–4:10 | Abrir Manejo documentado: insulinoterapia, recursos, restricciones y autoridad. | “La restricción de potasio es específica de insulinoterapia; revisar capacidad IV no ordena fluidos. Recursos declarados no son inventario verificado. Toda ejecución sigue bloqueada.” |
| 4:10–4:40 | Cambiar a B ciclo 18.1; seleccionar DKA del ciclo y después Tu recorrido → 5. Seguimiento. | “La reevaluación añade potasio medido, pero no concede autoridad ni demuestra tratamiento, eficacia o recuperación. Episodios y planes son trazables.” |
| 4:40–5:00 | Mostrar banner/contexto y explicar funcionamiento local. Si se preparó previamente desconexión de Internet, navegar otro checkpoint y volver. | “Motor, resultados y documentación base son locales. Internet no decide criterios. El ensayo offline automático bloqueó conexiones del adaptador y mantuvo resultados; la desconexión física/navegador requiere el checklist humano.” |

## Identificadores exactos y fechas Lima originales

- A 35: `frame-mission-crew-A-cycle-35` · 2026-09-05T07:00:00-05:00.
- A 21: `frame-mission-crew-A-cycle-21` · 2026-08-22T07:00:00-05:00.
- B 18: `frame-mission-crew-B-cycle-18` · 2026-08-19T07:00:00-05:00.
- B 18.1: `frame-mission-crew-B-cycle-18p1` · 2026-08-19T09:24:00-05:00.
- B 47 opcional: `frame-mission-crew-B-cycle-47` · 2026-09-17T07:00:00-05:00.

Valores reales de la corrida A 35 (sin ajustes para exposición):

- physiology.vo2max: 35.315 mL/min/kg; baseline 50.0; cambio -14.685 mL/min/kg.
- physiology.strength: 395.0 N; baseline 500.0; cambio -105.000 N.
- sleep.duration: 6.6 h; baseline 8.0; cambio -1.400 h.

Si el selector conserva una evaluación anterior, la UI indica fecha distinta. Usar el botón Ver DKA de este ciclo o Ir al ciclo de origen; no presentar juntos resultados de fechas distintas como simultáneos. Para revisar esa protección deliberadamente: B 47 → seleccionar DKA B 18 → observar advertencia → Ir al ciclo origen.

No afirmar: validación clínica/operacional/de vuelo, diagnóstico firmado, tratamiento ejecutado, recursos NASA, eficacia, capacidad real de sensores a bordo o prevención individual autorizada. El guion está preparado, no se declara ensayado visualmente por la herramienta: la inspección real quedó pendiente. Tiempo aproximado, dependiente de navegación humana.
