# VIGILE — Corrección de consistencia clínica, v0.6.1

## Resultado y causa raíz

El caso sintético informado satisface el árbol DKA existente. No se cambió ningún umbral, criterio, catálogo de enfermedades ni protocolo médico. El consenso utilizado es el mismo: [Hyperglycemic Crises in Adults With Diabetes, 2024](https://diabetesjournals.org/care/article/47/8/1257/156808/Hyperglycemic-Crises-in-Adults-With-Diabetes-A), DOI 10.2337/dci24-0032. La lógica permite las alternativas de diabetes/hiperglucemia, cetosis y acidosis representadas en el catálogo original.

La cadena del defecto era:

1. `clinical_logic.tree` calculaba correctamente el resultado AND/OR con true/false/null, pero no distinguía datos inválidos de datos desconocidos.
2. `clinical_engine.evaluate_condition` publicaba `missing_fields=fields(evaluated)`: todas las hojas null, incluso alternativas de OR ya satisfechas.
3. La API transmitía esa lista fielmente, sin la clasificación necesaria para interpretarla. No alteraba el resultado.
4. `local_assistant.evidence_blocks` la convertía en «datos faltantes». El filtro de contexto para preguntas sobre faltantes omitía el estado diagnóstico global y la estructura lógica.
5. El generador Ollama transformaba ese contexto ambiguo en un supuesto requisito diagnóstico. Su comprobación semántica no lo impedía. Era un defecto de representación y contexto anterior al LLM, amplificado por la generación.
6. El dashboard también mostraba «Faltantes» sin distinción. Además, la selección de pruebas omitía grupos con cualquier valor presente, aunque fuera negativo y otra alternativa siguiera desconocida.

## Contrato vigente

Cada resultado nuevo añade:

| Campo | Significado |
| --- | --- |
| `missing_required` | Candidatos ausentes en ramas que todavía pueden resolver el árbol. En una OR no son todos individualmente obligatorios: debe consultarse la estructura. |
| `optional_not_measured` | Hojas desconocidas no bloqueantes para el resultado lógico actual, por un ancestro determinado. No significa que carezcan de utilidad clínica para otros propósitos. |
| `invalid_required` | Hojas con datos inutilizables en ramas aún no resueltas. |
| `invalid_fields` | Todas las hojas inválidas, incluidas alternativas no bloqueantes. |
| `required_for_protocol_safety` | Datos de seguridad pendientes, independientes del diagnóstico. En el protocolo DKA implementado incluye potasio cuando no hay un valor utilizable. No es una lista universal de todas las necesidades terapéuticas. |
| `data_requirement_version` | `four-state-1`. |
| `missing_requirement_semantics` | Declara que los candidatos respetan AND/OR y no son todos obligatorios. |

`missing_fields` permanece como campo legado de hojas indeterminadas; está deprecado para mostrar requisitos. Sus consumidores deben migrar a los campos nuevos. Las listas usan conceptos; cuando existen varias muestras, la traza y sus identificadores distinguen cada evaluación. Los valores derivados mantienen sus dependencias en `metadata.derivation_inputs` cuando pueden calcularse; no se inventan baselines.

El árbol mantiene `state` booleano/null para compatibilidad y añade `truth_state` (`TRUE`, `FALSE`, `UNKNOWN`, `INVALID`), rutas de nodos, motivos de invalidez, ramas decisivas y `required_for_resolution`. Se recorren todas las ramas, sin eliminar las alternativas satisfechas, falsas, desconocidas o inválidas.

- AND: FALSE determina el resultado; sin FALSE, INVALID precede a UNKNOWN; todos TRUE producen TRUE.
- OR: TRUE determina el resultado; sin TRUE, INVALID precede a UNKNOWN; todos FALSE producen FALSE.
- Un error de calidad no se convierte en normalidad. Una alternativa válida puede resolver OR pese a otra inválida, cuyo error se conserva en la traza.
- UNKNOWN e INVALID no establecen criterios cumplidos por sí solos. CRITERIA_NOT_MET no excluye enfermedad.
- La confirmación ADA sigue siendo una regla específica de muestras/pruebas, no una OR simple; se conservan sus requisitos de repetición. Ahora se incluyen también sus rutas no medidas en la traza.

## Caso informado

```json
{
  "diagnostic_status": "CRITERIA_MET",
  "missing_required": [],
  "optional_not_measured": ["bicarbonate_mmol_l", "urine_ketones_plus"],
  "invalid_required": [],
  "required_for_protocol_safety": ["potassium_mmol_l"],
  "protocol_status": "BLOCKED_MISSING_DATA",
  "treatment_status": "NOT_STARTED"
}
```

El protocolo conserva `BLOCKED_MISSING_DATA:POTASSIUM`, los bloqueos de recursos y de autorización. Las pruebas de ese escenario sólo solicitan información de potasio para seguridad; no recomiendan bicarbonato ni cetonas urinarias para completar un criterio ya satisfecho. Si el pH no satisface la rama y falta bicarbonato, la alternativa vuelve a ser candidata y se recomienda el grupo de pruebas existente. No se añadieron pruebas ni nuevos umbrales.

## Asistente, RAG y portal

Las consultas identificadas sobre datos ausentes o alternativas no medidas devuelven `DETERMINISTIC_DATA_SUFFICIENCY`, con texto construido desde el motor y `inference_attempted=false`. En CRITICAL conservan el estado `EXTRACTIVE_ONLY`. Una consulta combinada de datos y pruebas también incluye las recomendaciones vigentes. Esto no simula una respuesta del LLM.

Otras consultas conservan Ollama y `vigile-qwen3-4b:latest`. El contexto incluye el estado global y una traza lógica compacta, además de la clasificación estructurada. Un filtro determinista rechaza menciones libres a determinadas alternativas no medidas y contradicciones explícitas de suficiencia. Se mantienen controles de citas y comprobación semántica. Son defensas conservadoras, no una garantía general contra alucinaciones o paráfrasis no contempladas. Ante rechazo queda la evidencia extractiva. No se cambió Norton ni se restauró llama-server.

Las evaluaciones históricas sin versión de requisitos muestran que su ausencia no está clasificada; no se reinterpretan silenciosamente ni se reescriben. Los documentos del RAG conservan su función documental y no pueden convertir un criterio satisfecho en uno pendiente.

## Archivos modificados

- `engine/vigile/clinical_logic.py`: cuatro estados, clasificación y traza completa.
- `engine/vigile/clinical_models.py`: contrato de requisitos.
- `engine/vigile/clinical_engine.py`: calidad, derivaciones, confirmación y seguridad separada.
- `engine/vigile/clinical_differential.py`: recomendaciones según ramas sin resolver y propósito diagnóstico/seguridad.
- `engine/vigile/local_assistant.py`: contexto, traza y resumen determinista.
- `engine/vigile/conversational.py`: instrucciones y rechazo determinista adicional.
- `engine/vigile/web/app.js`: presentación diferenciada de pendientes y estados inválidos.
- `engine/tests/test_clinical_consistency.py`: 63 regresiones nuevas.

## Resultados ejecutados

- Antes: **298 passed**, 1 advertencia, 37,65 s (`tests-consistency-before.xml`).
- Final: **361 passed**, 1 advertencia, 56,43 s (`tests-consistency.xml`). Se conserva la advertencia Starlette/httpx existente.
- Incluye los **30 escenarios científicos sintéticos existentes**, con expectativas previas sin modificar, y regresiones de DKA, OH, anafilaxia, AKI y diabetes.
- Matrices completas de AND/OR para las 16 combinaciones binarias de cuatro estados por operador; árboles anidados, datos negativos/desconocidos/inválidos, unidades incorrectas, tipos erróneos, no finitos y alternativa válida con otra inválida.
- Pruebas de integración con asistente simulado verifican que no se invoca el LLM para reinterpretar faltantes; prueban contexto global, evaluaciones históricas y rechazo de frases incorrectas incluso con citas válidas.
- Demostración HTTP sintética: **28 solicitudes**, reproducción correcta y reader sin escritura. Mediana 15,43 ms, máximo 62,34 ms en TestClient; estas mediciones no son latencia de producción.
- Integración TCP con Ollama real: **12 consultas**, cuatro en cada modo FULL/LOW_POWER/CRITICAL. Las seis preguntas sobre faltantes/alternativas devolvieron clasificación determinista; dos explicaciones del protocolo fueron generadas y aceptadas; dos explicaciones libres de criterios fueron rechazadas (`REJECTED_OR_FAILED`); las otras dos consultas CRITICAL fueron extractivas. No se presentan los rechazos como éxitos de generación. El endpoint no distingue todavía todos los motivos internos de rechazo/fallo en su respuesta pública.
- Reproducción exacta de cuatro evaluaciones, cadena de auditoría válida, hash de registros idéntico antes/después del asistente, escritura reader y acceso fuera de ámbito rechazados; Origin externo y modo inválido rechazados.
- **106 documentos originales y 9 archivos de conocimiento clínico sin cambios de bytes**.

Resultados detallados: `consistency-live-verification.json`, `consistency-demo.json`, `openapi-consistency.json`. La primera consulta determinista tardó 10,215 s incluyendo lecturas/estado; las siguientes, 169–246 ms. Explicaciones aceptadas: 8,723 s y 10,611 s. No se atribuye inferencia a las consultas deterministas ni se extrapolan percentiles.

## Reproducción y conservación

Se archivó el código anterior en `docs/ai/v06-before-consistency.zip`. La base anterior `engine/data/portal-v06-final` permanece conservada. La nueva base sintética está en `engine/data/portal-consistency-v061`; tiene los hashes de la implementación corregida. No se sobrescribieron hashes para hacer pasar un replay antiguo: usar otra implementación produce `REPLAY_VERSION_MISMATCH`, según el diseño existente.

Arranque desde PowerShell, si esos servicios no están ya ejecutándose:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe .\tools\start_ollama_vigile.py
```

En otra terminal:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir .\data\portal-consistency-v061 --port 8895
```

En otra terminal:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile.portal --config .\data\portal-consistency-v061\portal-config.json --port 8896
```

Abrir http://127.0.0.1:8896/ con el mismo código local del portal. Elegir DKA inicial y consultar «¿Qué datos faltan?». La UI muestra la clasificación directamente. Las credenciales reader nunca deben copiarse al navegador.

Verificación:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe ..\docs\ai\verify-consistency-live.py
```

La última orden necesita los tres servicios; usa sólo la demostración sintética y vuelve a dejar el portal en FULL. Los registros no cambian, pero se actualiza el informe de mediciones. Para otra demo aislada, usar `python -m vigile.portal_demo --output <carpeta-nueva>` con el Python del venv y configurar manualmente puertos/proveedor según el contrato, sin sobrescribir la demostración existente.

## Límites y próximos trabajos

No hay validación clínica ni espacial por aprobar pruebas sintéticas. Se conserva la ausencia de ejecución terapéutica y autorización de misión. SQLite no está cifrado; su auditoría no resiste a un atacante con control total del almacenamiento y capacidad de recalcularla. Ollama permanece sólo en loopback, sin autenticación propia de su API; hace falta aislamiento de procesos. Ninguna protección antivirus se modificó.

Prioridades: revisión biomédica independiente de la semántica y traducciones; ampliar pruebas adversariales de paráfrasis y consultas multilingües; mejores códigos auditables de rechazo del asistente; contratos formales de respuesta OpenAPI para los campos anidados (actualmente respuestas dinámicas); mapear candidatos derivados a solicitudes de adquisición por muestra; aislamiento y protección del almacenamiento. No ampliar enfermedades hasta completar esas verificaciones.

## CONTEXTO PARA CONTINUAR CON CHATGPT

Corrección v0.6.1 en el proyecto existente; Ollama v0.40.6 y `vigile-qwen3-4b:latest` intactos en 127.0.0.1:8891. Backend 8895 y portal 8896 usan `portal-consistency-v061`. Código anterior y base anterior preservados. Conocimiento clínico sin cambios: hash `cb0dc5bba91e4861f2395d5cf9514e6a75de95709feb105fb6866041812c44ae`. Migrar consumidores de `missing_fields` a las categorías nuevas y conservar AND/OR; no interpretar `missing_required` como una lista conjuntiva. El LLM no tiene autoridad para reinterpretar la suficiencia ni autorizar intervenciones. Suite final 361 aprobadas; 12 consultas reales registradas con sus dos rechazos explícitos. Los comandos anteriores permiten continuar la demostración sin tocar Norton ni la cuarentena.
