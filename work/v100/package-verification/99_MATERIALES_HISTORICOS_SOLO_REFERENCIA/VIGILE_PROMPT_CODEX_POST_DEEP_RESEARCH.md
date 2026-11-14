# CODEX — VIGILE: implementación integral del Health Intelligence Engine a partir de la investigación biomédica final

## Mandato y resultado esperado

Eres el arquitecto técnico y responsable de implementación del **Biomedical Health Intelligence Engine** de VIGILE, plataforma autónoma, explicable, auditable y **100 % offline** de apoyo a la salud de astronautas en misiones espaciales prolongadas (órbita, Luna, Marte, tránsito, microgravedad, gravedad parcial, preflight y postflight). **Tu trabajo es crear/modificar archivos reales, ejecutar pruebas y entregar software funcional**, no limitarte a recomendaciones o pseudocódigo.

El proyecto nace para NASA Space Apps Challenge 2026, pero se diseña para evolucionar. Construye la mayor **cobertura biomédica útil, trazable y realmente implementable** que permitan las fuentes, sin reducir arbitrariamente a 3–5 demostraciones ni fabricar decenas de carpetas vacías. Diferencia explícitamente *cobertura de conocimiento*, *monitorización funcional*, *decisión clínica respaldada* y *validación operacional*. VIGILE no es un producto médico NASA autorizado.

## 1. Ingesta obligatoria de la documentación

Primero inspecciona el repositorio y **todos los archivos** adjuntos, principalmente el ZIP `VIGILE_FINAL_BIOMEDICAL_KNOWLEDGE.zip` generado por el segundo Deep Research. Descomprímelo y lee al menos:

- `00_README/` y cualquier manifiesto de la entrega.
- `01_MASTER_SOURCES/master_source_registry.csv`.
- `02_PRIMARY_EVIDENCE_EXTRACTIONS/primary_evidence_extractions.csv`.
- `03_CONDITION_CATALOG/condition_catalog.csv`.
- `04_CLINICAL_PATHWAYS/clinical_pathways.md`.
- `05_COMPUTABLE_RULES/computable_rules.json`.
- `06_ALGORITHMS/algorithm_library.csv`.
- `07_SENSORS_BIOMARKERS/`, `08_MULTISYSTEM_RELATIONS/`, `09_DATASETS/`.
- `10_CLINICAL_COVERAGE/clinical_coverage_matrix.csv`.
- `11_EVIDENCE_GAPS/`.
- `12_CLINICAL_TEST_CASES/synthetic_test_cases.json`.
- `13_OFFLINE_RAG_LIBRARY/`.
- `14_CODEX_HANDOFF/VIGILE_BIOMEDICAL_IMPLEMENTATION_HANDOFF_FOR_CODEX.md`.
- `15_VALIDATION_AND_LIMITATIONS/VALIDATION_AND_LIMITATIONS.md`.

Lee también el primer paquete `VIGILE_Paquete_Revisado_Codex.zip` o sus archivos si están disponibles, solo como respaldo histórico. **El segundo Deep Research prevalece como catálogo de trabajo, pero sus datos tampoco son infalibles**: verifica sintaxis, unidades, vigencia, localizadores, contexto y conflictos de alta consecuencia. El informe declara 53 fuentes, 49 extracciones, 34 condiciones, 13 reglas, 11 algoritmos y 16 casos sintéticos: comprueba los conteos reales y la coherencia de los IDs, sin suponerlos.

Si el ZIP o algún archivo imprescindible no está realmente disponible, registra precisamente cuál falta y continúa con la infraestructura independiente de evidencia; no afirmes haber ingerido archivos ausentes. No repitas toda la búsqueda bibliográfica. Ante vacíos puntuales, identifica la pregunta científica exacta y deja el módulo en modo apropiado.

**Antes de codificar reglas clínicas**, produce un mapa automático: cada ConditionID ↔ RuleID ↔ SourceID/EvidenceID ↔ etapa clínica ↔ sensor/variable ↔ prueba ↔ estado de validación. Reporta referencias rotas, duplicados y contradicciones. Genera una matriz machine-readable para seguir el progreso.

