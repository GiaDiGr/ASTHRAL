# Implementación incremental v1.0.1

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
