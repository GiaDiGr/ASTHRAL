# Contratos VIGILE 0.5.0

## Componentes y autoridad

| Componente | Contrato | Restricción |
|---|---|---|
| Frontend | HTTP same-origin /api/* del portal; cookie de sesión | Sin bearer backend, sin escrituras clínicas |
| Portal/BFF | ReaderClient → HTTP API backend | GET explícitos, rol reader comprobado y scopes |
| LLM/RAG | LocalInference.status() y select(question, blocks) | Solo IDs existentes; sin herramientas ni acceso a DB |
| Sensores/simulador | API /devices, /measurements y bindings clínicos existentes | Credenciales de ingestión en otro proceso; no compartir con portal |
| Motor clínico | /clinical/evaluations y demás contratos v0.4 | Autoridad exclusiva; no habilitar tratamiento |
| Optimización | Medir procesos/latencia/disco externamente | Puede apagar inferencia; no omitir validaciones ni modificar umbrales |

No hay integración de frontend externo mediante CORS. Servir frontend desde el portal o diseñar explícitamente un nuevo despliegue autenticado. No usar claves en JavaScript, URLs, localStorage ni variables de compilación públicas.

## API backend añadida

- GET /dashboard/identity → {role,id}.
- GET /dashboard/subjects → perfiles filtrados por scopes de credencial.
- GET /dashboard/subjects/{subject_id}?mission_id={mission_id} → profile, mission, measurements, baselines, trends, findings, evaluations, limits, clinical_execution. measurement conserva el envoltorio de ingestión y quality del motor. evaluations son proyecciones clínicas con observations/as_of/condition_id/presentation_id; no exponen snapshot. IDs históricos pueden cambiar entre demos; no codificarlos.
- Contratos completos Pydantic/API: openapi-v05.json. Las APIs clínicas previas conservan semántica y protección. Las modificaciones por reader responden 403, no elevan privilegios por campos role o authorization del body.

## API del portal

| Método/ruta | Entrada | Salida |
|---|---|---|
| POST /api/login | {code: código de portal} y Origin exacto | {authenticated:true}, cookie HttpOnly |
| POST /api/logout | {} y Origin | Revoca sesión |
| GET /api/status | sesión | backend, network, assistant, clinical_execution, version |
| GET /api/subjects | sesión | perfiles autorizados |
| GET /api/dashboard/{id}?mission_id=... | sesión | proyección completa del dashboard |
| GET /api/source/{id} | sesión | source y source_status |
| GET /api/protocol/{id} | sesión | document y execution_enabled:false |
| POST /api/assistant | {evaluation_id,question}, Origin, sesión | status, inference_executed/attempted, retrieved, answer, sources, model_status, evaluation_id |

question: 3–1200 caracteres; body máximo 16384 bytes. 401 sesión ausente; 403 origen/método prohibido; 422 entrada inválida; 429 límite/intentos/inferencia ocupada; 502 backend no disponible/acceso rechazado; 503 credencial no reader. Errores sanitizados; no distinguir todos los errores backend desde navegador. Ningún POST de este portal modifica resultados clínicos.

Estados de asistente: UNAVAILABLE (evidencia disponible, no inferencia), ANSWERED (extractos seleccionados), INSUFFICIENT_INFORMATION (selección vacía), REJECTED_OR_FAILED (inferencia fallida o IDs no permitidos). Mostrar mensaje/status sin convertir UNAVAILABLE en una respuesta LLM. Cada bloque tiene id, kind, text, reference. answer es subconjunto literal de retrieved; referencias con evaluation_id/input_hash/source_ids o criterion_id/version. No presentar probabilidades.

## Ejemplo de cliente del portal

Tras abrir sesión en el navegador, estas son las mismas solicitudes que realiza app.js:

```javascript
const subjects = await fetch('/api/subjects', {cache:'no-store'}).then(r=>r.json());
const s = subjects[0];
const d = await fetch(`/api/dashboard/${encodeURIComponent(s.id)}?mission_id=${encodeURIComponent(s.mission_id)}`).then(r=>r.json());
const reply = await fetch('/api/assistant', {
  method:'POST', headers:{'Content-Type':'application/json'},
  body:JSON.stringify({evaluation_id:d.evaluations[0].id,question:'¿Por qué está bloqueado el protocolo?'})
}).then(r=>r.json());
```

El navegador incorpora Origin/cookie; no establecer Authorization. Respuesta resumida sin modelo: `{ "status":"UNAVAILABLE", "inference_executed":false, "inference_attempted":false, "answer":[], "retrieved":[...], "sources":[...] }`. Ejemplos completos de solicitudes y respuestas del motor: synthetic-http-transcript.json y request-*.json en la carpeta de demo. Son datos sintéticos, no contratos clínicamente validados.

## Inferencia y degradación

Ollama GET /api/tags y POST /api/chat; stream:false, JSON schema evidence_ids, temperature:0, num_predict:256, num_ctx:4096. Sin tools ni downloads. Máximo 12 extractos recuperados, 900 caracteres por bloque en contexto, 8 IDs seleccionados, respuesta leída hasta 64 KiB, timeout 40 s, estado 2 s. La selección del modelo no tiene garantía determinista; la evaluación clínica sí permanece independiente. Pruebas del adaptador usan HTTPX MockTransport y no prueban un modelo real.

Fallo de inferencia → evidencia recuperada y estado explícito; motor sigue funcionando. Falta de backend → error visible, sin generar evaluaciones sustitutas. Recursos limitados → desactivar model (null) o detener Ollama; portal y reglas siguen. CPU/RSS y carga sostenida pendientes. Aislar filesystem y salida de red del proceso de inferencia para aislamiento real.

## Versiones y reproducción

No cambiar JSON de conocimiento desde frontend/RAG. Versionar mediante proceso del motor y conservar manifiestos. Comparar input_hash/output_hash/knowledge_hash/implementation_hash y endpoint /clinical/evaluations/{id}/replay. La app no firma diagnósticos ni añade autorización humana. Las observaciones históricas, confirmación de criterios y diagnósticos clínicos firmados son conceptos distintos.