## 2. Principios no negociables

1. **Motor determinístico:** las decisiones y verificaciones proceden de reglas versionadas y configuraciones trazables. LLM/RAG solo consulta y explica; no inventa hechos ni decisiones médicas.
2. **Separación tipada:** `data_quality`, `normative_compliance`, `research_finding`, `clinical_assessment`, `diagnosis`, `severity`, `authorization` y `action_status` son conceptos y campos independientes. Medición anómala ≠ incumplimiento normativo ≠ diagnóstico ≠ tratamiento autorizado.
3. **Evidencia exigible:** cada regla activa enlaza documento original, revisión/fecha, requisito/página/tabla/DOI si existe, tipo de evidencia, población, misión y contexto de gravedad. Conserva estatus de verificación.
4. **Sin medicina inventada:** no completes umbrales, dosificaciones, decisiones de triaje de alto impacto, diagnósticos definitivos, procedimientos invasivos, anticoagulación o terapias a partir de intuiciones. Lo no sustentado debe permanecer `INCONCLUSIVE`, `REQUIRES_VALIDATION`, `RESEARCH_ONLY`, `NOT_PUBLICLY_AVAILABLE` o `REQUIRES_MISSION_AUTHORIZATION` según corresponda.
5. **Manejo explícito de ausencias:** falta de mediciones, calidad, baseline comparable, licencia, protocolo o configuración de misión nunca se interpreta como normalidad.
6. **Contexto gravitatorio:** no reutilizar sin justificar protocolos *postlanding* como pruebas in-flight en microgravedad.
7. **Derechos y privacidad:** bibliotecas `development` y `operational` diferenciadas; solo contenido redistribuible/autorizado puede incluirse en una distribución RAG. Datos sintéticos por defecto, control local de acceso a datos personales y auditoría.
8. **No acciones peligrosas:** sin órdenes autónomas a sistemas de soporte vital, equipos médicos o tratamientos. Un protocolo autorizado solo se consulta/guía dentro de las competencias y configuraciones expresamente previstas, con confirmación humana para acciones de riesgo.
9. **Offline verificable:** no dependencia de servicios cloud o APIs externas en tiempo de ejecución; instalación reproducible con dependencias ya preparadas; no telemetría saliente oculta.
10. **Honestidad de la entrega:** no afirmar implementación, validación o pruebas no ejecutadas.

## 3. Arquitectura funcional, revisable a tu criterio

Preferir inicialmente **Python 3.12+, FastAPI, Pydantic, SQLite, pytest y JSON/YAML con esquemas**; puedes cambiar el stack con razones técnicas comprobables. Evita sobreingeniería. Aplica diseño modular y capas verificables:

- `AstronautProfile`, `MissionProfile` y `MissionContext`: preflight/inflight/postflight, gravedad, EVA, perfiles de exposición, recursos médicos disponibles, autorización y latencia de comunicaciones.
- `TypedObservationStore`: unidad, timestamp UTC, dispositivo/método, compartimento o sitio anatómico, fase, calidad, proveniencia, incertidumbre, datos faltantes.
- `DataQualityEngine` y conversiones tipadas de unidades, semántica temporal, duplicados y calibración.
- `PersonalBaselineEngine` y `LongitudinalTrendEngine`: comparabilidad, seguimiento, porcentajes, robust statistics y señales exploratorias no diagnósticas.
- `EvidenceRegistry`, `SourceVersionRegistry`, `RequirementsEngine` y `RuleEngine` declarativo con operadores restringidos; prohibido `eval` de expresiones arbitrarias.
- `ClinicalConditionRegistry`, `GuidedAssessmentEngine`, `DifferentialSupportEngine`, `TriageEscalationEngine` sujeto a reglas autorizadas.
- `ProtocolRegistry` y `AuthorizationEngine`: source, version, authority, applicability, resources, indications, contraindications, stop conditions, followup, authorizer; operaciones bloqueadas sin autorización.
- `ClinicalEpisode`, `PreventionPlan`, `CountermeasureTracker`, `RecoveryPlan`, `FollowUpEngine` y `AuditTrail` para el ciclo completo.
- `MultisystemInteractionEngine` que representa asociaciones con evidencia, confusores y causalidad limitada.
- API local versionada, integración de solo lectura para LLM/RAG, harness de simulaciones y fixtures.

