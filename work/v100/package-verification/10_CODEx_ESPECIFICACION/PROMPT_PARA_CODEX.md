# VIGILE — PROMPT DE EJECUCIÓN PARA CODEX

Actúa como ingeniero principal de software biomédico científico para implementar **VIGILE Health Intelligence Engine**, un sistema local, offline, determinista, trazable, extensible, con IA conversacional separada. Trabaja **sobre el contenido real de este ZIP**, no sobre supuestos de un ZIP anterior faltante.

## Paso 0 — auditoría antes de escribir reglas

Lee por completo `LEEME_PRIMERO.md`, `01_INFORMES/REPORTE_CONSOLIDADO_COMPLETO.md`, `01_INFORMES/15_REGLAS_ENTREGA_ORIGINAL_COMPLETA.md`, `02_REGLAS_ORIGINALES_15/REGLAS_15_ORIGINALES.json`, `03_CATALOGO/condiciones_con_rutas_y_cobertura.json`, `03_CATALOGO/matriz_cobertura_44x11.csv` y `07_EVIDENCIAS/extracciones.json`.

El conjunto **15 reglas originales** procede del JSON publicado en el Deep Research Parte 1 y fue recuperado literalmente. El informe consolidado posterior lista **10 reglas reconstruidas**, con nomenclatura diferente. No supongas que 15+10=25 reglas independientes, ni que 10 reemplaza 15. Compara requisitos NASA, ámbito, revisión, semántica, unidades, ventanas temporales, datos y seguridad. Anota decisiones en `docs/RULE_RECONCILIATION.md`; cualquier regla no resuelta queda deshabilitada/REQUIRES_VALIDATION. `posibles_correspondencias_sin_validar.csv` solo ofrece sugerencias para auditar.

La investigación no equivale a autorización de la NASA ni a validación clínica. Verifica fuentes y revisión antes de activar thresholds y deja registro explícito de toda incertidumbre normativa (en especial NASA-STD-3001 V2 Rev F y sus localizadores).

## Objetivo de esta ejecución

Implementa en este repositorio una **primera versión funcional y probada** del motor biomédico determinista, sin front-end completo y sin integrar aún un LLM real. Produce código modular Python 3.11+, FastAPI, Pydantic 2, SQLite (SQLAlchemy si es útil) y pytest. Usa librerías de código abierto con licencias compatibles, sin depender de servicios de red durante la ejecución. Ejecuta localmente pruebas; no afirmes que pasaron si no se ejecutaron.

## Modelo funcional

1. EvidenceSource / EvidenceExtraction / SourceRevision (proveniencia, secciones, límites, status).
2. ConditionCatalog con 44 condiciones y sus 11 etapas clínicas, conservando la matriz exacta de estados y `source_ids`. La ruta clínica publicada es perfil abreviado: NO la conviertas en prescripción.
3. MissionContext / AstronautProfile / DeviceRegistry / Typed Measurement.
4. Calidad de datos, missingness, caducidad/calibración, conflictos multisensor, conversión dimensional segura, timestamps y contextos.
5. Baselines personales (comparabilidad y suficiencia por protocolo configurable), retención %, promedios temporales con cobertura comprobable, tendencias longitudinales y modo `RESEARCH_ONLY` para estadística no validada.
6. RuleEngine de estados determinísticos con applicability checks y evidencia por regla; no ejecutar comparaciones con datos ausentes o incompatibles.
7. Findings separados por tipo (cumplimiento de norma, anomalía estadística, hallazgo, hipótesis); nunca producir diagnóstico por incumplimiento normativo.
8. 12 relaciones multisistema, sin inferir causalidad; episodios clínicos y rutas parametrizadas.
9. Motor de autorización de solo servidor y máquina de estados de episodios; toda intervención sin protocolo autorizado debe bloquearse y auditarse.
10. SQLite local y API FastAPI con endpoints de lectura para futura interfaz y RAG. El modelo local NO tiene permisos de escritura sobre reglas/autorizaciones/auditorías.
11. Importadores para fuentes, condiciones, reglas, algoritmos, sensores, datasets y pruebas sintéticas; detecta inconsistencias en lugar de silenciarlas.

## Medición y regla clínica

Mantén explícitamente:
`RAW_MEASUREMENT -> QUALITY_CHECK -> DERIVED_METRIC -> NORMATIVE_COMPLIANCE / STATISTICAL_FINDING -> HUMAN_ASSESSMENT -> AUTHORIZED_PATHWAY -> FOLLOW_UP`.

No implementes `REQUIREMENT_NOT_MET -> DIAGNOSIS` ni dosificación/prescripción automática. La activación de una regla normativa requiere evidencia suficiente y contexto/método/unidad correctos; todas las decisiones deben versionarse.

## Pruebas mínimas obligatorias

Convierte `09_TESTS/casos_sinteticos.json` a tests reproducibles. Añade pruebas unitarias para inclusión/exclusión de límites, promedios CO2 con huecos, límites estrictos, dosis mSv frente a mGy, tasas frente a dosis acumuladas, mismatch entre regiones DXA y protocolos, EVA microgravity vs EVA surface, baseline ausente, falsos positivos evitados, autorización bloqueada, ataque de LLM para cambiar reglas, auditoría y reproducibilidad. No hardcodear `VALID` sobre datos incompletos ni asumir frecuencia de muestreo NASA desconocida.

## Entregables de código

- Repo ejecutable, README e instalación offline, `pyproject.toml`, `requirements` o lockfile.
- Código modular, modelos tipados, scripts de carga, esquema SQL/migraciones, API local, simulador sintético sencillo, suite pytest.
- `docs/RULE_RECONCILIATION.md`, `docs/EVIDENCE_TRACEABILITY.md`, `docs/CLINICAL_COVERAGE.md`, `docs/VALIDATION_STATUS.md`, `docs/LIMITATIONS.md`.
- `docs/INTEGRATION_CONTRACTS.md` para la persona de LLM/RAG, optimización y full stack; responsabilidades y payloads.
- Lista de funciones implementadas y deshabilitadas explícitamente; sin engañar sobre cobertura validada.

## Forma de trabajar

Audita primero el ZIP y diseña la implementación completa, pero **escribe código real en esta ejecución** empezando por foundation + safety + normative engine. Si no puedes acabar todo por límites prácticos, prioriza arquitectura ejecutable y pruebas por encima de simulaciones visuales y documentación duplicada. Mantén interfaces extensibles para los demás módulos. No sustituyas entregables con promesas, ni modifiques artificialmente datos científicos para que pasen los tests.

Al final informa qué archivos creaste, qué tests ejecutaste y pasaron, qué reglas quedaron habilitadas/deshabilitadas, qué conflictos entre investigaciones existen y qué necesita revisión externa. Termina tu respuesta exactamente con la sección `## CONTEXTO PARA CONTINUAR CON CHATGPT`, incluyendo estado del repo, rutas, decisiones, bloqueos y próximos pasos verificables.
