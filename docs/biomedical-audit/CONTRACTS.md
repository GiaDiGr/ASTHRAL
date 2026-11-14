# Contratos de integración del núcleo biomédico

Esquema completo: `openapi.json`. Modelos: `engine/vigile/clinical_contracts.py`. Identidad de implementación: `change-manifest.json`; el rótulo histórico del paquete no basta. No se retiran componentes del equipo ni se cambian URLs del portal/Ollama.

## Salida autoritativa

`POST /clinical/evaluations` y `/clinical/presentations/evaluate` requieren researcher autorizado; retornan 201 con `ClinicalEvaluationResponse`. GET de evaluación, diferencial, pruebas y replay permite reader dentro de su ámbito. Reevaluar exige researcher, mismo sujeto/misión/ruta y tiempo no regresivo. No se puede enviar rol, diagnóstico autorizado ni tratamiento en la solicitud.

Cada resultado separa `diagnostic_status`, `urgency`, `confirmation_status`, `protocol_status`, `treatment_status`. Los resultados de laboratorio no son diagnósticos; las hipótesis diferenciales no son enfermedades confirmadas. `protocol.automatic_execution=false`, `new_authorization=false`, `treatment_status=NOT_STARTED`.

| Campo | Contrato |
|---|---|
| `missing_required` | Candidatos ausentes capaces de resolver ramas indeterminadas; respetar AND/OR. No significa que todos sean individualmente obligatorios. |
| `optional_not_measured` | Ausencias que no bloquean el estado lógico actual; no implican normalidad ni inutilidad clínica universal. |
| `invalid_required` | Datos presentes pero inutilizables en ramas todavía indeterminadas. |
| `invalid_fields` | Todos los datos inválidos del árbol, también los de alternativas no decisivas. |
| `required_for_protocol_safety` | Restricciones de seguridad independientes del diagnóstico. No es una lista terapéutica exhaustiva. |
| `missing_fields` | Legado: hojas indeterminadas; no mostrar como requisitos obligatorios. |
| `evaluation_tree` | Árbol recursivo completo: `state` bool/null, `truth_state`, razones, rutas, contexto y descendientes no podados. |
| `confirmation_evidence` | En raíz ADA, pruebas positivas con vía, muestra e instante. No representa autorización médica. |
| `context_observation_ids` | Observaciones contextuales seleccionadas por muestra para la evaluación DM. |
| `metadata.derivation_inputs` | Identificadores de entradas seleccionadas para derivaciones existentes. |

AND: FALSE determina; sin FALSE, INVALID precede a UNKNOWN; todos TRUE producen TRUE. OR: TRUE determina; sin TRUE, INVALID precede a UNKNOWN; todos FALSE producen FALSE. La confirmación ADA es una operación de nivel superior, no una OR simple. Una rama verdadera no puede convertir en obligatorio el bicarbonato ausente si ya hay pH válido positivo.

El estado final incorpora población, fuente y gravedad además del árbol. Mostrar limitaciones. Las pruebas pendientes distinguen `purpose=DIAGNOSTIC_RESOLUTION` y `PROTOCOL_SAFETY`; `execution_authorized=false` en ambos casos.

## Compatibilidad y cambios de comportamiento

1. No se eliminaron campos ni endpoints. Serialización `response_model_exclude_unset=True`: registros antiguos sin campos de suficiencia siguen sin esos campos; no se rellenan como si hubieran sido evaluados con lógica nueva. El cliente debe mostrar «clasificación no disponible» y pedir reevaluación versionada, no interpretar ausencia de propiedad como lista vacía clínica.
2. No se permite condición y presentación juntas; enviar exactamente una. Las solicitudes ambiguas ahora responden 422.
3. Anafilaxia: enviar `adult_sbp_mm_hg` para la presión actual. Ya no se acepta implícitamente `upright_sbp_mm_hg` como sustituto para calcular la caída porcentual. La entrada anterior permanece válida para OH; sin presión actual la alternativa porcentual anafiláctica queda desconocida. No se renombraron campos de entrada.
4. DM: asignar el mismo `sample_id` a las atestaciones que pertenecen a una colección/contexto clínico. Los síntomas/crisis de otra colección ya no sirven automáticamente para la vía aleatoria. Las repeticiones requieren IDs y tiempos reales distintos; nunca fabricar IDs para conseguir confirmación.
5. Mediciones vinculadas: se cumple la caducidad técnica a `as_of`; para evaluación retrospectiva fijar el momento real de evaluación. No ampliar `max_age_seconds` para forzar un resultado. El baseline renal histórico es una excepción explícita con ventana propia.
6. Reproducción: la lectura histórica sigue posible. Un código diferente produce `REPLAY_VERSION_MISMATCH`; usar el archivo de implementación de esa versión o crear una reevaluación nueva. No reescribir hashes históricos.

## Ejemplo del caso DKA

Solicitud: adulto, población establecida, diabetes conocida, glucosa plasmática 180 mg/dL, beta-OHB 4.2 mmol/L, pH venoso 7.22; método, tiempo y calidad válidos. Extracto conceptual de salida:

```json
{
  "diagnostic_status": "CRITERIA_MET",
  "urgency": "EMERGENCY",
  "missing_required": [],
  "optional_not_measured": ["bicarbonate_mmol_l", "urine_ketones_plus"],
  "invalid_required": [],
  "required_for_protocol_safety": ["potassium_mmol_l"],
  "protocol_status": "BLOCKED_MISSING_DATA",
  "treatment_status": "NOT_STARTED"
}
```

No es un diagnóstico médico autorizado. Las respuestas completas reproducibles están en `cases-30-reviewed.json` y la demo HTTP. Un consumidor RAG explica estos estados ya emitidos; no altera reglas, resultados o autorizaciones y no dispone de credenciales de escritura.

## Consulta reader desde PowerShell

```powershell
$vigileReader = (Get-Content -LiteralPath 'C:\Users\Gianni\Desktop\Vigile\engine\data\portal-biomedical-audit-final\reader-token.txt' -Raw).Trim()
$vigileHeaders = @{Authorization=('Bearer ' + $vigileReader)}
Invoke-RestMethod -Uri 'http://127.0.0.1:8895/clinical/knowledge/version' -Headers $vigileHeaders
# Sustituir <id> por el ID real de una evaluación visible para este reader.
Invoke-RestMethod -Uri 'http://127.0.0.1:8895/clinical/evaluations/<id>' -Headers $vigileHeaders
```

No registrar tokens en transcripciones ni enviarlos al LLM. La cuenta reader está limitada a los sujetos/misiones de su configuración. Para entregar credenciales a otro proceso, usar un archivo protegido separado, no copiar los archivos del servidor. El paquete de revisión no contiene credenciales ni bases de datos.
