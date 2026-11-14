# Contratos de integración v1.0.1

## Autoridad y compatibilidad

El motor determinista conserva evaluación diagnóstica, urgencia, confirmación, diferencial y elegibilidad del protocolo. management es una proyección documental aditiva, nunca una orden. intervention_indication_decided=false: protocol_indication_supported no decide cada intervención. applicability_status describe el soporte documental/contextual; CONDITIONALLY_APPLICABLE no implica que sus condiciones estén cumplidas ni que exista autorización. Revisar conditions, safety_restrictions, resource_checks y authority_verification juntos.

ClinicalRequest y MonitoringRequest: resource_policy=DECLARED_R2 por defecto, conserva resources y resultados históricos. MISSION_INVENTORY es opt-in, sólo sintético, y rechaza resources declarados simultáneos. Desconocido no se convierte en false: disponibilidad de una prueba permanece null cuando no se ha verificado. Los flags antiguos true conservan su significado en el evaluador R2; la nueva vista documental aclara que no constituyen verificación de inventario.

ClinicalEvaluationResponse añade management opcional, diccionario por condición de ManagementView, validado por Pydantic y referenciado en OpenAPI. Los documentos/intervenciones tienen modelos estrictos. Las rutas auxiliares GET de manejo/registros devuelven envoltura/listas JSON; los registros persistidos añaden campos de servidor al ManagementRecord de entrada. No reutilizar ese modelo de entrada con extra=forbid para deserializar la respuesta ampliada. Un cliente R2 estricto debe migrar al contrato nuevo o proyectar explícitamente los campos R2. No se reescriben registros viejos; legacy_record=true y management=null si no existían. Reproducir R2 con runtime R2 archivado exacto.

## Rutas y permisos

Todas las rutas del backend salvo /health requieren Authorization: Bearer. Identidades, roles y ámbitos provienen del servidor, no del cuerpo. Inventario es de misión (no individual); compartir misión comparte ese recurso, no datos privados de otros astronautas.

| Método/ruta | Contrato | Acceso |
|---|---|---|
| POST /missions/{mission_id}/medical-inventory | InventoryVersion; 201 | researcher/clinician con ámbito de misión |
| GET /missions/{mission_id}/medical-inventory?as_of=... | ResourceSnapshot | reader/operator/researcher/clinician con ámbito |
| POST /clinical/evaluations | ClinicalRequest, resource_policy opcional | permisos clínicos existentes; reader denegado |
| GET /clinical/evaluations/{id} | ClinicalEvaluationResponse | lectura con ámbito de sujeto/misión |
| GET /clinical/evaluations/{id}/management | evaluation_id, management, legacy_record, clinical_execution | lectura con ámbito |
| POST /clinical/management-records | ManagementRecord; 201 y campos de servidor | operator/researcher/clinician, todos los objetos referidos autorizados |
| GET /clinical/evaluations/{id}/management-records?as_of=... | lista de registros humanos | lectura con ámbito |
| GET /dashboard/subjects/{subject}?mission_id=...&frame_id=... | checkpoint completo congelado | reader con ámbito |
| GET /openapi.json | esquema de esta versión | autenticado |

No endpoint para aprobar autoridad terapéutica, ejecutar, dispensar, consumir existencias ni modificar reglas. Añadir campos role/authorization/execution al cuerpo no eleva privilegios; contratos de entrada estrictos los rechazan. Un rol clinician informático tampoco acredita autoridad médica de misión. reader/LLM no recibe tokens operator/researcher/clinician. El portal usa reader y no añade mutaciones de inventario o seguimiento.

## Inventario y tiempo

InventoryVersion contiene id, mission_id, version entera consecutiva desde 1, supersedes, effective_at=updated_at, source, responsible, resources y synthetic=true. Recurso: id/kind/label, quantity/unidad, availability, verification/verified_at, expires_at, storage_status/storage_conditions, integrity_status, requires_cold_chain/cold_chain_status, updated_at, source/responsible. Cantidad finita no negativa, sin booleanos como números, recursos únicos y máximo 64. No se interpretan unidades como conversión de dosis; cantidad positiva no demuestra suficiencia para una pauta.

