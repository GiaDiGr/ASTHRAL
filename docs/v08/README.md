# VIGILE v0.8.0 — ejecución e integración

Lea primero [A. Auditoría biomédica](A_BIOMEDICAL_AUDIT.md), [B. Local AI](B_LOCAL_AI_KNOWLEDGE.md) y [resultados finales](RESULTS.md). La documentación v0.7 conserva los contratos de adquisición y monitorización. El cambio v0.8 añade lectura longitudinal al asistente, no un motor clínico alternativo.

## Entorno

Python >=3.11; entorno probado y versiones exactas en `change-manifest.json`. FastAPI, Pydantic, Uvicorn; httpx para integración y pytest para pruebas. No se añadieron dependencias al RAG. Para reinstalar dependencias en un entorno preparado: `python -m pip install -e ".[test,integration]"`. Este paso necesita paquetes disponibles; no forma parte de la ejecución offline. El corpus fuente y su índice deben distribuirse juntos conservando rutas y hashes.

## Iniciar la demostración existente

El backend y portal ya están iniciados en 8895/8896. No ejecutar una segunda instancia en esos puertos. Cuando estén detenidos, abrir dos terminales PowerShell:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -m vigile serve --integration-dir data\portal-v080-final --port 8895
```

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -m vigile.portal --config data\portal-v080-final\portal-config.json --port 8896
```

Abrir http://127.0.0.1:8896/. El código de acceso del portal está en `data\portal-v080-final\portal-access.txt`; es distinto de la credencial del backend. No compartirlo ni copiarlo en prompts. Ollama conserva su servicio actual en 127.0.0.1:8891 y el modelo existente; estos comandos no descargan ni reinstalan modelos.

Seleccionar `v07-crew-A`, B o C. A muestra cambios longitudinales; B hipoglucemia y seguimiento; C vigilancia multisistema/radiación. Elegir «Último ciclo de vigilancia» para preguntar por monitorización; «Evaluación clínica seleccionada» conserva el flujo anterior. Datos exclusivamente sintéticos.

## Reproducir pruebas y banco

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m vigile.ai_evaluation --reader-token-file data\portal-v080-final\reader-token.txt --library local_ai\library-v080.json --output ..\docs\v08\bank-recheck.json --modes FULL LOW_POWER CRITICAL
```

El banco necesita backend 8895 y Ollama 8891 activos; rechaza sobrescribir el archivo de resultados. Usar otro nombre para una segunda corrida. Las expectativas son reproducibles, pero el texto/latencia del modelo pueden variar; conservar cada resultado. El proceso del banco bloquea conexiones fuera de loopback.

Generar una simulación independiente, sin tocar historias anteriores:

```powershell
.\.venv\Scripts\python.exe -m vigile.monitoring_demo --output data\v080-recheck
```

Este comando exige una carpeta nueva y produce 15 ciclos, replay, OpenAPI, solicitudes, respuestas y mediciones locales. Para una nueva demostración de portal, también con carpeta nueva:

```powershell
.\.venv\Scripts\python.exe -m vigile.monitoring_portal_demo --output data\portal-v080-recheck --reuse-config data\portal-v080-final\portal-config.json
```

Arrancarla después de detener las instancias anteriores, sustituyendo la carpeta en los dos comandos de inicio. No editar bases antiguas para que coincidan con el hash nuevo. `before-v08.zip` y `release-source.zip` preservan fuentes por versión.

Para construir un índice de comprobación sin sobrescribir el activo:

```powershell
.\.venv\Scripts\python.exe -m vigile.knowledge_v08 --output local_ai\library-v080-recheck.json
```

## Contratos para el equipo

### Motor y sensores

Se conservan los endpoints y modelos de v0.7, consultables en `http://127.0.0.1:8895/docs`. El campo opcional nuevo `sample_ids` de la solicitud de ciclo es un mapa `{measurement_id: sample_id}`. Si se omite, cada medida conserva su identidad. Declarar el mismo ID solo si corresponde realmente a una misma toma. Los cambios de fase inválidos quedan en la traza; no son datos normales.

