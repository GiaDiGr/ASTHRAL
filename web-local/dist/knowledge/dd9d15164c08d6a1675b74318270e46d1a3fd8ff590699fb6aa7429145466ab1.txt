# Contratos de integración v0.7

API local autenticada Bearer. OpenAPI protegido en `GET /openapi.json`; copia reproducible en `engine/data/v070-final/openapi.json`.

| Operación | Contrato | Permiso |
|---|---|---|
| POST `/monitoring/cycles` | MonitoringRequest → MonitoringResult, HTTP 201 | researcher/clinician, ámbito servidor |
| GET `/monitoring/cycles?subject_id=…&mission_id=…` | lista de MonitoringResult | reader autorizado |
| GET `/monitoring/cycles/{id}` | MonitoringResult, sin request ni replay_records | reader autorizado |
| GET `/monitoring/cycles/{id}/replay` | id, matches, scope, clinical_validation=false | reader autorizado |
| GET `/monitoring/domains` | indicadores, fuentes, límites; no datos personales | autenticado |
| GET `/dashboard/subjects/{subject}?mission_id=…` | contrato anterior + monitoring (últimos 50 ciclos) | reader autorizado |

Frontend: conservar `diagnostic_status`, `urgency`, `confirmation_status`, `protocol_status`, `treatment_status` separados. Cada `clinical_evaluations[condition]` contiene `next_tests`, fuentes, árboles y enlaces de reevaluación. No traducir `notify=false` como ausencia de riesgo. No presentar `DESCRIPTIVE_AVAILABLE`, `REQUIREMENT_MET` ni un valor antiguo como normalidad clínica actual. `as_of` indica la fecha evaluada, no la hora actual del navegador. El listado de dominios no prueba que un sensor exista físicamente en la misión.

Sensores/simuladores: mantener IDs inmutables, timestamps con zona, dispositivo/calibración, calidad, método, protocolo, fase, unidades y procedencia. `clinical_context_id` identifica el contexto explícito cuyos datos pueden arrastrarse; no agrupar episodios distintos automáticamente. `previous_run_id` evita bifurcaciones inadvertidas. `history_start` limita análisis histórico; `clinical_window_start` limita datos actuales; `followup_at` es planificación explícita del solicitante. Ninguno de estos parámetros es un umbral clínico validado por el motor. Asegurar ámbito coherente entre sujeto/misión y referencias.

La petición contiene como máximo 256 mediciones, 256 observaciones y 32 baselines; el cuerpo HTTP sigue limitado a 1 MiB. Si la combinación arrastrada excede los límites clínicos se rechaza atómicamente; ajustar la ventana según política aprobada, sin eliminar silenciosamente datos relevantes. Errores de esquema o consistencia: 422; ámbito/rol: 403; referencia inexistente: 404 (la comprobación previa de ámbito puede responder 403); conflicto de registro SQLite: 409. No reintentar un conflicto de predecesor inventando un ID: leer el último ciclo y reconciliar.

Lógica de datos: `missing_required` contiene candidatos necesarios para resolver ramas, interpretados con su árbol AND/OR; `optional_not_measured` contiene alternativas no bloqueantes; `invalid_required` identifica ramas no resueltas por datos inválidos; `required_for_protocol_safety` es independiente del diagnóstico. Los cuatro estados TRUE/FALSE/UNKNOWN/INVALID se conservan. Una alternativa satisfecha no exige medir la otra; gravedad clínica no concede autorización terapéutica.

RAG/LLM: seguir usando el cliente reader existente y `/clinical/evaluations/{id}`, `/clinical/sources/{id}`, `/clinical/criteria/{id}`. No suministrar credenciales de escritura al proceso LLM. La nueva proyección dashboard es accesible al frontend con su reader; no se añadió una vía para modificar reglas. El asistente explica resultados existentes y puede carecer de un extracto documental nuevo; debe mostrar esa limitación y la fuente del motor.

Recursos: la demostración informa latencias de ciclo y tamaño SQLite. El motor funciona sin el proceso LLM; faltar una medición deja resultado incompleto y no habilita alternativas terapéuticas. No se añadió optimización ni garantía de tiempo real. No podar snapshots/auditoría sin una política explícita de conservación y reproducción.

## Ejemplo de lectura con credencial existente

```powershell
Set-Location C:\Users\Gianni\Desktop\Vigile\engine
$readerHeaders = @{ Authorization = 'Bearer ' + (Get-Content .\data\portal-v070\reader-token.txt -Raw).Trim() }
Invoke-RestMethod 'http://127.0.0.1:8895/monitoring/cycles/B-cycle-0' -Headers $readerHeaders
Invoke-RestMethod 'http://127.0.0.1:8895/monitoring/cycles/B-cycle-0/replay' -Headers $readerHeaders
Invoke-RestMethod 'http://127.0.0.1:8895/dashboard/subjects/v07-crew-C?mission_id=v07-mission-C' -Headers $readerHeaders
```

No imprimir ni compartir `$readerHeaders`. Esta credencial no permite POST. `examples/request-B-cycle-0.json` y `examples/response-B-cycle-0.json` son solicitudes/respuestas reales sintéticas. Para escribir se necesita identidad researcher/clinician configurada por el servidor y las misiones/dispositivos preparados. El comando `monitoring_demo` demuestra ese flujo completo con credenciales efímeras que no se guardan ni se muestran.

Compatibilidad: las rutas existentes siguen disponibles y los contratos se amplían. Los consumidores deben tolerar HYPOGLYCEMIA y nuevos metadatos; no interpretar condiciones desconocidas como descartadas. Los snapshots internos y credenciales nunca se devuelven por los endpoints de ciclos. La reproducción verifica hash de entrada, salida almacenada, conocimiento y código, y reejecuta una base temporal aislada.
