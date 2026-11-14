# Ejemplos comprobados y recorrido

examples.json contiene cuatro respuestas GET reales de loopback, rechazo reader 403, cuatro cuerpos completos de InventoryVersion (aplicables en orden sólo a una misión nueva) y un ClinicalRequest real con resource_policy=MISSION_INVENTORY. No incluye credenciales. demo-report.json contiene resultados completos, snapshots de manejo, seguimiento y replays. Los identificadores generados cambian al preparar otra demo; usar los nuevos del informe, no IDs de esta corrida.

| Escenario real sintético | Criterios | Recurso de insulinoterapia/epinefrina | Restricción destacada | Resultado |
|---|---|---|---|---|
| DKA sin potasio | CRITERIA_MET | RESOURCE_AVAILABLE | BLOCKED_MISSING_DATA:POTASSIUM, específica de insulinoterapia | EMERGENCY, AUTHORIZATION_REQUIRED |
| DKA con insulina ficticia vencida | CRITERIA_MET | RESOURCE_UNAVAILABLE | Caducidad | EMERGENCY, AUTHORIZATION_REQUIRED |
| DKA con monitorización desconocida | CRITERIA_MET | RESOURCE_UNVERIFIED | Verificación pendiente | EMERGENCY, AUTHORIZATION_REQUIRED |
| DKA recursos disponibles, K=4 | CRITERIA_MET | RESOURCE_AVAILABLE | Política de autoridad no verificada | EMERGENCY, AUTHORIZATION_REQUIRED |
| Anafilaxia sospechada, sin recursos | SUSPECTED | RESOURCE_UNVERIFIED | Criterios incompletos; urgencia preservada | EMERGENCY, AUTHORIZATION_REQUIRED |

Todos: treatment_status=NOT_STARTED, clinical_execution=BLOCKED. Una lista vacía de restricciones no demuestra ausencia de contraindicaciones. La revisión de capacidad IV DKA no recibe el bloqueo de potasio de insulina; tampoco constituye una orden de fluidos.

## Cliente externo reader (PowerShell privado)

Con el supervisor activo, obtener token sólo en memoria y consultar el checkpoint y sus identificadores. No imprimir token ni pegarlo en prompts/logs:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$reader = & .\.venv\Scripts\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/mission-v101-final/reader-token.txt'))"
$headers = @{ Authorization = "Bearer $reader" }
$dashboard = Invoke-RestMethod 'http://127.0.0.1:8901/dashboard/subjects/clinical-crew?mission_id=clinical-earth&frame_id=v101-management-frame' -Headers $headers
$cycle = $dashboard.monitoring | Where-Object { $_.id -eq 'v101-management-cycle' }
$id = $cycle.clinical_evaluations.DKA.id
Invoke-RestMethod "http://127.0.0.1:8901/clinical/evaluations/$id/management" -Headers $headers
Invoke-RestMethod "http://127.0.0.1:8901/clinical/evaluations/$id/management-records?as_of=2026-10-16T20:00:00Z" -Headers $headers
Invoke-RestMethod 'http://127.0.0.1:8901/missions/clinical-earth/medical-inventory?as_of=2026-10-16T20:00:00Z' -Headers $headers
Remove-Variable reader,headers
```

GET /openapi.json también requiere reader válido; copia pública de esquema exacto en esta carpeta. Para probar publicación de inventario se requiere identidad researcher/clinician provisionada en servidor: la demo descarta bootstrap y no proporciona una elevación vía API. Los cuerpos examples.json son datos ficticios de software, no instrucciones de preparación o almacenamiento de medicación.

## Recorrido en el portal

Abrir http://127.0.0.1:8902/, usar código protegido según README y seleccionar frame v101-management-frame. En Evaluación clínica elegir DKA de v101-management-cycle. Mantener visible urgencia EMERGENCY; abrir Manejo documentado y separar indicación documental, condiciones, recursos, autorización y seguimiento. Hay cinco registros humanos no verificados y un plan pendiente; HUMAN_REPORTED_PERFORMED no cambia tratamiento a ejecutado. Elegir escenario de anafilaxia para comprobar SUSPECTED + EMERGENCY + recursos no verificados. Contramedidas sólo aparecen para variables pertinentes/fase; la demo clínica no simula toda vigilancia espacial y no debe fingirla.

Este recorrido tiene comprobaciones HTTP y seis casos DOM simulados. No se completó inspección visual real por fallo de inicialización CUA, ni prueba física de voz/micrófono.