Usa historial inmutable o mecanismo de auditoría que permita **reproducir exactamente** una decisión con inputs, reglas, versión y evidencia usados en ese momento. Evalúa SQLite WAL, índices de consultas temporales, backup y migraciones de esquema. No guardes datos reales de astronautas en el repositorio.

## 4. Cobertura integral, sin módulos ficticios

Usa **las 34 condiciones/riesgos del `condition_catalog.csv` como primera fuente de alcance**, expandibles donde la evidencia lo permita. Recorre TODAS las filas y columnas de `clinical_coverage_matrix.csv` y registra para cada una las etapas: prevención, monitorización, detección, evaluación, diagnóstico diferencial, triaje, intervención apoyada, recuperación, seguimiento, pronóstico.

Considera cardiovascular, muscular, óseo, SANS/oftalmológico, sueño/circadiano, cognitivo, conductual/psicológico, inmunológico/infeccioso, renal, neurológico/sensorimotor, nutrición/metabolismo, respiratorio, gastrointestinal, dermatológico, farmacológico, radiación, ambiente y emergencias. No asumas que todos tienen igual madurez. Para un dominio con evidencia incompleta, implementa la ingesta y el workflow respaldado, pero no simules tratamientos ausentes.

**Prioridad doble:** (a) construir infraestructura y modelos para la cobertura completa; (b) completar flujos end-to-end en tantos dominios como sea seguro y factible con la biblioteca. Muestra una métrica de cobertura basada en código probado y evidencia, no solo número de condiciones enumeradas. Cada área debe terminar con `IMPLEMENTED_TESTED`, `IMPLEMENTED_UNVALIDATED`, `STRUCTURED_ONLY`, `BLOCKED`, `NOT_IMPLEMENTED` o equivalentes explícitos.

## 5. Reglas concretas que deben verificarse e implementarse primero

Importa la semántica del JSON de Deep Research, valida referencias y considera al menos estas reglas reportadas:

- `R-AERO-MICRO-EVA`, `R-AERO-SURFACE-EVA`, `R-AERO-RETENTION`: NASA-STD-3001 V1 Rev C requisitos V1 4001–4003; VO₂max mínimo contextual de 32.9 o 36.5 mL/min/kg según EVA y retención ≥80 % frente a baseline comparable. No diagnosticar enfermedad por incumplimiento.
- `R-MUSCLE-RETENTION`: V1 4024, ≥80 % de fuerza preflight comparable por grupo muscular y método.
- `R-BONE-HIP-SPINE`, `R-BONE-FEMORAL-NECK`: V1 4027, BMD ≥95 % en cadera/columna y ≥90 % cuello femoral, con mismo sitio/técnica y limitaciones DXA/QCT; no calcular fractura individual con estas reglas.
- `R-RAD-CAREER`: V1 4030, límite acumulado de dosis efectiva de carrera por vuelo espacial `<600 mSv` conforme al modelo aplicable; mantener dosimetría de órganos, magnitudes y ventanas independientes. No mezclar mSv, mGy y mGy-Eq.
- `R-CO2-1H`: V2 6004, media temporal de 1 h de presión parcial de CO₂ ≤3 mmHg en volumen habitable aplicable, con política explícita de cobertura y calidad. Un punto instantáneo alto no equivale a incumplimiento horario.
- `R-CABIN-PRESSURE`: V2 6006, ventana contextual para presión de cabina en exposición indefinida, `34.5 kPa < P ≤103 kPa`; no trasladarla a traje espacial.
- `R-SANS-OCT`: del NASA SANS Evidence Report, cambio BMO-250 TRT >19.4 µm contra baseline como señal de aumento de vigilancia cuando sean comparables imagen/método/registro. No diagnóstico automático de SANS.
- `R-NUTRITION-PROVISION`: requisitos de provisión nutricional configurados, separando `provision` de `actual intake` y documentando método de cálculo de necesidades.
- `R-IMMUNE-TREND`: variaciones longitudinales solo como observación contextual/investigación; no diagnóstico inferido de un biomarcador aislado.
- `R-EVA-CLEARANCE`: **no** conceder autorizaciones de EVA automáticamente; proporcionar exclusivamente evaluación de requisitos y bloqueo/revisión humana según reglas autorizadas.

