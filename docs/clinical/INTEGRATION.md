# Integración clínica VIGILE v0.4

El proyecto sigue en `C:\Users\Gianni\Desktop\Vigile`. Runtime offline, Python/FastAPI/Pydantic/SQLite existentes. No se añade frontend ni LLM. El esquema SQLite sigue en versión 1; las evaluaciones usan el nuevo tipo append-only `clinical_evaluation` de la tabla records existente.

## Ejecutar y verificar

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile clinical-demo
```

La demo crea una carpeta temporal nueva y muestra su ruta. Para elegirla, usar una ruta que aún no exista:

```powershell
& .\.venv\Scripts\python.exe -m vigile clinical-demo --output data\mi-demo-clinica
```

Genera una BD aislada, informe de rendimiento, transcripción HTTP sintética y tres solicitudes JSON reutilizables. La demo realiza peticiones HTTP ASGI contra la aplicación FastAPI real mediante TestClient, sin abrir un puerto. No mide latencia de red ni demuestra operación espacial. Las credenciales temporales no se escriben en sus archivos. Su entrada es reproducible; IDs de evaluaciones y marcas de auditoría varían. Los hashes de entradas y salidas permiten comparar significado sin fingir identidad binaria de las BD.

Para el servidor TCP local habitual:

```powershell
& .\.venv\Scripts\python.exe -m vigile init
& .\.venv\Scripts\python.exe -m vigile serve --port 8765
```

`init` reutiliza configuración provisionada y no reemite los tokens ya migrados a hashes. No compartir `data\client-credentials.json` con el LLM. El administrador debe asignar a cada token reader los subject_ids/mission_ids apropiados en la configuración de servidor; el reader inicial vacío puede consultar conocimiento pero no evaluaciones personales. No existe API para elevar su rol.

Dependencias del entorno instalado: Python 3.13, FastAPI/Pydantic/Uvicorn, pytest y HTTPX para pruebas/demo; no se añadió ninguna dependencia. En instalación limpia offline, con Python compatible con los wheels disponibles:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements.lock
```

Ejecutar desde `engine` permite importar el paquete sin instalación editable. pyproject incorpora los JSON como package-data; el corpus histórico sigue requiriendo la raíz VIGILE existente.

## Endpoints

Todas las rutas requieren Bearer, salvo /health. POST clínicos: researcher o clinician y scope autorizado. Operador puede adquirir mediciones por la API existente pero no evaluar la capa clínica. GET de conocimiento: cualquier identidad válida. GET de resultados: reader con scope exacto o rol autorizado.

| Método | Ruta | Contrato |
|---|---|---|
| POST | /clinical/evaluations | ClinicalRequest, seis condition_id soportados |
| POST | /clinical/presentations/evaluate | ClinicalRequest con presentation_id, sin condition_id |
| GET | /clinical/evaluations/{id} | Proyección sin snapshot ni identidad del sujeto |
| GET | /clinical/evaluations/{id}/differential | Hipótesis ordinales, soporte, contradicciones, fuentes |
| GET | /clinical/evaluations/{id}/next-tests | Pruebas o acciones pendientes; test_id puede ser null si no existe en catálogo |
| GET | /clinical/evaluations/{id}/replay | matches y hashes; falla si cambió código/conocimiento |
| POST | /clinical/evaluations/{id}/reassess | Nuevo snapshot completo; ID nuevo, parent_id inmutable |
| GET | /clinical/conditions/{condition_id} | Criterio o EXTERNAL_PATHWAY_NOT_IMPLEMENTED |
| GET | /clinical/conditions/{condition_id}/criteria | Documento del criterio original |
| GET | /clinical/criteria/{criterion_id} | Criterio por ID |
| GET | /clinical/protocols/{protocol_id} | Documento, execution_enabled=false |
| POST | /clinical/protocols/{protocol_id}/eligibility | {evaluation_id}; consulta elegibilidad ya evaluada, no autoriza |
| GET | /clinical/sources/{source_id} | Fuente y estado de vigencia fijado |
| GET | /clinical/knowledge/version | Manifiesto, hashes, runtime offline |

OpenAPI real exportado a `docs/clinical/openapi-v04.json`; también GET /openapi.json autenticado. Versiones previas de documentación no se sobrescribieron.

## Ejemplo mínimo por API

En otra consola, `$env:VIGILE_RESEARCH_TOKEN` debe contener una credencial researcher legítima, mantenida fuera de archivos del LLM. Crear sujeto/misión de ejemplo una sola vez en una BD de prueba:

