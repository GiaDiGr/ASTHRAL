from pathlib import Path
R=Path(__file__).resolve().parents[2]; D=R/'docs/v101'
(D/'INTEGRATION_CONTRACTS.md').write_text('''# Contratos de integración v1.0.1

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
''',encoding='utf8')
(D/'IMPLEMENTATION.md').write_text('''# Implementación incremental v1.0.1

No se reconstruyó el motor, cambió la base SQL ni se creó un segundo motor terapéutico. Se reutilizan Store transaccional/auditable, clinical_knowledge, protocolos, episodios, followups, proyecciones y permisos existentes. La vista documental es determinista y está incluida en los hashes/replays de evaluaciones nuevas. Inventario y registros usan los mismos registros inmutables que el resto del sistema. Las evaluaciones R2 no reciben enriquecimiento retroactivo.

## Cobertura de las brechas autorizadas

| Brecha | Implementación | Límite explícito |
|---|---|---|
| G01 | Intervenciones documentales estructuradas desde protocolos previos; indicación del protocolo separada de decisión individual | No se ejecutan condiciones textuales/dosis/secuencias; precauciones incompletas |
| G02 | Manifiestos sintéticos versionados por misión, recursos/caducidad/integridad/fuente, persistencia y permisos | Sin inventario NASA, reservas, consumo ni suficiencia cuantitativa de una pauta |
| G03 | Política opt-in, snapshot atómico, recursos vinculados a elegibilidad existente y pruebas, replays | DECLARED_R2 intacto; nuevo runtime no sustituye archivado R2 |
| G04 | Cinco estados de declaraciones humanas ligados a episodios/planes/mediciones | No autorización, ejecución, eficacia ni transición automática de tratamiento |
| G05 | Bloqueo previo conservado | NO_VERIFIED_MISSION_POLICY; no aprobación ficticia |
| G06 | Registro/versiones/hash de fuentes y señales de incertidumbre por intervención | Revisión clínica primaria terapéutica incompleta; decisiones en CLINICAL_REVIEW.md |
| G07 | Portal reader: manejo/seguridad/recursos/autoridad/seguimiento; urgencia visible | HTTP y DOM simulado comprobados; inspección visual real pendiente por fallo CUA |
| G08 | Textos exactos previos de vías espaciales C001/C002/C003/C005/C012/C013/C014/C032 | Biblioteca documental, dependiente de misión; sin nuevo motor ni recomendación individual |

## Archivos nuevos

- engine/vigile/management.py: contratos, inventario/snapshot, evaluación documental de recursos, seguimiento y rutas.
- engine/vigile/web/management.js: presentación determinista reader; sin fetch, innerHTML o comandos terapéuticos.
- engine/tools/demo_management_v101.py: preparación fresca y supervisor loopback propios.
- engine/tests/test_management_v101.py: 54 casos, incluyendo parametrizaciones.
- engine/tests/management_ui_unit.cjs y fixtures/management-v101-report.json: seis escenarios DOM simulados sin navegador real.
- docs/v101/* y VIGILE_v101_START_HERE.md: evidencia de entrega; work/v101/* conserva scripts/checkpoints de desarrollo, no es fuente de credenciales para consumidores.

Archivos modificados exactos frente al ZIP R2: change-manifest.json. Cambios de integración: clinical_models/monitoring_models (resource_policy), clinical_engine (snapshot/transacción/proyección/replay), clinical_contracts (campo aditivo), monitoring (snapshot opt-in), api/security (rutas y ámbito), dashboard_api/mission_frames (lectura/congelación), portal/index/style y pyproject (asset/metadatos). No cambios en funciones diagnósticas, clínica declarativa, fuentes científicas originales, Ollama/Norton ni pesos.

## Correcciones de representación verificadas

Potasio afecta a documentos de insulinoterapia, no a todo soporte DKA. Revisión de capacidad IV no ordena fluidos ni presume pauta segura. Criterios no cumplidos no deciden NOT_APPLICABLE para una intervención; sólo NOT_APPLICABLE del contexto original se conserva. Sospecha de anafilaxia con urgencia no se convierte en confirmación. Las acciones de soporte sin mapeo de recurso completo quedan RESOURCE_UNVERIFIED, no heredan epinefrina indebidamente. Deglución usa último dato válido, coherente y dentro de ventana; ausencia/conflicto/invalidez/futuro quedan desconocidos sin nuevo régimen oral.

Recursos desconocidos no se convierten en pruebas indisponibles; su disponibilidad permanece null. Recurso ausente y no disponible se diferencian por estado/motivo. Caducidad exacta excluye disponibilidad. Manifest futuro o de otra misión no se incorpora. Se impide reescribir contexto ya comprometido. Seguimiento no puede tomar intervención de otra ruta en una evaluación compuesta ni adjuntar mediciones de otro astronauta. Ninguna combinación desbloquea administración.

## Preservación y límites

Recuperabilidad R2 comprobada antes de modificar: ZIP SHA y backup SQLite en checkpoint.json, original conservado; 76 replays con runtime archivado en copia aislada. Comparación exacta de 30 resultados clínicos R2/v1.0.1 incluyendo diagnóstico, diferencial, pruebas, urgencia y elegibilidad; conocimiento sin cambios. La suite completa usa datos sintéticos y directorios temporales, no base congelada. Los resultados reales finales están en RESULTS.json; registros de desarrollo conservados con nombres separados no equivalen al resultado final.

Sin nuevas dependencias; versión 1.0.1, Python>=3.11, FastAPI/Pydantic/SQLite/pytest existentes, Windows DPAPI para demo protegida. La prueba física de voz anterior continúa pendiente. No se reejecutó el banco reservado LLM/RAG ni se declara validación de nuevas explicaciones libres.

No implementado: terapia autónoma, autorización clínica, reservas/dispensación/consumo, cálculo ejecutable de dosis, pautas orales nuevas, catálogo exhaustivo de contraindicaciones, tratamiento SANS, cáncer individual, cambios farmacológicos por microgravedad, nuevos diagnósticos, nuevos algoritmos clínicos ni nuevo motor de contramedidas. Estas pruebas de software no validan clínica, operación ni vuelo.
''',encoding='utf8')
(R/'VIGILE_v101_START_HERE.md').write_text('''# VIGILE v1.0.1 — entrega de apoyo terapéutico

Instrucciones exactas y demostración: [docs/v101/README.md](docs/v101/README.md).

- Implementación, brechas y archivos: [IMPLEMENTATION.md](docs/v101/IMPLEMENTATION.md) y change-manifest.json.
- Contratos/permisos/tiempo/compatibilidad: [INTEGRATION_CONTRACTS.md](docs/v101/INTEGRATION_CONTRACTS.md).
- Conflictos científicos y revisión humana: [CLINICAL_REVIEW.md](docs/v101/CLINICAL_REVIEW.md).
- Resultados: docs/v101/RESULTS.json, final-tests.xml, examples.json, http-integration.json y clinical-invariance-*.json.

Portal sintético preparado: http://127.0.0.1:8902/ mientras el supervisor está activo. No distribuir códigos de acceso ni la base. Todas las intervenciones siguen bloqueadas para ejecución; los registros humanos no prueban administración, autorización ni eficacia. Sin datos clínicos reales, sin validación clínica/operacional/de vuelo. Ver limitaciones de SQLite sin cifrado, aislamiento, revisión visual y voz en README.
''',encoding='utf8')
print('Wrote integration, implementation and start-here documentation')