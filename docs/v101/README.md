# VIGILE v1.0.1 — apoyo al manejo, no ejecución terapéutica

Extensión incremental de R2: protocolos reutilizados, restricciones documentales por intervención, inventario sintético versionado por misión, snapshots reproducibles y declaraciones humanas de seguimiento. Las siete rutas y sus criterios/umbrales permanecen iguales. G05 conserva NO_VERIFIED_MISSION_POLICY y el bloqueo de autorización. No hay administración, dispensación, consumo automático, cálculo ejecutable de dosis ni verificación de eficacia.

Estado y resultados exactos: RESULTS.json, final-tests.xml, r2-replay-verification.json y clinical-invariance-*.json. Los fallos de desarrollo se conservan aparte; no cuentan como resultados finales. La prueba física de voz de R2 sigue pendiente. La inspección visual real de esta revisión no pudo iniciarse por un error de assets del kernel CUA: HTTP y pruebas DOM simuladas no se presentan como inspección visual.

## Ejecutar la demostración preparada

PowerShell privado:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$py = '.\.venv\Scripts\python.exe'
& $py tools\demo_management_v101.py serve --output data\mission-v101-final
```

Portal http://127.0.0.1:8902/; backend http://127.0.0.1:8901/health. Se rechazan puertos ocupados; no se detienen servicios R2. Ctrl+C sólo termina hijos del supervisor. Ollama conserva 127.0.0.1:8891 y vigile-qwen3-4b:latest; su disponibilidad no condiciona manejo determinista. No modificar Norton/cuarentena ni configuración de Ollama.

En otra consola privada obtener sólo el código del portal, sin copiarlo a archivos, informes o prompts:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/mission-v101-final/portal-access.txt'))"
```

Entrar → Evaluación clínica → DKA del ciclo v101-management-cycle → Manejo documentado. La prioridad de emergencia queda fuera de las tarjetas ocultables. Expandir una intervención para distinguir condiciones, potasio específico de insulinoterapia, inventario congelado, autoridad pendiente y pauta original. Los registros humanos aparecen separados y no cambian NOT_STARTED. Seleccionar la evaluación de anafilaxia sospechada para revisar urgencia con criterios incompletos.

## Repetición aislada

El directorio de salida DEBE ser nuevo:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$py = '.\.venv\Scripts\python.exe'
& $py tools\demo_management_v101.py prepare --output data\mission-v101-my-demo
& $py tools\demo_management_v101.py serve --output data\mission-v101-my-demo
& $py -m pytest -q --junitxml=..\work\v101\my-tests.xml
```

prepare reutiliza clinical_demo y los servicios existentes: cinco escenarios, cuatro versiones de inventario ficticio, once evaluaciones clínicas y un ciclo adicional de monitorización, cinco declaraciones humanas y un checkpoint. Conserva replays y crea credenciales nuevas DPAPI con ACL. Sólo persiste operator/reader; la identidad de bootstrap researcher se descarta. Cambiar inventario posteriormente requiere provisionamiento de servidor autorizado; ningún rol reader/LLM puede elevarse por API.

Escenarios: DKA sin K; insulina ficticia vencida; monitorización desconocida; recursos disponibles pero autorización aún bloqueada; anafilaxia con sospecha urgente y recursos no verificados. No inventario NASA ni pacientes reales ni fármacos administrados. management-report.json guarda salidas completas sin credenciales. inventory quantities/conditions son datos ficticios, no instrucciones de almacenamiento de medicamentos.

## Compatibilidad, requisitos y datos

Sin nuevas dependencias ni migración SQL. Se reutilizan Python/FastAPI/Pydantic/SQLite y herramientas de voz existentes. Node sólo es necesario para pruebas de DOM simuladas, no para el motor. Windows/DPAPI se requieren para preparar/servir la demo protegida. No se redistribuyen pesos ni voces.

ClinicalRequest y MonitoringRequest añaden resource_policy. El valor por defecto DECLARED_R2 conserva el significado de resources y sus resultados; MISSION_INVENTORY es opt-in y rechaza mezclar flags declarados. Las evaluaciones sintéticas nuevas incorporan management aditivo; consumidores estrictos deben usar el contrato Pydantic/OpenAPI v1.0.1 o una proyección de los campos R2. Un consumidor R2 con extra=forbid requiere esa migración explícita.

Los registros R2 no reciben management retroactivo ni inventario actual. Sus replays requieren el runtime archivado exacto, no esta versión. Copia aislada y código recuperable en work/v101/r2-runtime y r2-db-copy; ZIP R2 y datos originales conservados. No usar v1.0.1 para reevaluar silenciosamente una base congelada. No se reejecutó el banco reservado LLM/RAG ya utilizado.

SQLite/WAL/backups siguen SIN CIFRADO. DPAPI/ACL/HMAC no aíslan procesos de la misma cuenta. La autoridad y la verificación de un recurso de la demo son declaraciones sintéticas, no acreditación médica o farmacéutica real. No usar datos clínicos reales. Sólo prototipo de investigación; pruebas de software no validan clínica, operación ni vuelo.
## Resultado de cierre y siguiente revisión

Suite final: **687 aprobadas, cero fallos/errores/omisiones**, 464.77 segundos según salida pytest (tiempo JUnit en RESULTS.json). Una advertencia de deprecación Starlette/httpx, sin cambiar dependencias. Las 54 pruebas nuevas incluyen una prueba que ejecuta seis escenarios DOM simulados. 30 casos originales idénticos a R2; 76 replays archivados correctos; demo nueva con 11 replays clínicos y uno de monitorización correctos, también después de restaurar respaldo verificado. Inventario, manejo y seguimiento accesibles por reader; escritura reader rechazada con 403.

Entrega técnica apta para integración de investigación con datos sintéticos, ejecución terapéutica siempre bloqueada y consumidores adaptados al contrato aditivo. Pendientes: revisión clínica de CLINICAL_REVIEW.md, inspección visual real, prueba física de voz, aislamiento y cifrado de almacenamiento/política operacional. No validación clínica independiente, operacional ni de vuelo.

Detalle: IMPLEMENTATION.md, INTEGRATION_CONTRACTS.md, COVERAGE.md y EXAMPLES.md. Resultados reales completos en examples.json/demo-report.json; esquema exacto en openapi.json; archivo de código recuperable sin bases, credenciales o pesos en candidate-code-v101.zip y CODE_FREEZE.json. Base privada sólo en engine/data/mission-v101-final; respaldo verificado privado en work/v101/final-db-backup. Copiar código no redistribuye ni aprovisiona credenciales/modelos.

Próximo trabajo priorizado: (1) revisión humana de discrepancias terapéuticas y fuentes/localizadores, (2) QA visual y voz física, (3) aislamiento/cifrado/política de autoridad de misión antes de considerar datos reales, (4) integración de consumidores sobre OpenAPI y pruebas de contrato. Mantener bloqueos hasta aprobación y validación adecuadas.

El ZIP de código no es una distribución autónoma del corpus: restaurarlo en una copia de VIGILE con los catálogos, documentos científicos y fuentes RAG originales conservados. El archivo no contiene esas bibliotecas completas, pesos ni credenciales. No sustituir con él la carpeta R2 congelada ni su base.