Además aplica requisitos ambientales V2 6002/6003/6020, monitorización de ppO₂, gases diluyentes, humedad, presión, temperatura y separación de compartimentos; y vigilancia de sueño/cognición, fuerza, BMD, farmacología/inventario, infecciones/renal y relaciones multisistema según los pathways de la biblioteca.

Confronta todas las cifras con `primary_evidence_extractions.csv` y las fuentes; no programes una cifra procedente únicamente de este prompt si discrepa con el original. Clasifica cada regla entre `NORMATIVE_CHECK`, `RESEARCH_SIGNAL`, `AUTHORIZED_CLINICAL_DECISION` y `OBSERVATIONAL_ANALYTIC`.

## 6. Motores y etapas clínicas

Para cada condición con información respaldada, enlaza funcionalmente:

`Prevention → Measurement/QC → Personal baseline → Detection → Guided assessment → Differential support → Human-authorized triage → Protocol retrieval → Intervention tracking → Recovery → Follow-up → Reassessment`.

Los pasos pueden ser `NOT_AVAILABLE` sin inventar medicina, pero nunca deben desaparecer del modelo. En cualquier evento genera una explicación estructurada con `what_changed`, `why_flagged`, `measurement_ids`, `rule_ids`, `source_ids`, `confidence_and_limits`, `authorized_next_step`, `follow_up_due` cuando esté documentado y permitido.

Estados independientes recomendados:

`data_quality: VALID | PARTIAL | INVALID | MISSING`;
`normative_compliance: MET | NOT_MET | NOT_APPLICABLE | INCONCLUSIVE`;
`clinical_assessment: NOT_ASSESSED | UNDER_REVIEW | INCONCLUSIVE | REVIEW_REQUIRED`;
`research_signal: NO_FLAG | FLAGGED | NOT_COMPUTABLE`;
`severity: UNDETERMINED | NORMAL | WATCH | CAUTION | CRITICAL` solo bajo reglas autorizadas;
`authorization: RESEARCH_ONLY | REQUIRES_VALIDATION | MISSION_AUTHORIZED`.

Implementa políticas explícitas para reglas simultáneas/conflictivas, prioridades, supervisión y stale data. Ninguna etiqueta de gravedad debe inferirse arbitrariamente de una norma de rendimiento.

## 7. Interfaz con el resto del equipo

Tu responsabilidad principal es **el backend Health Intelligence**, no sustituir el trabajo de quienes implementan el LLM/RAG, la optimización de hardware ni la interfaz final. Proporciona contratos OpenAPI, schemas, fixtures y un adaptador local de **solo lectura** para el equipo de IA y endpoints utilizables por el equipo full-stack. No acoples la lógica clínica a textos generados por LLM.

Separa modos `FULL`, `LOW_POWER`, `CRITICAL` con degradación responsable: bajo recursos, priorizar integridad de datos y verificaciones normativas críticas habilitadas; no presentar vigilancia desactivada como resultado `NORMAL`. Medir memoria, latencia y almacenamiento sin prometer consumos no medidos.

## 8. Casos de prueba y aceptación

