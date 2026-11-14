# VIGILE v0.9.0 — ejecución, integración y reproducción

Lea [A. Auditoría LLM/RAG](A_LLM_RAG_AUDIT.md) y [B. Space Computing](B_SPACE_COMPUTING.md). Los datos de esta entrega son sintéticos. No hay nuevas enfermedades ni cambios de umbrales clínicos.

## Servicios actuales y arranque

Backend 127.0.0.1:8895; portal 127.0.0.1:8896; Ollama 127.0.0.1:8891 con `vigile-qwen3-4b:latest`. Demostración activa nueva: `engine/data/portal-v090-release`. No ejecutar instancias duplicadas en esos puertos.

Cuando backend y portal estén detenidos, iniciar en dos terminales PowerShell:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -m vigile serve --integration-dir data\portal-v090-release --port 8895
```

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -m vigile.portal --config data\portal-v090-release\portal-config.json --port 8896
```

Si Ollama está detenido, usar el helper existente; no ejecutar llama-server ni restaurar cuarentena:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe tools\start_ollama_vigile.py
```

Abrir http://127.0.0.1:8896/. El código local del portal está en `data\portal-v090-release\portal-access.txt`. No introducir una credencial del backend en el navegador ni copiar secretos a conversaciones. Seleccionar astronautas sintéticos A/B/C y el contexto de evaluación o último ciclo. El portal usa exclusivamente reader en el servidor.

Requisitos: Python >=3.11, entorno probado Python 3.13.16; FastAPI, Pydantic y Uvicorn existentes, httpx para integración y pytest para pruebas. Versiones exactas en `change-manifest.json`. Instalar dependencias solo si es necesario en un entorno nuevo: `python -m pip install -e ".[test,integration]"`; requiere paquetes disponibles y puede necesitar red. La ejecución posterior no necesita Internet. La telemetría Windows utiliza nvidia-smi si está disponible; GPU desconocida se informa como no disponible.

## Pruebas y bancos

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe ..\docs\v09\evaluate_audit.py --folder data\portal-v090-release --output ..\docs\v09\audit-recheck-full.json --mode FULL
.\.venv\Scripts\python.exe ..\docs\v09\evaluate_audit.py --folder data\portal-v090-release --output ..\docs\v09\audit-recheck-low.json --mode LOW_POWER
.\.venv\Scripts\python.exe ..\docs\v09\evaluate_audit.py --folder data\portal-v090-release --output ..\docs\v09\audit-recheck-critical.json --mode CRITICAL
```

Los runners requieren servicios locales activos, bloquean conexiones externas en su proceso y rechazan sobrescribir resultados. Usar nombres nuevos para repetir. Texto, carga y latencias de Ollama pueden variar; conservar cada corrida. No ejecutar `reserved-bank.json` durante ajustes: sus 12 casos quedan para evaluación futura.

`human-review-sample.json` y `human-review-rubric.csv` están preparados para revisión humana independiente; las columnas siguen vacías. No confundir los checks automáticos del banco con esa revisión.

## Benchmark y fallos

Desde `engine`:

```powershell
.\.venv\Scripts\python.exe ..\docs\v09\benchmark_compute.py --output ..\docs\v09\compute-recheck.json --samples 6 --soak-seconds 120
.\.venv\Scripts\python.exe ..\docs\v09\benchmark_endtoend.py --output ..\docs\v09\endtoend-recheck.json
.\.venv\Scripts\python.exe ..\docs\v09\profile_resources.py --output ..\docs\v09\resources-recheck.json
.\.venv\Scripts\python.exe ..\docs\v09\stability_soak.py --output ..\docs\v09\soak-recheck.json --seconds 300
```

El benchmark compute descarga y recarga **solo el modelo seleccionado** mediante su API, prueba una solicitud CPU y restaura FULL. Ejecutarlo sin otros usuarios del asistente para evitar interferencias; no cambia reglas clínicas ni configuración global del daemon. Usa la base sintética de referencia indicada en su código; puede sustituirse por otra demostración con iguales escenarios. Los scripts de perfil, extremo a extremo, recuperación y bancos rechazan sobrescribir resultados existentes; indicar un nombre de salida nuevo.

Liberación explícita del modelo, separada del cambio a CRITICAL:

```powershell
.\.venv\Scripts\python.exe -m vigile.space_compute release
.\.venv\Scripts\python.exe -m vigile.space_compute telemetry
```

`release` no cambia el modo del portal: FULL podrá volver a cargar el modelo en la próxima consulta. CRITICAL evita inferencia, pero no implica memoria liberada. La API de modos mantiene su contrato anterior. La prueba física de pérdida/reinicio se reproduce con:

```powershell
.\.venv\Scripts\python.exe ..\docs\v09\verify_runtime_recovery.py --output ..\docs\v09\recovery-recheck.json
```

