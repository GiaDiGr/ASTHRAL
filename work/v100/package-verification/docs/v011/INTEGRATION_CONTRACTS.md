# Contratos de integración v0.11 (aditivos)

OpenAPI completo: engine/data/mission-v011-final/openapi.json y backend-openapi.json. API local Bearer; BFF por cookie HttpOnly/SameSite=Strict y POST con Origin exacto. No exponer las claves en frontend, prompts, capturas o repositorios. Las credenciales determinan rol/ámbito en servidor, no campos del cliente.

## Frontend / UX

Backend 8897, BFF/portal 8898. GET /health es público; OpenAPI requiere identidad autorizada. Rutas reader:

- GET /dashboard/subjects: perfiles visibles.
- GET /dashboard/frames/{subject_id}?mission_id=mission-v011: lista FrameIndex (id, as_of con zona, phase, gravity, monitoring_id, snapshot_hash SHA256).
- GET /dashboard/subjects/{subject_id}?mission_id=mission-v011&frame_id={frame_id}: proyección congelada. Sin frame_id conserva proyección actual compatible.
- GET /monitoring/cycles/{id} y /replay; GET /clinical/evaluations/{id} y /replay; criterios, fuentes y protocolos existentes.

BFF equivalentes: /api/subjects, /api/frames/{subject_id}, /api/dashboard/{subject_id}, /api/replay/{monitoring|clinical}/{id}, /api/source/{id}, /api/protocol/{id}, /api/document/{id}. Índice sólo muestra fechas/fases; nunca anticipar contenido médico del checkpoint futuro. historical_frame y knowledge_time identifican la proyección; seleccionar un ciclo con frame debe actualizar todo el contexto y descartar respuestas tardías. Backend comprueba también ámbito del frame, no sólo de la URL. No hay endpoint reader para crear/modificar frames o contextos.

Ejemplo de solicitudes, con token reader sólo en el cliente de servidor:

```http
GET /dashboard/frames/mission-crew-B?mission_id=mission-v011
Authorization: Bearer <reader protegido, nunca en navegador>

GET /dashboard/subjects/mission-crew-B?mission_id=mission-v011&frame_id=frame-mission-crew-B-cycle-18
```

El JSON de esa vista contiene historical_frame.monitoring_id=mission-crew-B-cycle-18, mission.phase=IN_MISSION, mission.gravity=MICROGRAVITY y clinical_execution=BLOCKED. api-examples.json contiene solicitudes y respuestas reales sin credenciales.

## Biomedical y adquisición

operator: POST /measurements con Measurement existente (ID inmutable, subject/mission, valor o ausencia explícita, unidad, timestamp zonado, dispositivo/calibración, método/protocolo, fase, calidad y procedencia). El token nuevo de adquisición está en acquisition-token.txt protegido con DPAPI, separado de la configuración del BFF. Su ámbito es sólo los dos sujetos/misión sintéticos. No puede crear dispositivos, contextos ni ejecutar ciclos/evaluaciones de investigación.

researcher/clinician: las rutas existentes de dispositivos, baselines y ciclos. Nuevo POST /missions/{id}/contexts recibe MissionContextVersion: id, mission_id, effective_at y MissionContext sintético coincidente. Fechas estrictamente crecientes y posteriores a ciclos comprometidos. Sólo contexto de misión, sin cambiar criterios clínicos. La CLI usa una identidad temporal de investigador para preparar la misión y no la conserva en credenciales de entrega; para adquisición/evaluación adicional el equipo debe provisionar su identidad de servidor con el rol/ámbito aprobado, sin elevar un reader desde la API.

ClinicalEvaluationResponse conserva missing_required, optional_not_measured, invalid_required y required_for_protocol_safety. No confundir alternativas AND/OR con listas de pruebas obligatorias ni seguridad con diagnóstico. No eliminar estados UNKNOWN/INVALID, urgencia o confirmación. Protocolos y tratamientos siguen bloqueados. Estados de episodios y planes no acreditan diagnóstico firmado ni recuperación.

## Local AI / RAG

Mantener ReaderClient y su allowlist; sólo GET autorizados. POST /api/assistant exige exactamente uno de monitoring_id/evaluation_id, pregunta 3..1200 caracteres, hasta tres preguntas previas y history_context_id. Historial ajeno se descarta. El objetivo debe ser el seleccionado del frame, nunca el ciclo final mientras se muestra un instante anterior.

La respuesta conserva answer/retrieved/generated por separado, referencias, estado, inferencia y contexto. Estados aditivos:

- DETERMINISTIC_DATA_SUFFICIENCY: clasificación del motor.
- DETERMINISTIC_TEST_RECOMMENDATIONS: recomendaciones existentes, no órdenes.
- DOCUMENT_EXCERPTS_ONLY: documentos/criterios implementados, no decisión de paciente.
- EXTRACTIVE_ONLY: resultados exactos, incluida degradación offline/CRITICAL.
- EXTRACTIVE_FALLBACK o REJECTED_OR_FAILED: no mostrar texto rechazado como respuesta generada.
- ANSWERED sólo con generated no vacío cuando realmente fue aceptada la explicación; otros proveedores históricos pueden usar selección extractiva, por lo que debe inspeccionarse generated/kind.

failure_trace publica category, code, stage, exception_type y clinical_state_changed=false. Códigos acotados: nunca serializar str(exc). inference_trace.model_requests_attempted cuenta POST intentados, no inferencias completadas; explanation_accepted refleja aceptación. El legacy inference_executed no es contador de solicitudes. Fuente documental o verificador no puede anular el resultado del motor. No dar al modelo tokens, rutas de archivos de secretos, herramientas de escritura ni facultad de modificar reglas.

## Space Computing / recursos

POST /api/mode con FULL, LOW_POWER o CRITICAL afecta al asistente global del portal, no a reglas ni urgencia. Sólo con sesión y Origin correctos. Cambiar modo no descarga automáticamente un modelo residente. GET /api/status y /api/runtime distinguen conexión, memoria observada/no observada y ausencia de inferencia.

Medidas iniciales: RESULTS.json/performance. Latencias de ciclo son ASGI TestClient + SQLite, no red/LLM. CPU y memoria corresponden al proceso de simulación de escritorio; sin medida energética ni benchmark de vuelo. La inyección de indisponibilidad de mission_review afecta su adaptador y no detiene procesos. Si faltan recursos, conservar resultados/evidencia y explicitar abstención; nunca alterar criterios clínicos.

## Persistencia y compatibilidad

Sin migración destructiva de SQLite. Nuevos registros mission_context y mission_frame en el Store append-only. FrameIndex tiene contrato Pydantic/OpenAPI. La proyección histórica mantiene las claves de dashboard y agrega metadatos. Funciona sólo donde existen checkpoints capturados; no fingir reconstrucción para datos históricos de 0.10. Replays exigen código y conocimiento originales. Las 12 preguntas reservadas sólo se verifican por hash.