Usa los 16 escenarios sintéticos del paquete, corrigiéndolos si están mal construidos, y añade pruebas positivas/negativas/de frontera para todos los flujos activos:

1. EVA microgravedad vs superficie, mismas medidas distintas configuraciones y retención del 80 %.
2. Fuerza muscular por grupo comparable, cambios de metodología, baseline ausente/0.
3. BMD por zona anatómica, modalidad distinta y seguimiento lento.
4. Dosimetría temporal por órgano y carrera, tipos de dosis incompatibles, valores de frontera.
5. CO₂ rolling time-weighted average 1 h, intervalos irregulares, falta de muestras, compartimentos distintos, duplicados.
6. Oxígeno, diluyente, presión, falla de cobertura atmosférica.
7. SANS OCT frente a baseline y técnica incorrecta, señal ≠ diagnóstico.
8. Sueño ↔ cognición, datos exploratorios, sin inferencia psiquiátrica.
9. Inmunología y enfermedad renal: ingestión/monitorización y rechazo de umbrales sin evidencia.
10. Prueba ortostática **preflight/postlanding**, nunca standing in-flight microgravity por defecto.
11. Red flags y emergencias simuladas, sin tratamiento sin autorización.
12. Multi-condición, calidad mala, missing data, conflicto de reglas, modo low-power y sin red.
13. Autorización de protocolos, controles de rol, integridad de bitácora, fuente obsoleta y derechos de documentos RAG.
14. API, migraciones, backups, schemas y reproducibilidad offline.

Ejecuta `pytest` y linters/type checkers disponibles; documenta comandos, versiones, métricas y fallos. Diferencia **tests software con datos sintéticos** de validación clínica humana/espacial. No inventes tasas de sensibilidad/especificidad.

## 9. Autonomía técnica e iteración

Tienes libertad para cambiar arquitectura, priorización, tecnologías, modelos, APIs, estructura y algoritmos cuando aporten calidad. Corrige errores en los documentos, pero conserva un log de discrepancias con evidencia primaria y nunca inventes reemplazos médicos. No solicites permiso por elecciones ordinarias de ingeniería. Haz commits o checkpoints claros si el entorno lo permite. **Trabaja progresivamente dentro de esta ejecución**, priorizando código real. Si no llegas a cubrir todas las condiciones, deja una implementación vertical sólida, interfaces funcionales y backlog detallado, sin asegurar completitud.

## 10. Entrega permanente y reporte al chat, obligatorios

Archivos de documentación, organizables sin redundancia:
- `README.md` (instalación, ejecución, offline)
- `ARCHITECTURE.md`
- `IMPLEMENTATION_STATUS.md`
- `CLINICAL_COVERAGE.md` y matriz CSV/JSON machine-readable
- `EVIDENCE_TRACEABILITY.md` y registros importados de fuentes/reglas
- `TECHNICAL_DECISIONS.md`
- `TEST_REPORT.md`
- `VALIDATION_AND_SAFETY.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `HANDOFF.md`

**En el último mensaje del chat de Codex**, entrega un reporte con: (1) resumen; (2) archivos/código real; (3) cobertura y etapas clínicas por dominio; (4) reglas y locators implementados; (5) cambios y decisiones; (6) pruebas con resultados reales; (7) brechas y bloqueos; (8) recursos/compatibilidad offline; (9) plan de integración con LLM/full-stack; (10) prioridades siguientes.

Cierra con el título literal:

## CONTEXTO PARA CONTINUAR CON CHATGPT

Incluye **resumen autosuficiente y concreto** del estado del proyecto, rutas del repositorio, artefactos, decisiones, cobertura, pruebas, limitaciones, diferencias frente al Deep Research, preguntas clínicas específicas pendientes y próximos pasos. Debe servir para copiar y pegar a ChatGPT sin que ChatGPT tenga acceso al repositorio ni a sesiones anteriores.

**Empieza ahora inspeccionando e inventariando los archivos aportados; después programa, prueba, documenta y presenta resultados verificables.**
