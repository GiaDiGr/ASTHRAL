# Contrato para la extensión opcional de Internet del equipo

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
