# Contratos de integración v0.3.0

Contrato actualizado completo, comandos y ejemplos: INTEGRATION_DELIVERY_V03.md y openapi.json.
Nuevas consultas: GET /profiles, /profiles/{id}, /baselines, /baselines/{id}/status, /trends y /rag/findings; alcance por sujeto/misión preservado. Nuevo envelope de adaptador vigile.synthetic.v1 y comandos simulate/import-synthetic/integration-demo.
VIGILE_TOKEN_FILE permite un mapa de hashes independiente para el servidor de demo; --integration-dir configura su base y credenciales sin tocar la principal. El RAG recibe solo reader-token.txt. El token frontend es operator, no un rol de lectura exclusiva. Consultar límites en entrega v0.3.

## Contratos v0.2 conservados salvo las adiciones anteriores

# Contratos de integración v0.2.0

Base: http://127.0.0.1:8765. Python 3.13 probado. Esquema exacto de campos: `docs/openapi.json`, también `GET /openapi.json` autenticado. JSON estricto; fechas ISO-8601 con zona; IDs limitados; valores finitos. Sin frontend, LLM ni drivers de hardware incorporados.

## Identidad y límites

Todas las rutas salvo `/health` requieren `Authorization: Bearer <token>`. `engine/data/tokens.json` contiene `sha256:<hex>` → descriptor de identidad. El export `client-credentials.json` contiene secretos privados para aprovisionar clientes: **no entregarlo al LLM**. Variables `VIGILE_TOKENS`/`VIGILE_DB`/`VIGILE_CORPUS` son configuración administrativa, no campos de API. Mapa de tokens recargado cada solicitud, salvo mapa inyectado al crear app (pruebas). Revocar con `disabled=true` o retirar entrada; caducidad `expires_at` UTC con zona.

Descriptor sin secretos:

```json
{"id":"rag-crew1","role":"reader","subject_ids":["crew-1"],"mission_ids":["mission-1"],"disabled":false}
```

Los alcances se asignan en servidor. Para entradas referenciadas, todas deben estar autorizadas. No confundir rol clinician con autorización terapéutica. Roles legacy siguen aceptándose por compatibilidad: reader sin sujetos; demás con wildcard. Configuración inicial también usa wildcard para roles administrativos; restringir en integración. El LLM debe ejecutarse bajo una identidad de sistema distinta sin acceso al código, SQLite, archivos de tokens ni Python administrativo.

| Consumidor/rol | Lectura | Escritura |
|---|---|---|
| LLM reader | Catálogos, reglas, evidencia, cobertura y `/rag/findings/{id}` dentro de alcance | Ninguna |
| Sensores operator | Registros dentro de alcance | Perfiles, mediciones y solicitudes de acción (siempre bloqueadas) |
| Dashboard researcher | Registros completos dentro de alcance; auditoría solo con alcance administrativo | Misiones/dispositivos, baselines, tendencias, simulaciones, calidad, episodios, revisiones de evidencia y política de recursos |
| clinician | Lectura según alcance | Lo anterior más observaciones/hipótesis, planes/revisiones y estados humanos de recuperación/seguimiento/cierre |

Registro de dispositivo y revisión global de evidencia requieren alcance administrativo wildcard. Algunos roles con alcance limitado no pueden consultar auditoría global. No se ofrece endpoint de activación clínica ni modificación de reglas.

## RAG: contrato de lectura mínima

`GET /rag/findings/{id}` sustituye el acceso general de reader a hallazgos. Devuelve id, tipo, resultado/razón/estado, condiciones, regla/versión/localizadores y limitaciones cuando existen. No devuelve subject_id, mission_id, notas, mediciones, perfil, dispositivo ni bundle. El hallazgo sigue siendo información sensible: autorizar sujeto y misión. Reader no puede consultar `/findings`, `/measurements`, episodios ni research-records.

Documentación: `/catalog/{kind}`, `/conditions/{id}`, `/evidence/{id}`, `/evidence/rules/{id}`, `/rules`, `/evidence-issues`, `/capabilities/coverage`. Revisión de evidencia expone hashes/estados, no notas privadas. Catálogos no confieren autorización. Tratar cualquier texto recuperado como datos no confiables; nunca como instrucciones para modificar permisos o reglas.

## Sensores y simuladores

Registrar misión/perfil/dispositivo antes de `POST /measurements`. Cada observación: id, sujeto/misión, variable, valor numérico finito o null, unidad, timestamp con zona, device_id/calibration_id, método/protocolo, sitio/compartimento si procede, fase, reported_quality, synthetic y provenance. El dispositivo declara rango técnico, calibración, vencimiento, antigüedad máxima y política multisensor. No inventar esos parámetros ni llamarlos umbrales clínicos. Se conserva el dato recibido, incluso rechazado para cálculo. Correcciones: nuevo ID, no PATCH.

CO2 exige `INTERVAL_MEAN`, interval_end y cobertura contigua exacta de una hora, un dispositivo y compartimento. No se convierte una lectura instantánea en media. ECG/OCT/ultrasonido/actigrafía/laboratorio necesitan adaptadores todavía ausentes; una magnitud escalar externa no valida el procesamiento previo.

