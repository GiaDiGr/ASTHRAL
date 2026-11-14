# VIGILE — Auditoría de Biomedical / Health Intelligence

Identificador: `BIOMED-AUDIT-2026-10-20`. Base: v0.6.1 y `docs/ai/CONSISTENCY_AUDIT.md`. Alcance: las seis rutas existentes, diferencial, calidad, baselines, contratos y reproducción. No es una validación clínica independiente ni una autorización de uso asistencial o espacial.

## Dictamen técnico

El núcleo es integrable para investigación y demostraciones sintéticas bajo los contratos adjuntos. No está validado para tomar decisiones clínicas reales. Las rutas tienen cobertura computacional parcial: algunas entradas son juicios o declaraciones de un operador, no resultados inferidos de sensores. La urgencia y el orden diferencial son políticas de investigación pendientes de revisión sanitaria.

Se conservan frontend, RAG, asistente, Ollama y el modelo `vigile-qwen3-4b:latest`. No se han desarrollado funciones nuevas en ellos. No se modificaron Norton ni autorizaciones terapéuticas. Los 15 comparadores normativos de simulación no se convierten en diagnósticos.

## Errores corregidos

| Hallazgo | Corrección y alcance |
|---|---|
| Orden lexicográfico de timestamps con husos diferentes | Historial ordenado por instantes conscientes de zona; derivaciones usan la medición cronológicamente correcta. |
| Una entrada reciente inválida, desconocida o no medida dejaba reaparecer un valor previo | Se bloquea el reemplazo silencioso. Se conserva el motivo y las alternativas válidas siguen pudiendo resolver OR. UNKNOWN/NOT_MEASURED siguen siendo ausencia, no normalidad. |
| Un solo camino negativo de DM cerraba el árbol pese a alternativas desconocidas | La raíz permanece indeterminada mientras no se resuelvan las alternativas; no implica que todas deban medirse. |
| Contexto de ayuno invalidado en una muestra histórica podía reutilizarse si otra muestra tenía contexto válido | Selección y conflictos por muestra, registro de identificadores contextuales y bloqueo de la confirmación sin evidencia utilizable. |
| Valores contradictorios en una muestra histórica podían contar para confirmar DM | La rama de esa muestra queda INVALID. |
| Glucosa aleatoria de una colección y síntomas de otra se combinaban | Se exige vinculación explícita mediante `sample_id` para esa vía; no se inventa una duración temporal. |
| Confirmación ADA sin prueba explícita de las colecciones utilizadas | Raíz `ADA_CONFIRMATION`, política y lista `confirmation_evidence`; no se reduce a una OR de comparaciones. |
| Baseline de presión posterior a la medición erguida | No se deriva una caída con cronología invertida. |
| Caída porcentual WAO calculada desde presión ortostática | Usa `baseline_sbp_mm_hg` y `adult_sbp_mm_hg`. La presión erguida queda reservada a OH. Véase migración. |
| Creatinina ≥4 aislada elevaba a estadio 3 un caso detectado por diuresis | Esa alternativa exige también cambio agudo de creatinina respaldado por datos, conforme al razonamiento KDIGO 2.1. Se conserva el umbral de tabla; no se imputa baseline. |
| Bindings clínicos omitían caducidad del dispositivo | Comprueban `max_age_seconds` a `as_of`. Única excepción histórica explícita: baseline renal, que mantiene sus controles de calibración y ventana renal. |
| Derivaciones enumeraban todo el historial como entradas usadas | La traza identifica las observaciones seleccionadas en el instante más reciente para cada dependencia. |
| Replay verificaba recomputación pero no la salida persistida | Se contrasta también el hash de la salida almacenada; una discrepancia genera `REPLAY_STORED_OUTPUT_HASH_MISMATCH`. |
| Solicitudes con condición y presentación simultáneas | Rechazo `AMBIGUOUS_ROUTE` en lugar de enrutamiento ambiguo. |
| Respuestas clínicas sin esquemas de transporte | Modelos Pydantic recursivos y contratos OpenAPI; lectura compatible de registros históricos sin fabricar clasificaciones ausentes. |