### Frontend y asistente

El navegador solo usa el portal autenticado por cookie local. Nunca recibe el token reader del backend. POST `/api/assistant` admite exactamente uno de estos campos:

```json
{"monitoring_id":"C-cycle-28","question":"Explain radiation dose coverage limitations.","history":[]}
```

```json
{"evaluation_id":"ID_DE_EVALUACION_EXISTENTE","question":"¿Qué datos faltan?","history":[]}
```

Ambos a la vez o ninguno producen 422. `history` admite hasta 3 preguntas; `question` entre 3 y 1200 caracteres. El contrato anterior con `evaluation_id` sigue válido.

La salida longitudinal incluye `run_id`, `as_of`, `mode`, `status`, `answer` (bloques exactos), `generated` (frases del modelo con evidence_ids), `documents`, `retrieved`, `document_issues`, `sources`, `inference_attempted`, `inference_executed`, `authority` y `clinical_execution`. Referencias de ENGINE y DOCUMENT se mantienen separadas. Véase `monitoring-response-example.json` y los casos completos del banco.

Estados: `EXTRACTIVE_ONLY`, `ANSWERED`, `EXTRACTIVE_FALLBACK`, `DETERMINISTIC_DATA_SUFFICIENCY`, `INSUFFICIENT_INFORMATION`, `REFUSED_ACTION`. No interpretar ninguno como estado diagnóstico: el estado clínico viene del motor. Un error de transporte debe mostrarse como indisponibilidad, nunca como resultado normal. No ocultar restricciones diagnósticas/terapéuticas cuando exista texto generado.

### Cliente reader externo

Ejemplo de lectura directa en PowerShell, sin imprimir la credencial:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$vigileReader = (Get-Content -Raw -LiteralPath 'data\portal-v080-final\reader-token.txt').Trim()
$vigileHeaders = @{ Authorization = "Bearer $vigileReader" }
Invoke-RestMethod 'http://127.0.0.1:8895/monitoring/cycles/C-cycle-28' -Headers $vigileHeaders
Invoke-RestMethod 'http://127.0.0.1:8895/monitoring/cycles/C-cycle-28/replay' -Headers $vigileHeaders
```

Los permisos y ámbitos se deciden en el backend. El reader no puede registrar mediciones/ciclos ni modificar reglas. El módulo de IA no recibe credenciales de investigador, administrador o médico. No usar el historial de conversación para cambiar de sujeto/contexto.

### Persona de optimización

Conservar FULL, LOW_POWER y CRITICAL y la ejecución del motor sin LLM. Usar tiempos crudos del banco como observaciones locales, no benchmark energético/de vuelo. No se optimizó profundamente RAM/VRAM. No eliminar snapshots, fuentes o verificaciones para mejorar latencia sin un contrato de degradación explícito.

## Estado y próximos trabajos

Prioridad: auditoría especializada del banco y errores semánticos por revisores independientes; investigar desconexiones locales intermitentes; ampliar cobertura documental primaria y consultas retenidas fuera del banco de desarrollo; fortalecer aislamiento y almacenamiento. El motor sigue siendo un prototipo integrable de investigación. Ninguna prueba sintética ni comprobación del mismo modelo constituye validación clínica independiente.


Comprobación adversarial adicional con Ollama real (requiere servicios locales activos; conserva corpus y registros):

```powershell
.\.venv\Scripts\python.exe ..\docs\v08\evaluate_adversarial.py --output ..\docs\v08\bank-adversarial-recheck.json
```

El OpenAPI del backend se conserva en `backend-openapi.json`. El del portal se exportó localmente a `portal-openapi.json`; su publicación por HTTP está deshabilitada por el diseño existente (404), sin afectar a `/api/assistant`.