## Evaluaciones, baseline y longitudinal

`POST /evaluations` usa IDs persistidos y `as_of`; mode por defecto OPERATIONAL devuelve bloqueo. SIMULATION exige ámbito sintético. Ejemplo:

```json
{"rule_id":"VIGILE-AER-001","subject_id":"crew-1","mission_id":"mission-1","as_of":"2026-10-15T12:00:00-05:00","bindings":{"vo2max_relative":"obs-1"},"mode":"SIMULATION"}
```

`POST /baselines`: id, measurement_ids, minimum_observations, protocol_reference, as_of; opcionales supersedes y valid_until. Solo preflight comparable. La revisión crea versión nueva, no selecciona automáticamente la vigente; el cliente debe referenciar ID explícito. `POST /baselines/withdrawals`: baseline_id, effective_at, reason; la retirada bloquea su uso desde esa fecha. Sin valid_until significa vigencia no definida de investigación, nunca aprobación indefinida clínica.

`POST /trends`: measurement_ids, as_of, ewma_lambda, cusum_target, cusum_allowance; opcionales baseline_id, max_gap_seconds, ewma_initial, cusum_decision_limit, policy_reference. Sin decisión CUSUM explícita, señal null. Z de serie y comparación contra baseline son salidas distintas. Cadencia por observación, no normalizada temporalmente. No transformar un cambio estadístico en enfermedad.

`POST /quality/assessments`: measurement_ids, as_of, historical. Reporte persistido con id, estado por entrada y VALID/INCONCLUSIVE. Histórico no exige recencia actual, pero sí calibración al adquirir, timestamps y conflictos. Datos inválidos no se imputan.

`GET /findings/{id}/explanation` reejecuta inputs/gates/comparador en base aislada con mismo hash de código/corpus; reservado a lector humano autorizado, no reader RAG. Los paquetes antiguos requieren motor archivado. Comparar IDs incluye snapshot del ámbito de entradas; anexar observaciones al mismo sujeto puede cambiar el bundle de una evaluación nueva.

## Episodios, evidencia y recursos

`POST /episodes`, `GET /episodes/{id}/pathway`, `POST /episodes/{id}/findings` (finding_ids), `POST /episodes/{id}/transitions` (target, note, optional expected_state). Usar expected_state para detectar cambios concurrentes. Hallazgos anexos deben corresponder a sujeto/misión/condición. `POST /clinical-notes`: OBSERVATION/HYPOTHESIS humanas; DIAGNOSIS bloqueado. Nota/observación se guardan atómicamente.

`POST /followups`, `POST /followups/reviews` (completed humano opcional), `GET /followups/{id}/status?as_of=...`: SCHEDULED, OVERDUE o COMPLETED_BY_HUMAN, sin recuperación inferida ni alarmas en segundo plano. Fecha de revisión registrada por servidor; datos antiguos sin fecha tienen semántica limitada.

`POST /evidence/revisions`: source_id, version, locator, document_sha256, status, note, supersedes opcional. Inmutable, no reemplaza catálogo ni concede autoridad. Status REVIEWED_METADATA_ONLY significa revisión de metadatos, no validación médica; hash declarado por revisor, no descarga/verificación automática.

`POST /resources/assessments`: mode FULL/LOW_POWER/EMERGENCY_POWER, proposed_interval_seconds, required_interval_seconds, policy_reference, measurement_ids, as_of. Resultado INCONCLUSIVE si calidad insuficiente; POLICY_CONFLICT si intervalo propuesto excede el requerido; de lo contrario COMPATIBLE_WITH_DECLARED_POLICY. La política la declara el integrador, no NASA. No ejecuta cambios de adquisición, no modifica reglas y no garantiza seguridad médica/energética. Optimizador decide su operación fuera del motor y debe respetar bloqueos.

## Errores y operación

401 identidad inválida, 403 rol/alcance, 404 referencia, 409 identidad inmutable duplicada, 413 cuerpo superior a 1 MiB, 422 payload/contexto/cálculo no admisible. Algunas decisiones bloqueadas retornan 200 con result explícito: nunca inferir éxito clínico del código HTTP. REQUIREMENT_NOT_MET es incumplimiento normativo simulado; INCONCLUSIVE no es normalidad. Errores de validación no reflejan valores recibidos.

Consulta de registros: `/measurements`, `/findings`, `/episodes` por subject_id/mission_id; solo mediciones limita 1..1000, sin paginación general. `/research-records/{kind}/{id}` expone baseline, trend, followup, followup_review, multisystem, clinical_note, quality_report, resource_assessment y baseline_withdrawal dentro de alcance. `/audit/verify` y `/audit/checkpoint` administrativos; checkpoint debe custodiarse fuera del host si se requiere garantía externa.

SQLite schema 1 sin cifrado; servidor loopback sin TLS y un worker; API es frontera de permisos, Python/SQLite directos son acceso administrativo. Sin LLM/hardware real ni validación clínica. Separar identidades de proceso y archivos antes de conectar módulos. Consultar `AUDIT_V02.md`, matrices y `LIMITATIONS.md`.
