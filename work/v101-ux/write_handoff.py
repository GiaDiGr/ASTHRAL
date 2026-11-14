from pathlib import Path
from datetime import datetime,timedelta,timezone

import json
R=Path(__file__).resolve().parents[2];D=R/'docs/v101-ux';report=json.loads((R/'engine/data/mission-v101-astronaut/mission-report.json').read_text(encoding='utf8'))
byid={x['id']:x for x in report['outputs']}
def date(sid,day):return datetime.fromisoformat(byid['mission-crew-'+sid+'-cycle-'+day]['as_of']).astimezone(timezone(timedelta(hours=-5))).isoformat()
a=byid['mission-crew-A-cycle-35'];numbers=[]
for d in a['domains']:
 for i in d['indicators']:
  if i['baseline_comparison']:numbers.append(f"- {i['variable']}: {i['value']} {i['unit']}; baseline {i['baseline_comparison']['baseline_value']}; cambio {i['baseline_comparison']['absolute_change']:.3f} {i['unit']}.")
(D/'DEMO_5_MIN.md').write_text('''# Guion reproducible · aproximadamente cinco minutos

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

'''+f"- A 35: `frame-mission-crew-A-cycle-35` · {date('A','35')}.\n- A 21: `frame-mission-crew-A-cycle-21` · {date('A','21')}.\n- B 18: `frame-mission-crew-B-cycle-18` · {date('B','18')}.\n- B 18.1: `frame-mission-crew-B-cycle-18p1` · {date('B','18p1')}.\n- B 47 opcional: `frame-mission-crew-B-cycle-47` · {date('B','47')}.\n\nValores reales de la corrida A 35 (sin ajustes para exposición):\n\n"+'\n'.join(numbers)+'''

Si el selector conserva una evaluación anterior, la UI indica fecha distinta. Usar el botón Ver DKA de este ciclo o Ir al ciclo de origen; no presentar juntos resultados de fechas distintas como simultáneos. Para revisar esa protección deliberadamente: B 47 → seleccionar DKA B 18 → observar advertencia → Ir al ciclo origen.

No afirmar: validación clínica/operacional/de vuelo, diagnóstico firmado, tratamiento ejecutado, recursos NASA, eficacia, capacidad real de sensores a bordo o prevención individual autorizada. El guion está preparado, no se declara ensayado visualmente por la herramienta: la inspección real quedó pendiente. Tiempo aproximado, dependiente de navegación humana.
''',encoding='utf8')
(D/'OPTIONAL_INTERNET_RAG_CONTRACT.md').write_text('''# Contrato para la extensión opcional de Internet del equipo

Estado: PROPUESTA DE INTEGRACIÓN DOCUMENTADA, NO IMPLEMENTADA. No nuevos endpoints, proveedor, credenciales, permiso de red ni cambio de Ollama en este trabajo. El otro integrante debe implementarla como extensión separada y verificable del contrato RAG ya existente. No reemplazar ni bifurcar el motor clínico.

## Invariantes obligatorios

1. Recuperación local y documentación fijada por versión/hash son la base. El motor determinista y sus replays no dependen de Internet, el LLM, un buscador, DNS o credenciales externas.
2. La red es opcional y sólo permitida en FULL con habilitación/política explícita de operador. LOW_POWER/CRITICAL no solicitan Internet; fallo de red vuelve a recuperación local con estado claro. No activar Internet por defecto, no cambiar el modo global desde una respuesta del LLM, no bloquear el motor por un timeout de búsqueda.
3. La extensión sólo tiene capacidades de lectura. Sin token operator/researcher/clinician, endpoint de escritura, edición de reglas, protocolo, inventario, observaciones, historia, autorización o administración. Roles informáticos no equivalen a autoridad médica. No genera nuevos estados clínicos ni reevalúa por contenido web.
4. No transmitir medidas, notas, perfiles, IDs, fechas/ubicación de misión, síntomas individuales, archivos, transcripciones/audio, tokens/cookies, fragmentos de contexto de astronauta o consultas libres del usuario a terceros. Ni siquiera en URLs, telemetría, trazas, embeddings, nombres de archivo o cabeceras. La consulta externa debe construirse exclusivamente de términos públicos previamente aprobados y referencias bibliográficas, independientemente de datos clínicos. Si no puede demostrarse esa independencia, no hay consulta externa.
5. Separar documento externo no revisado de evidencia local aprobada. Descarga/búsqueda/cita no equivale a aprobación clínica. Ninguna página, prompt injection o instrucción incrustada puede añadir herramientas, cambiar política o solicitar datos locales. No cargar enlaces arbitrarios propuestos por contenido remoto; aplicar allowlist y restricciones SSRF/redirecciones, sin acceso a localhost/servicios internos/archivos.
6. Documentación remota no modifica automáticamente clinical_knowledge ni sus versiones. Una nueva fuente requiere revisión humana, procedencia, licencia, localizador, fecha/versión, hash y proceso explícito de aprobación fuera del asistente; su eventual incorporación al motor requiere revisión clínica y nueva versión/pruebas.

## Envoltorios mínimos de intercambio propuestos (aún sin API)

Consulta pública: query_id aleatorio independiente del astronauta, approved_public_terms, source_allowlist y language. No raw_user_question, patient_context, evaluation_id ni mission_id. Política de modo, habilitación y presupuesto/timeout se resuelven del lado servidor; no confiar en una bandera enviada por el cliente.

Respuesta documental: retrieval_status (LOCAL_ONLY/REMOTE_OPTIONAL/UNAVAILABLE), origin (LOCAL_PINNED/REMOTE_UNREVIEWED), retrieved_at timezone-aware, public_url/source_author/title/version/date, locator, content_sha256, extraction_method, excerpt, review_status=UNREVIEWED para remoto, cache_policy y limitaciones. No incluir campo de diagnóstico, recomendación ejecutable o autorización. Este envoltorio no sustituye el contrato de citas/validación de respuestas del asistente; debe mapearse explícitamente y someterse a sus guardas existentes.

## Presentación, cache y auditoría

Mostrar “Fuente externa no revisada”, fecha/versión y separación de resultados deterministas. No sugerir mayor autoridad por ser reciente ni ocultar discrepancias con fuentes fijadas. En offline indicar resultado local y antigüedad conocida; ausencia de red no es ausencia de evidencia. Cache local acotada de material público autorizado, separada de datos clínicos y corpus aprobado, sin autoaprendizaje. Auditoría local de modo/política/estado/URL pública/hash/timeout, sin contenido clínico o secretos. Sin telemetría remota por defecto. Replays del motor siguen usando fuentes fijadas y snapshots, nunca una nueva búsqueda para reconstruir el pasado.

## Pruebas exigidas antes de integrar

- Desconexión/DNS/timeout/proveedor indisponible: evaluación y replays idénticos, retorno local claro.
- FULL deshabilitado y LOW_POWER/CRITICAL: cero solicitudes externas comprobadas por transporte instrumentado.
- Plantar datos clínicos/secrets en pregunta/contexto: ninguno aparece en tráfico, URLs, logs o cache remota.
- Prompts maliciosos, redirecciones, localhost/SSRF, documentos contradictorios: no habilitan herramientas ni aprobación.
- reader no escribe ni obtiene privilegios aunque el modelo lo solicite.
- Ninguna respuesta documental cambia diagnóstico, urgencia, missing_required, seguridad por potasio, inventario o autoridad.
- Contrato/UI distingue LOCAL_PINNED de REMOTE_UNREVIEWED y muestra condiciones/limitaciones.

Hasta superar esa revisión no anunciar Internet integrado ni evidencia web validada. SQLite sin cifrado, aislamiento de procesos y revisión clínica siguen siendo limitaciones independientes.
''',encoding='utf8')
(R/'VIGILE_v101_ASTRONAUT_START_HERE.md').write_text('''# VIGILE v1.0.1 — cierre de experiencia del astronauta

- Ejecución y alcance: [docs/v101-ux/README.md](docs/v101-ux/README.md).
- Guion de cinco minutos: [DEMO_5_MIN.md](docs/v101-ux/DEMO_5_MIN.md).
- Flujo y cambios acotados: [FLOW_AND_CHANGES.md](docs/v101-ux/FLOW_AND_CHANGES.md).
- Inspección visual real pendiente: [MANUAL_VISUAL_QA.md](docs/v101-ux/MANUAL_VISUAL_QA.md).
- Contrato para otro integrante, sin implementación de Internet: [OPTIONAL_INTERNET_RAG_CONTRACT.md](docs/v101-ux/OPTIONAL_INTERNET_RAG_CONTRACT.md).
- Resultados exactos, hashes y recuperación: docs/v101-ux/RESULTS.json y CODE_FREEZE_UX.json.

Portal sintético local: http://127.0.0.1:8912/ mientras su supervisor está activo. No distribuir credenciales ni bases. No cambia criterios/umbrales/dosis ni habilita terapias. R2 y v1.0.1 previos preservados; esta revisión sólo cambia experiencia y herramientas de demostración.
''',encoding='utf8')
print('Wrote 5-minute script, optional Internet contract and entry point')