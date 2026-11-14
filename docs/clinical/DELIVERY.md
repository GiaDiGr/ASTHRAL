# Entrega clínica VIGILE v0.4 — 2026-10-16

Implementación incremental en `C:\Users\Gianni\Desktop\Vigile`. Se revisaron módulos existentes de engine/vigile, modelos, Store, autenticación, API, CLI, simulador, pruebas y contratos; se leyó íntegro el informe focalizado y se conservó su copia exacta. Inventario original: **106 archivos sin cambios**. El ZIP previo v0.3 se conserva en la carpeta work/releases del workspace de Codex.

**Verificación:** baseline 172 pruebas; entrega **251 pruebas aprobadas**, 0 fallos, 0 errores y 0 omitidas, en 57.84 s. Incluye los 30 casos reconciliados y 49 pruebas adicionales de seguridad/criterios/integración. Advertencia pendiente: deprecación Starlette/httpx. No hay validación clínica u operacional.

## Arquitectura y archivos

Ocho módulos clínicos nuevos: clinical_models.py, clinical_logic.py, clinical_knowledge.py, clinical_engine.py, clinical_differential.py, clinical_api.py, clinical_simulator.py, clinical_demo.py. Modificados: api.py, security.py, quality.py, __main__.py, service.py, __init__.py, pyproject.toml y README. Nueva suite tests/test_clinical.py. Ocho JSON originales más manifiesto bajo engine/vigile/clinical_knowledge. Documentación y resultados en docs/clinical. No se reemplazó el motor ni el almacenamiento; clinical_evaluation es un tipo de registro en la tabla existente y comparte auditoría transaccional.

Modelos estrictos, lógica de tres valores, criterios compuestos, validación de calidad/unidades/método, confirmación por muestras independientes, ventanas AKI, diferencias respecto de muestras basales, ranking diferencial ordinal, pruebas pendientes, elegibilidad bloqueada, reevaluación inmutable, replay y proyección reader están conectados a FastAPI. La edad es obligatoria para aplicar la ruta POTS >=20 años; el resto de reglas no se transforma en diagnóstico confirmado por el LLM.

## Cobertura computacional

| Ruta | Operativo | Límite |
|---|---|---|
| DM | Cuatro vías ADA; confirmación, discordancia, exclusión de CGM, calidad OGTT/A1C | Adultos no gestantes; no tipificación etiológica ni tratamiento |
| DKA | Tres componentes, diabetes conocida con glucemia menor, indicador de resolución, potasio y recursos | Sin ejecución; revisión de simultaneidad clínica pendiente |
| OH | Diferencias de BP, ventana <=3 min, persistencia declarada | Microgravedad no aplicable; gravedad parcial bloqueada |
| POTS | Incremento sostenido, ventana, duración, síntomas y exclusiones; OH calculada excluye POTS | >=20 años; requiere edad y contexto; no rama adolescente |
| AKI | Delta 48 h, razón 7 días, diuresis validada, etapas 1–3 | Sin imputar baseline; etapa mínima sustentada; contexto espacial limitado |
| Anafilaxia | Dos vías WAO, sin exigir piel en segunda, emergencia independiente | Restricciones de exposición; datos ausentes no se vuelven falsos |
| Diferencial | 6 presentaciones; orden ordinal y pruebas explicadas | Ramas externas sin diagnóstico ni probabilidades inventadas |
| Protocolos | Seis documentos y consulta de elegibilidad | Toda ejecución y autorización de misión bloqueadas |

La cobertura estructural histórica de 44 condiciones no equivale a estas seis rutas computables. No se añade validación clínica a ninguna condición. Prevención/pronóstico autónomos y condiciones externas siguen fuera de alcance.

## Demo y rendimiento inicial

Demo final en docs/clinical/demo-final: 28 solicitudes HTTP ASGI, replay concordante, escritura reader rechazada y auditoría íntegra. Mediana **11.71 ms**, máximo **78.72 ms**, pico de asignaciones Python **7316752 bytes**, SQLite **229376 bytes**. No son medidas RSS/CPU, latencia TCP, carga sostenida ni rendimiento en hardware de vuelo.

Flujo DKA: /devices → /measurements → bindings clínicos → CRITERIA_MET/EMERGENCY → bloqueos → lectura reader → replay → reevaluación con potasio bajo. Anafilaxia mantiene emergencia sin autorización. Mareo/taquicardia presenta vía externa de arritmia y ECG sin inventar su diagnóstico.

## Documentos y contratos

- INTEGRATION.md: comandos, endpoints, seguridad, modelos y responsabilidades de frontend/RAG/sensores/optimizador.
- DECISIONS.md: contradicciones, fuentes primarias contrastadas y limitaciones.
- case-reconciliation.json/.md: las 30 entradas originales, resultados y diferencias justificadas.
- demo-final/synthetic-http-transcript.json: solicitudes y respuestas reales, sin credenciales.
- openapi-v04.json: contrato API completo actualizado.
- verification.json y tests-v04.xml: evidencia de ejecución.
- original-preservation.json, knowledge-audit.json y change-manifest.json: conservación, enlaces de conocimiento y cambios.

## Pendientes priorizados

1. Revisión biomédica independiente de reconciliaciones, población, simultaneidad, calidad y prioridad de pruebas; completar IDs de pruebas de seguridad y rutas externas antes de activarlas.
2. Definir gobernanza, firma y revisión de políticas de misión. Ningún protocolo puede ejecutarse con el código entregado.
3. Aislar procesos y secretos, cifrar almacenamiento/backups y anclar externamente auditoría/manifiestos. Un administrador de disco/código puede reescribir una cadena local.
4. Integrar hardware real mediante contratos existentes y verificar calibración, procedencia y disponibilidad sin presumir inventario espacial.
5. Ensayos de carga, CPU/RSS, disco lleno, fallos de proceso, hardware limitado y revisión de la dependencia TestClient. No confundir demo sintética con validación operacional.

## CONTEXTO PARA CONTINUAR CON CHATGPT

VIGILE v0.4 conserva arquitectura Python/FastAPI/Pydantic/SQLite y módulos previos. Nueva capa focalizada en DM, DKA, OH, POTS, AKI y anafilaxia, con diferencial de seis presentaciones. 251 tests aprobados. Ocho JSON y original preservados; hashes, criterio/fuente/versión, snapshot y árbol por evaluación. No migración destructiva de BD. Autorización terapéutica no implementada: fail closed. RAG reader solo proyecciones autorizadas y documentos; no snapshots ni escritura.

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile clinical-demo
& .\.venv\Scripts\python.exe -m vigile init
& .\.venv\Scripts\python.exe -m vigile serve --port 8765
```

Los dos primeros comandos verifican la entrega completa con datos sintéticos. La demo imprime una carpeta nueva con ejemplos. Los últimos inician la API TCP habitual; asignar scopes reader desde configuración del servidor. Integrar frontend/RAG mediante /clinical/evaluations/{id}, differential, next-tests y sources; sensores mediante /measurements y measurement_bindings. ClinicalRequest declara as_of/window_start, población, edad para POTS y observaciones con método, calidad y muestra. No entregar credenciales de escritura al LLM. Antes de modificar reglas revisar DECISIONS.md; no convertir las expectativas originales contradictorias en pruebas verdes por imputación de datos.