No se han cambiado los números ni operadores de los JSON científicos. Las correcciones de interpretación están en código y quedan identificadas por `implementation_hash`; `criterion_version` sigue refiriendo el documento original.

## Verificación realizada

- Referencia anterior: **361 passed**, 42,99 s; `../ai/tests-biomedical-before.xml`.
- Primera suite ampliada: **456 passed**, 111,94 s. Después se añadieron las correcciones de contexto entre rutas y muestras y se repitió la suite completa.
- Resultado definitivo: **460 passed, 0 failures, 0 errors, 0 skipped**, 67,65 s reportados por pytest; `tests-final.xml` y `test-summary.json` conservan el resultado real (tiempo JUnit: 67,592 s).
- **99 casos nuevos**: `engine/tests/test_biomedical_audit.py`, incluidos 64 estados de árbol anidado, zonas horarias, límites, contradicciones históricas, contextos, sensores caducados, protocolos independientes, coexistencia DKA/anafilaxia, contratos y replay.
- Los **30 casos originales** se ejecutaron y contrastaron con EXPECTED de la reconciliación previa, no con expectativas generadas a partir de la implementación. Solicitudes, expectativas, resultados y replay: `cases-30-reviewed.json`.
- La primera ejecución del nuevo test HTTP tuvo un fallo del propio test por invertir los argumentos de `create_app`; se corrigió. No se presenta ese fallo como defecto clínico.
- Se conserva una advertencia de deprecación Starlette/httpx; no se cambiaron dependencias durante esta auditoría.
- Preservación comprobada de **106 documentos originales y 9 archivos de conocimiento clínico**; `preservation.json`. Copia previa de código y pruebas: `v061-before-audit.zip`.

La demo ASGI ejecuta adquisición, evaluación, consultas reader, seguridad de potasio, reevaluación, auditoría y replay. Su informe está en `engine/data/portal-biomedical-audit-final/demo-report.json`. Las métricas son de una demostración local sintética, no de desempeño clínico ni de vuelo.

Comprobación HTTP final: backend y portal 200; cuatro evaluaciones consultadas y reproducidas con reader; escritura y acceso fuera del ámbito rechazados; auditoría válida y registros sin modificación. El asistente respondió la pregunta de faltantes mediante la política determinista existente, sin invocar inferencia. Se verificó la presencia del modelo en Ollama y la conservación de su configuración; esta comprobación no es un ensayo nuevo de inferencia generativa. Detalles en `live-checks.json`.

## Archivos y contratos

Módulos modificados: `clinical_engine.py`, `clinical_models.py`, `clinical_api.py`. Nuevo: `clinical_contracts.py`. Pruebas: `test_biomedical_audit.py`. Rutas, fuentes y catálogo originales preservados. Los hashes completos figuran en `change-manifest.json`.

`openapi.json` formaliza evaluaciones, diferencial, pruebas, protocolos y replay. La aplicación mantiene desactivada la publicación pública de Swagger/OpenAPI: el archivo está disponible para integración local. Los documentos de evidencia de las rutas de consulta siguen siendo documentos versionados, no órdenes ejecutables.

El rótulo histórico de versión de paquete/API continúa siendo 0.6.0; **no identifica este parche**. Para esta entrega usar el identificador de auditoría, `implementation_hash`, `knowledge_hash` y manifiesto. No usar sólo ese rótulo para reproducir registros.

## Límites y riesgos abiertos

