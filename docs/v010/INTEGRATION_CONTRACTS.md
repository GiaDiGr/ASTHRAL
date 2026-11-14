# Contratos de integración v0.10.0

Cambios aditivos; se preservan campos y endpoints anteriores. Contratos biomédicos existentes en los OpenAPI y documentos de v0.6.1–v0.9. No usar una explicación para modificar estados clínicos.

## Frontend / BFF 8896

Todas las llamadas son locales. POST exige `Origin: http://127.0.0.1:8896`; GET cross-site se rechaza. Credencial backend jamás llega al navegador. No guardar el código del portal en localStorage, URL, logs o historial de conversación.

| Método/ruta | Petición | Respuesta y semántica |
|---|---|---|
| POST /api/login | `{code: string}` | cookie HttpOnly, autenticación reader validada, límites idle/absoluto |
| GET /api/session | cookie | idle_seconds_remaining, absolute_seconds_remaining, secure_transport; no renueva inactividad |
| POST /api/session/renew | `{}` | cookie rotada, renewed=true, absolute_lifetime_extended=false |
| POST /api/logout | `{}` | revoca cookie/sesión |
| GET /api/status | cookie | backend, portal, assistant, assistant_busy, runtime, clinical_execution, process_isolation, version |
| GET /api/runtime | cookie | observación explícita `/api/ps`; loaded true/false/null; nunca solicita inferencia |
| POST /api/mode | mode FULL/LOW_POWER/CRITICAL | clinical_rules_changed=false; no implica descarga |
| GET /api/subjects | cookie | perfiles autorizados |
| GET /api/dashboard/{subject}?mission_id={mission} | IDs | proyección scoped existente + episodes y followups |
| GET /api/replay/{clinical,monitoring}/{id} | ID | reproducción scoped de solo lectura; no valida clínicamente |
| GET /api/source/{id} | ID de evidencia clínica | registro bibliográfico |
| GET /api/protocol/{id} | ID | requisitos documentados; no autorización |
| GET /api/document/{fragment_id} | D- + 20 hex | texto exacto, reference, relevance=NOT_INDEPENDENTLY_VALIDATED, authority_is_not_patient_state=true |
| POST /api/assistant | un evaluation_id o monitoring_id; question; history opcional; history_context_id; documentary=false opcional | answer/retrieved/documents/generated/status/message existentes; inference_trace aditivo |

El dashboard conserva profile, mission, measurements (últimas 1000), baselines, trends, findings (100), monitoring (50), evaluations (100), limits y clinical_execution. episodes/followups pertenecen al scope autorizado. Un límite de proyección puede ocultar muestras antiguas: no interpretarlo como ausencia clínica. No hay endpoint de escritura de episodios o reglas en el BFF.

`runtime.loaded=null` significa no observado o no disponible. CRITICAL no observa automáticamente memoria; GET /api/runtime permite observarla explícitamente sin inferir. `assistant.available` describe disponibilidad/configuración, no residencia en GPU. Presentar fecha de observación y no inventar memoria liberada.

`inference_trace.model_requests_attempted`: entero si el adaptador instrumenta solicitudes, null si no; cuenta intentos HTTP al modelo durante esa consulta, incluso salidas rechazadas. `explanation_accepted`: bool de salida generada aceptada. No reemplazar el mensaje de fallback. `inference_executed` histórico se mantiene pero no es contador de runtime ni prueba de que no se intentó inferencia.

Errores: 401 sesión, 403 permisos/origen, 404 desconocido, 413 tamaño, 422 inválido, 429 límite/ocupado, 502 backend/runtime requerido indisponible, 503 almacenamiento/biblioteca. Nunca convertir error, lista truncada, null o resultado inconcluso en normalidad. Cambiar sujeto/evaluación/ciclo invalida respuestas pendientes e historial anterior.

## Autoridad biomédica

Conservar independientemente diagnostic_status, urgency, confirmation_status, differential, next_tests, protocol_status, treatment_status, space_applicability y árbol completo. `missing_required` son ramas indeterminadas necesarias; no significa medir todas las alternativas. `optional_not_measured` no bloquea un árbol ya resuelto; `invalid_required` no se imputa; `required_for_protocol_safety` permanece independiente. Cumplir criterios no firma diagnóstico ni habilita intervención.

Las curvas/indicadores históricos deben usar los IDs de entrada del ciclo y el estado temporal calculado por el motor. Una muestra posterior no sustituye la usada en una evaluación pasada. Baseline o cambio descriptivo no es un umbral médico nuevo.

## LLM / RAG offline

Acceso reader mediante allowlist y scopes existentes; GET de evaluaciones, monitorización, fuentes/criterios y replay. Sin credenciales researcher, escritor ni clave HMAC; sin herramientas para cambiar reglas/autorizar. La documentación tiene autoridad propia, no autoridad sobre el paciente. Mostrar texto exacto, fuente, hash/offsets/versión, pertinencia no adjudicada y rechazos. La recuperación mantiene la limitación 4/12 top-3 y 8/12 top-5 ya documentada; no ejecutar los 12 casos reservados.

## Sensores y simuladores

Se mantienen los modelos Pydantic de adquisición backend y adaptadores existentes. No enviar mediciones a través del token reader del BFF. Aprovisionar fuera del navegador una credencial con el mínimo permiso y scope de adquisición; rechazar unidades/calidad/contexto inválidos mediante contratos existentes. Identificar datos sintéticos y no presuponer sensores disponibles en vuelo. No existe conversión del output del LLM en medición.

## Space Computing / infraestructura

Mismos presupuestos FULL/LOW_POWER/CRITICAL. Reducir contexto solo afecta explicación y recuperación documental, no snapshot ni reglas. Instrumentar intentos, aceptación, fallos de HTTP/aplicación/inferencia/DB por separado. `/api/ps` es residencia declarada por Ollama; GPU global no es energía. Release de modelo explícito y separado de CRITICAL. Rechazar con 429 y conservar acceso clínico si el runtime falla.

`local_protection` es administrativo local, no endpoint del modelo. Backups y restauraciones crean destinos nuevos; HMAC externo verifica prefijo auditado, no protege del control de la misma cuenta. SQLCipher no está activo. Para otros equipos, reprovisionar secretos: DPAPI está ligado a usuario/máquina.

Ejemplos ejecutables y respuestas reales sintéticas: `client_example.py`, `api-examples.json`. OpenAPI: `backend-openapi.json` (también protegido con Bearer en backend), `portal-openapi.json` (exportado localmente, publicación HTTP deshabilitada).

El modo es global a la instancia del portal. Es el presupuesto para próximas solicitudes; runtime.context_tokens puede corresponder al modelo ya residente de un modo anterior hasta la siguiente inferencia. No confundir política objetivo con recarga instantánea.

Los IDs de hallazgos normativos dependen de la versión de implementación; no tratarlos como identificadores estables entre bases preparadas con código distinto. Conservar scope, versionado y referencias originales. La invariancia descriptiva excluye únicamente esa referencia; los hashes originales se verifican dentro de su versión.