Esa prueba detiene únicamente el daemon cuyo PID y ejecutable constan en `ollama-process.json`, verifica la ruta y lo reinicia con el helper original; puede interrumpir otras consultas al mismo runtime. No usarla mientras otra persona esté trabajando. `verify_live.py` comprueba replay, permisos, invariancia y concurrencia sin detener Ollama. No hay razón para tocar Norton.

## Demostración nueva sin destruir historias

```powershell
.\.venv\Scripts\python.exe -m vigile.monitoring_demo --output data\v090-recheck
.\.venv\Scripts\python.exe -m vigile.monitoring_portal_demo --output data\portal-v090-recheck --reuse-config data\portal-v090-release\portal-config.json
```

Cada carpeta debe ser nueva. Las reproducciones históricas requieren su implementación exacta: conservar `before-v09.zip`, la entrega v0.8 y las bases antiguas. No reescribir hashes para aprobar replay con código diferente. `release-source.zip` conserva las fuentes finales sin bases ni credenciales.

## Contrato del asistente y compatibilidad

POST `/api/assistant` sigue aceptando exactamente uno de `monitoring_id` o `evaluation_id`. Se añadieron campos opcionales:

```json
{
  "monitoring_id": "A-cycle-14",
  "question": "How are baselines selected and validated?",
  "history": [],
  "history_context_id": "A-cycle-14",
  "documentary": true
}
```

- Sin `history_context_id`, el historial se ignora para evitar atribución entre contextos; las preguntas anteriores siguen siendo compatibles como petición, pero cambia ese comportamiento deliberadamente. Para usarlo, enviar el ID del objetivo actual y reiniciar historial cuando cambie sujeto, misión, evaluación o ciclo. El frontend ya envía el campo.
- `documentary` es falso por defecto. Si es verdadero, añade `documentary_explanation` con documentos, citas exactas seleccionadas, estado de comparación y posibles discrepancias explícitas. No sustituye `answer`, `generated`, ni los estados del motor.
- Nuevos estados posibles de seguridad: `CONTEXT_MISMATCH` y falta de evidencia antes de invocar el modelo. El cliente debe mostrar el mensaje y el resultado exacto, sin convertir esos estados en normalidad clínica.
- Los bloques clínicos y los contratos de `missing_required`, `optional_not_measured`, `invalid_required` y `required_for_protocol_safety` siguen siendo autoridad del motor.
- Una cita documental no significa que su contenido haya sido adjudicado científicamente ni que sea un resultado del astronauta. Mostrar `authority`, versión, referencia y limitaciones. El modelo no recibe herramientas ni credenciales de escritura.

`backend-openapi.json` y `portal-openapi.json` son copias de los contratos. El OpenAPI del backend está protegido con Bearer en `/openapi.json`; el portal conserva deshabilitada su publicación HTTP y se exporta localmente.

Ejemplo de cliente reader, sin imprimir su token:

```powershell
$vigileToken = (Get-Content -Raw -LiteralPath 'data\portal-v090-release\reader-token.txt').Trim()
$vigileHeaders = @{ Authorization = "Bearer $vigileToken" }
Invoke-RestMethod 'http://127.0.0.1:8895/monitoring/cycles/A-cycle-14' -Headers $vigileHeaders
Invoke-RestMethod 'http://127.0.0.1:8895/monitoring/cycles/A-cycle-14/replay' -Headers $vigileHeaders
```

## Integración con el equipo

Sensores/simuladores conservan `/monitoring/cycles`, IDs, unidades, calidad, muestras y contexto de v0.7/v0.8. Frontend conserva por separado vigilancia, criterios, confirmación, urgencia, seguridad y autorización; debe manejar 429/502 y fallback. IA/RAG usa únicamente reader y documentación verificada. Space Computing puede ajustar presupuestos medidos sin cambiar snapshots, reglas, fuentes ni resultados clínicos. No compartir el token del backend con navegador o LLM.

Prioridades pendientes: revisión humana de las respuestas y omisiones; mejorar recuperación de pasajes con otro conjunto de evaluación; auditoría computacional independiente con ensayos repetidos y carga sostenida de horas; hardware espacial real; aislamiento de procesos, cifrado/ACL y anclaje externo de auditoría. No se declara fiabilidad clínica, consumo energético medido ni aptitud de vuelo.

## CONTEXTO PARA CONTINUAR CON CHATGPT

Versión de componentes v0.9.0, base activa `portal-v090-release`, backend 8895, portal 8896, Ollama 8891 y modelo original. Suite: 545 aprobadas. Auditoría de desarrollo: 36 consultas por modo; 12 reservadas intactas. RAG: corpus v0.8 sin modificar, verificación más estricta y caché pública acotada. Integración documental opcional mediante citas exactas. Políticas FULL 6144/8/700, LOW_POWER 2048/4/300, CRITICAL sin inferencia. Medidas y limitaciones en los dos informes; datos crudos y paquete de revisión humana conservados. No ampliar catálogo clínico ni afirmar validación a partir de pruebas sintéticas.