```powershell
$vigileHeaders = @{ Authorization = "Bearer $env:VIGILE_RESEARCH_TOKEN" }
$vigileBase = 'http://127.0.0.1:8765'
Invoke-RestMethod -Method Post -Uri "$vigileBase/missions" -Headers $vigileHeaders -ContentType 'application/json' -Body '{"id":"clinical-earth","phase":"PRE_MISSION","gravity":"EARTH","environment":"HABITABLE_VOLUME","mode":"NOMINAL","synthetic":true}'
Invoke-RestMethod -Method Post -Uri "$vigileBase/profiles" -Headers $vigileHeaders -ContentType 'application/json' -Body '{"id":"clinical-crew","mission_id":"clinical-earth","synthetic":true}'
```

Utilizar `request-anaphylaxis.json` o `request-dizziness.json` generados por la demo, sustituyendo la ruta de ejemplo por la ruta que imprimió:

```powershell
$vigileRequest = Get-Content -LiteralPath 'RUTA_DE_DEMO\request-anaphylaxis.json' -Raw
$vigileEvaluation = Invoke-RestMethod -Method Post -Uri "$vigileBase/clinical/evaluations" -Headers $vigileHeaders -ContentType 'application/json' -Body $vigileRequest
$vigileReaderHeaders = @{ Authorization = "Bearer $env:VIGILE_READER_TOKEN" }
Invoke-RestMethod -Uri "$vigileBase/clinical/evaluations/$($vigileEvaluation.id)" -Headers $vigileReaderHeaders
Invoke-RestMethod -Uri "$vigileBase/clinical/evaluations/$($vigileEvaluation.id)/replay" -Headers $vigileReaderHeaders
```

El ejemplo DKA usa referencias a mediciones: primero importar los POST /devices y /measurements de la transcripción de la demo; no basta con copiar sus IDs a otra BD. Las filas ya existentes generan conflicto 409, nunca se sobreescriben automáticamente. El archivo `demo-final/synthetic-http-transcript.json` contiene solicitudes/respuestas reales completas y sin tokens. Una salida resumida de anafilaxia muestra CRITERIA_MET, EMERGENCY, NOT_REQUIRED, BLOCKED_RESOURCE y NOT_STARTED; block_reasons incluye también BLOCKED_AUTHORIZATION.

## Contratos de los integrantes

**Frontend:** conservar por separado diagnostic_status, urgency, confirmation_status, protocol_status, treatment_status. CRITERIA_MET significa criterio computable sustentado, no diagnóstico firmado. La urgencia agregada no desaparece cuando un protocolo está bloqueado. Mostrar missing_fields, data_issues, fuentes, limitaciones espaciales y todos los motivos de bloqueo. No presentar UNKNOWN como verde/normal. Diferenciales externos permanecen no implementados. metadata.aki_stage=null no significa etapa cero. Las recomendaciones con test_id=null son acciones pendientes de catálogo, no órdenes ejecutables. Usar parent_id para historial; no sobrescribir tarjetas históricas.

**RAG/LLM:** token propio reader con sujetos/misiones explícitos, proceso separado, sin montaje de SQLite, archivos de tokens ni credenciales researcher/operator. Leer evaluaciones, diferenciales, pruebas, fuentes y criterios; explicar decisiones existentes. POST/PATCH/PUT/DELETE están prohibidos al reader. La explicación generada no sustituye el árbol ni crea hallazgos, diagnósticos o autorizaciones. El servidor no entrega snapshots por estas rutas.

**Sensores/simuladores:** reutilizar /devices y /measurements. Cada binding declara measurement_id, concept y sample_id. La variable debe coincidir con el concepto; única adaptación especial: muestra serum_creatinine_mg_dl previa puede vincularse como baseline_creatinine_mg_dl. Se verifican sujeto/misión, dispositivo, calibración, rango, calidad y conflictos antes de criterios. Campos clínicos cualitativos van en observations con valor estricto, unidad 1, timestamp aware, método, muestra y procedencia. Los inválidos se conservan en el snapshot y data_issues; no dan soporte positivo. No presuponer disponibilidad de los dispositivos documentados.

**Optimizador:** medir fuera del motor y no alterar lógica, orden de prioridades, calidad ni umbrales. La demo informa mediana/máximo de latencia ASGI, pico de asignaciones Python y bytes SQLite. No equivale a RSS/CPU de vuelo. Ante falta de recursos, no inferir evidencia ni retirar auditoría para seguir emitiendo resultados; conservar salida bloqueada o fallo explícito. No hay garantía de evaluación si el disco/SQLite falla: la transacción falla y no se devuelve éxito persistido.

**Responsable biomédico:** revisar DECISIONS.md y las 30 reconciliaciones antes de cambiar conocimiento; validar simultaneidad, calidad, priorización, fuentes y población. Cambios de reglas o criterios se despliegan como nueva versión, nunca desde el LLM. Autoridad terapéutica futura necesita política de misión verificable e independiente y revisión específica; esta entrega no la implementa.