1. No hay validación clínica independiente, sensibilidad/especificidad medidas con datos clínicos ni validación de vuelo. CRITERIA_MET representa cumplimiento de una representación restringida; no equivale a diagnóstico médico autorizado. CRITERIA_NOT_MET no excluye enfermedad.
2. La vigencia de observaciones manuales depende de la ventana declarada; no existe una política clínica validada de caducidad y contemporaneidad por variable/ruta. No deben mezclarse episodios agudos distintos. Un `sample_id` es una declaración de asociación, no prueba física de simultaneidad.
3. Supino previo, técnica de prueba ortostática, carácter sostenido, gravedad clínica de síntomas y exclusión de causas de taquicardia requieren comprobación profesional. Las banderas no sustituyen ese juicio. POTS 12–19 años no está implementado; gravedad parcial no validada y prueba erguida en microgravedad no aplicable.
4. El estadio renal es mínimo respaldado por el snapshot; no reconstruye el máximo de un episodio completo. No se infiere creatinina basal ni se implementa eGFR pediátrico. Anuria/RRT y estadificación longitudinal necesitan revisión adicional. `resolution_status` de DKA es un cálculo bioquímico, no prueba de recuperación o alta; su árbol puede recomputarse del snapshot, pero no se expone como árbol separado.
5. El diferencial no ofrece probabilidades y tiene ramas externas sin criterios implementados. La lista de pruebas no es un protocolo exhaustivo: el mapeo de pruebas a condiciones contextuales es parcial. El catálogo de 44 condiciones no implica 44 detectores clínicos.
6. Confirmación, urgencia y protocolos son estados separados. Toda autorización terapéutica sigue bloqueada y `treatment_status=NOT_STARTED`. Las notas, recuperación y seguimiento registran trabajo humano; no constituyen tratamientos ejecutados ni resultados clínicos demostrados. No existe un registro clínico completo de administración de medicamentos en estas rutas.
7. SQLite carece de cifrado. Un atacante con control del almacenamiento puede alterar código, registros y rehacer hashes/auditoría. Falta anclaje externo firmado, identidad clínica certificada, aislamiento de procesos y gestión operacional de secretos. El reader no recibe credenciales de escritura ni endpoints para cambiar reglas.
8. Fuentes fijadas a la fecha del informe: VERIFIED no significa vigilancia continua. Se recuperó texto completo de KDIGO y WAO; para cinco fuentes se contrastaron pasajes indexados del original, pero la recuperación íntegra falló. Debe completarse esa revisión documental antes de aprobación clínica. Ver `SOURCE_REVIEW.md`.

## Preparación del resto del equipo

Frontend y RAG deben leer los estados y la traza; no deducir requisitos de `missing_fields`, no tratar UNKNOWN como FALSE, no convertir urgencia en confirmación ni interpretar una alternativa ausente como obligatoria. Consultar `CONTRACTS.md`. Optimización debe conservar el snapshot, hashes, precisión decimal de límites y orden temporal; cualquier cambio de implementación exige nuevos ensayos de equivalencia y replay versionado. No se ha ampliado ese módulo.

## CONTEXTO PARA CONTINUAR CON CHATGPT

El código auditado es una corrección incremental de v0.6.1, no una reconstrucción. Conocimiento clínico intacto, seis rutas y diferencial existentes; ejecución terapéutica bloqueada. Nuevo contrato recursivo y regresiones de tiempo, contexto, límites y reproducción. Usar `change-manifest.json` para la identidad exacta. Código anterior archivado; base anterior conservada. La demo activa usa `engine/data/portal-biomedical-audit-final`, backend 8895 y portal 8896; Ollama permanece en su configuración previa. Abrir primero `COVERAGE.md`, `SOURCE_REVIEW.md`, `CLINICIAN_REVIEW.md`, `test-summary.json` y `live-checks.json`.

Para verificar sin modificar la demo activa (PowerShell):

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile clinical-demo --output .\data\clinical-review-new-run
```

La carpeta `clinical-review-new-run` debe ser nueva. Para iniciar los servicios auditados si no están ya ejecutándose, usar dos terminales:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir .\data\portal-biomedical-audit-final --port 8895
```

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile.portal --config .\data\portal-biomedical-audit-final\portal-config.json --port 8896
```

No reiniciar ni reconfigurar Ollama para esta auditoría. No compartir `server-tokens.json`, archivos de tokens o código de acceso. Integración reader: bearer leído de un archivo protegido; rutas `/clinical/evaluations/{id}`, `/differential`, `/next-tests`, `/replay`, `/clinical/knowledge/version`. Los IDs se obtienen del dashboard autorizado o de las respuestas del escritor de pruebas. Una reproducción de registros de v0.6.1 requiere su implementación archivada; el motor nuevo rechaza deliberadamente versiones distintas.
