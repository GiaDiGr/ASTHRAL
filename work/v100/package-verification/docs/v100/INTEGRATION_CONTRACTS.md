# Contratos v1.0 R2 · aditivos

Siguen vigentes docs/v011/INTEGRATION_CONTRACTS.md. Backend 8897, BFF 8898, Ollama 8891. Exportaciones backend-openapi.json, portal-openapi.json y structured-fact.schema.json. El BFF no publica una nueva ruta pública OpenAPI. Entradas estrictas Pydantic sin campos extra.

## Persona 1 · Biomedical / Health Intelligence

Motor determinista: autoridad exclusiva. Mantener adquisición/quality/baseline/trend/monitoring/clinical/differential/episode/followup/replay. Siete rutas sin cambios. ClinicalEvaluationResponse separa criterios, confirmación, urgencia, protocolo y tratamiento. missing_required = candidatos de ramas pendientes, NO obligación de medirlos todos; optional_not_measured = alternativas no bloqueantes; invalid_required = datos inválidos bloqueantes; required_for_protocol_safety = seguridad independiente del diagnóstico. Ausente/UNKNOWN/INVALID/STALE no es normal. No habilitar terapia.

Nuevo GET reader /clinical/evaluations/{id}/context: evaluation_id, subject_id, mission_id, as_of, input_hash del snapshot; Pydantic y scope backend. Sin snapshot crudo ni escritura. Nuevos análisis requieren identidad/ámbito de servidor autorizados, no elevar reader por API.

## Persona 2 · Local AI / RAG / voz

ReaderClient sólo GET allowlist. POST /api/assistant: exactamente uno monitoring_id/evaluation_id, question 3..1200 caracteres, history/context compatible, language en|es (opcional, es por defecto). Mantener answer/retrieved/generated/status separados; adiciones structured_facts/explanation_context/timings/speech. MODEL_CONTROLLED_LANGUAGE_EXPLANATION requiere inferencia real aceptada; nunca llamar generado al fallback determinista.

GET /api/voice/status: disponibilidad STT/TTS por idioma, load_verified, recursos/modo/límites/retención. Antes de cargar, available no acredita aún integridad/carga verificada.

POST /api/voice/transcribe: {monitoring_id|evaluation_id, language, audio_base64}; WAV PCM16 mono 16000 Hz, 0.2..40 s, máximo 1,350,000 bytes; JSON hasta 1,820,000. Devuelve text editable, palabras/confianza, capture_seconds/transcription_seconds, requires_user_review=true, automatic_question_submission=false, is_authoritative_measurement=false, retained_audio=false y target_id. No escribe mediciones ni envía consulta automáticamente.

POST /api/voice/synthesize: {response_id,target_id,rate}; rate ENTERO -3..3, sin texto del cliente. Ticket del asistente, TTL 300 s ligado a sesión/objetivo; audio/wav, X-Synthesis-Seconds y no-store. speech.text es exactamente el texto visible que se leerá. En contexto multicondición se declara resumen oral de hechos/rutas urgentes; resto en pantalla. Nunca raw/rejected output. Fallos conservan texto.

Errores: 401 sesión, 403 ámbito/origen, 410 ticket caducado/contexto, 413 tamaño, 422 formato, 429 cuota/ocupado, 503 recurso/componente. Sin rutas/secretos. No bearer en JS/prompt; audio es entrada no confiable.

## Persona 3 · Space Computing

Políticas/telemetría de space_compute.py. CRITICAL sin generación; modos nunca alteran reglas/urgencia. Sin inferencia ≠ modelo descargado de RAM/VRAM. Voz CPU mismo perfil, presión de recursos conserva texto. No afirmar energía/latencia reducidas sin medir. CPU/RAM por proceso, VRAM/GPU GLOBAL etiquetada. No reducir evidencia/ventanas/historia por ahorrar recursos.

## Persona 4 · Full-stack / UX

Cookie HttpOnly/origen exacto, sujeto/misión/frame coherentes. Transcript editable, envío manual. getUserMedia sólo tras pulsación; AudioWorklet local, sin CDNs/cloud/wake word. Cancelar/cambiar contexto/idioma/modo/logout/pagehide/ocultación debe detener tracks/playback y descartar respuestas tardías. Sin soporte de captura, usar texto. TTS por botón, detener y velocidad. No ocultar alerta urgente en Asistente. Fecha del ciclo ≠ fecha de cada muestra.

## Ejemplo browser autenticado, sin bearer

```javascript
const r = await fetch('/api/assistant', {
 method:'POST', headers:{'Content-Type':'application/json'},
 body:JSON.stringify({monitoring_id:'mission-crew-B-cycle-18',
 language:'es',question:'¿Qué datos faltan en esta evaluación?'})
});
const result = await r.json();
// Mostrar answer/retrieved y generated separados. Reproducir sólo tras pulsación.
// Enviar sólo result.speech.response_id, target_id y rate al endpoint TTS.
```

Respuesta DKA real B18: CRITERIA_MET, missing_required=[], optional_not_measured incluye bicarbonato/cetonas urinarias, required_for_protocol_safety incluye potasio, protocolo BLOCKED_MISSING_DATA. En B18p1 llega potasio y persisten otras restricciones/autorizaciones. No implica tratamiento autorizado. Resultados completos sin secretos en e2e-r2/results.json.

Sin migración destructiva. Replay exige hash/versión exacta; congelar fuente/config. Cambios posteriores requieren pruebas y un banco ciego nuevo porque el anterior está usado.