Cada versión es un manifiesto completo; ausencia de un recurso no hereda disponibilidad. availability=AVAILABLE sin verificación no basta. Ausente -> RESOURCE_UNVERIFIED con ABSENT_FROM_MISSION_MANIFEST; desconocido -> RESOURCE_UNVERIFIED; vencido (expires_at<=as_of), vacío, comprometido o almacenamiento incumplido -> RESOURCE_UNAVAILABLE. Medicamentos/consumibles requieren cantidad, unidad y caducidad; medicamentos también declaración de cadena de frío. Recursos físicos requieren integridad/almacenamiento. Insulina y epinefrina no pueden declararse CAPABILITY para evitar controles. Son verificaciones de software sobre declaraciones sintéticas, no inspección farmacéutica.

Sólo versión efectiva<=as_of. Se rechaza un cambio con effective_at<=cualquier evaluación/ciclo ya comprometido de esa misión, así como retroceso temporal/linaje incorrecto. Se conserva snapshot de recursos e inventory_hash en la evaluación; selección y persistencia clínica ocurren en la misma transacción. MISSION_INVENTORY incorpora inventario al snapshot de monitorización; DECLARED_R2 no lo reinterpreta. Los replays usan snapshots congelados, nunca manifiestos actuales.

Fechas timezone-aware. occurred_at y recorded_at de ManagementRecord son tiempos declarados de la simulación, no sellos de recepción confiables: occurred_at<=recorded_at, ocurrido no anterior a la evaluación y mediciones no posteriores al registro. GET as_of filtra esos tiempos declarados; no reconstruye lo que el servidor sabía entonces. Auditoría conserva recepción real. Para conocimiento a recepción usar mission_frame congelado en el checkpoint, no una consulta por fecha. El dashboard sin frame sigue siendo vista viva.

## Seguimiento

Estados: DOCUMENTED, PROPOSED, REVIEW_PENDING, HUMAN_REPORTED_PERFORMED, POST_INTERVENTION_OBSERVATION. Se vinculan episode_id/evaluation_id/intervention_id de la MISMA ruta clínica; followup_plan_id opcional del mismo episodio, measurement_ids del mismo sujeto/misión. Datos pendientes son etiquetas documentales, no pruebas ordenadas. Texto/fuente/autoridad declarada se presentan como no verificados. El servidor fija authority_verification=NOT_VERIFIED, execution_by_vigile=false, authorization_by_vigile=false y efficacy_verified=false. Registro inmutable: corrección mediante nuevo registro identificable, no sobrescritura. No cambia treatment_status=NOT_STARTED ni adjudica causalidad/eficacia.

## Consumidores

Frontend: mostrar urgencia fuera de paneles ocultables; luego intervención, condiciones, precauciones incompletas, recursos, autoridad y seguimiento. No deducir normalidad/seguridad de listas vacías. reference_only contiene pauta original documental y condiciones de texto NO ejecutadas. monitoring no es agenda. Sin órdenes de tratamiento en esta UI.

LLM/RAG: conservar contrato/proyecciones autorizadas existentes. No se añade herramienta de escritura ni se modifica inferencia. Puede explicar decisiones existentes según controles previos; no completar indicación, contraindicación, recursos o autoridad por generación. Los nuevos documentos se muestran determinísticamente en el portal; no se afirma haber evaluado generación libre nueva sobre ellos. Ollama y modelo originales intactos. El motor y manejo operan sin Ollama ni red externa.

Optimización: mismas rutas de FULL/LOW_POWER/CRITICAL y núcleo clínico; no saltar bloqueos ni cambiar desconocidos por normales. Esta revisión no modifica presupuestos computacionales ni promete latencia de vuelo. Simulador/sensor: enviar observaciones con unidades/calidad/tiempos mediante contratos existentes; inventario sólo mediante identidad de servidor autorizada. No se presupone disponibilidad de dispositivos.

Errores: 401 sin token válido; 403 ámbito/rol insuficiente; 422 validación/linaje/tiempo/política incompatibles; 409 intento de reutilizar ID inmutable; 404 referencia inexistente después de autorización (middleware puede negar 403 sin revelar existencia). Sin credenciales en ejemplos ni logs de entrega.

## Límites de seguridad

SQLite/WAL/backups SIN CIFRADO. DPAPI y ACL protegen credenciales locales, no aislan procesos de la misma cuenta. Un atacante que controla almacenamiento/código puede reescribir datos y recalcular hashes: integridad verificable interna no es anclaje externo ni firma clínica. Falta aislamiento de procesos/roles operacionales y política médica verificada. Sólo loopback de desarrollo; no publicación de puertos ni datos reales. Sin autorización terapéutica bajo ninguna combinación de recursos/roles de esta demo.
