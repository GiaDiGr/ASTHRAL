# VIGILE — Rescate documental para Codex (paquete PARCIAL)

## Qué se ha recuperado realmente

1. `00_INFORME_DEEP_RESEARCH_2/INFORME_COMPLETO.md`: texto íntegro del informe final del **segundo** Deep Research recuperado de la Biblioteca; sus antiguos enlaces `sandbox:` eran inaccesibles y se marcaron como `ARCHIVO_ORIGINAL_NO_RECUPERADO`.
2. `01_ENLACES_ENCONTRADOS_EN_INVESTIGACION/links_reportados_por_herramienta.csv`: enlaces indexados en los metadatos originales de la investigación. **No** constituyen una auditoría individual de documentos y no implican validación médica.
3. `02_PAQUETE_ANTERIOR/`: ficheros reales del **primer** trabajo y auditoría primaria anterior, no del segundo.
4. `03_PROMPTS/`: prompt elaborado para Codex basado en el informe segundo. Contiene referencias a un ZIP original que **NO** se ha recuperado; leer este README antes.
5. `04_RESUMEN_RECONSTRUIDO/`: IDs de 13 reglas mencionadas en el informe, solo como índice de trabajo, no es `computable_rules.json` del Deep Research.

## Qué NO se pudo recuperar

El archivo generado en el entorno de Deep Research `VIGILE_FINAL_BIOMEDICAL_KNOWLEDGE.zip` **no existe en el entorno de archivos de esta conversación ni se encuentra como fichero accesible en la Biblioteca**. Por tanto NO es posible recuperar de allí los originales del segundo estudio, entre ellos:

- `01_MASTER_SOURCES/master_source_registry.csv` (53 filas reportadas),
- `02_PRIMARY_EVIDENCE_EXTRACTIONS/primary_evidence_extractions.csv` (49 hallazgos reportados),
- `03_CONDITION_CATALOG/condition_catalog.csv` (34 condiciones reportadas),
- `04_CLINICAL_PATHWAYS/clinical_pathways.md`,
- `05_COMPUTABLE_RULES/computable_rules.json` (13 reglas reportadas),
- `06_ALGORITHMS/algorithm_library.csv` (11 algoritmos reportados),
- `10_CLINICAL_COVERAGE/clinical_coverage_matrix.csv`,
- `12_CLINICAL_TEST_CASES/synthetic_test_cases.json` (16 casos reportados),
- el handoff estructurado original.

**NO CONFUNDIR ESTE ARCHIVO RECONSTRUIDO CON EL ZIP ORIGINAL.** Los conteos declarados en el informe no pueden verificarse contra ficheros ausentes.

## Instrucción sugerida a Codex

Inspecciona este ZIP y el repositorio actual. Usa el informe completo como guía e inventario de hipótesis de trabajo, y los archivos más antiguos como evidencia preliminar. No asumas que se dispone del JSON original de 13 reglas, matriz de 34 condiciones o 49 extracciones primarias. No inventes esos contenidos. Antes de activar cada regla, valida su fuente original, contexto, unidad, versión, reglas de autorización y casos de prueba; clasifica `REQUIRES_VALIDATION` cuando proceda. Avanza ahora con la infraestructura offline, data model, calidad de datos, provenance, motor de reglas versionadas, API, auditoría y pruebas; implementa checks normativos solo tras la verificación correspondiente. Documenta faltantes y finaliza tu reporte con `CONTEXTO PARA CONTINUAR CON CHATGPT`.

## Cómo obtener los faltantes del segundo Deep Research

En la conversación original de Deep Research, solicita **archivos adjuntos reales, no enlaces sandbox internos de otra sesión**. Pide entrega en múltiples adjuntos individuales si el ZIP falla, especialmente `computable_rules.json`, `condition_catalog.csv`, `primary_evidence_extractions.csv` y `VIGILE_BIOMEDICAL_IMPLEMENTATION_HANDOFF_FOR_CODEX.md`. Una vez descargados/adjuntados, podrán añadirse a este paquete sin rehacer la investigación.
