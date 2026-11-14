# VIGILE v1.0.1 — experiencia del astronauta

Cierre incremental de presentación. No nuevo motor, enfermedades, algoritmos, terapias, umbrales, dosis, autorizaciones, servicios de Internet ni cambios de Ollama/Norton. La demostración reutiliza exactamente mission_demo seed=42 con el motor v1.0.1 existente; conserva fechas/mediciones/escenarios y resultados de R2. Los cuerpos de solicitud sólo añaden el default v1.0.1 resource_policy=DECLARED_R2, por lo que el hash de solicitudes completo cambia respecto a R2, pero es idéntico al retirar ese único campo. Hash semántico de resultados igual a R2 en http-and-invariance.json.

## Iniciar la demo preparada

Mientras el supervisor está activo: http://127.0.0.1:8912/ (backend 8911). No reiniciarlo sobre puertos ocupados. Para iniciarlo una vez detenido:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe tools\demo_astronaut_v101.py serve --output data\mission-v101-astronaut
```

Obtener el código del portal sólo en una consola privada. No copiarlo a informes/prompts ni utilizar un token backend como código:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/mission-v101-astronaut/portal-access.txt'))"
```

Guion: DEMO_5_MIN.md. El usuario navega por los selectores Astronauta/misión y Momento de misión. El panel Tu recorrido de salud abre mediciones/tendencias, hallazgos, prevención, evaluación/manejo y seguimiento. No crea resultados o relaciones. Un botón de evaluación sólo aparece si el ID está explícitamente en clinical_evaluations del ciclo y en la proyección autorizada. Cambiar fecha invalida contexto anterior; una evaluación de otra fecha queda identificada, con vínculo al checkpoint de origen. Urgencia preservada con fechas/IDs de sus contextos.

## Repetición independiente, con directorio NUEVO

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$py = '.\.venv\Scripts\python.exe'
& $py tools\demo_astronaut_v101.py prepare --output data\mission-v101-astronaut-repeat
& $py tools\demo_astronaut_v101.py verify --output data\mission-v101-astronaut-repeat --report ..\work\v101-ux\repeat-verification.json
& $py tools\demo_astronaut_v101.py serve --output data\mission-v101-astronaut-repeat
```

prepare rechaza una carpeta existente; verify rechaza un informe existente. Para segunda repetición usar otros nombres. serve reutiliza supervisor v1.0.1: sólo loopback, puertos 8911/8912, rechaza ocupados y termina sólo sus propios hijos al finalizar. No altera procesos R2/v1.0.1/Ollama. La demo descarta bootstrap researcher y conserva credenciales nuevas protegidas por DPAPI/ACL para reader y adquisición. El portal sigue siendo reader; no puede crear inventario, tratamientos, mediciones o seguimiento clínico.

## Pruebas

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -m pytest -q --junitxml=..\work\v101-ux\my-full-tests.xml
.\.venv\Scripts\python.exe -m pytest tests\test_astronaut_ux_v101.py tests\test_management_v101.py -q
```

Se reutilizan dependencias existentes. Python>=3.11, FastAPI/Pydantic/SQLite/pytest/httpx; Windows DPAPI para demo protegida. Node sólo para DOM simulado (si falta, pytest lo declara omitido). No nuevas dependencias, descargas o pesos. Suite exacta y tiempos en RESULTS.json y XML. Las pruebas no son validación clínica. La inspección visual real falló al inicializar el kernel Computer Use, antes de abrir navegador; no sustituida por automatización alternativa. Checklist humano en MANUAL_VISUAL_QA.md. Voz física sigue pendiente; no se solicitó micrófono ni se cambió Ollama.

## Límites

Mediciones ausentes/invalidas/desactualizadas/contradictorias no significan normalidad. La tendencia y el requisito normativo no son diagnóstico. Fuentes y contramedidas proceden del catálogo previo; no se elevó su evidencia. Algunas fichas no estructuran condiciones/recursos: la vista declara esa limitación y no infiere hardware disponible. Cognición/inmunidad muestran datos/incertidumbre/biblioteca, sin nueva contramedida integrada. No se supone disponibilidad a bordo de DXA, laboratorio o pruebas terrestres. No hay pauta personalizada ni nuevas horas, dosis, ejercicios, umbrales o agenda de prevención.

La misión longitudinal usa recursos DECLARED_R2, no inventario NASA ni disponibilidad ficticia. Todas las intervenciones continúan AUTHORIZATION_REQUIRED/NO_VERIFIED_MISSION_POLICY y clinical_execution=BLOCKED. Datos históricos no se rellenan con inventario actual. Planes conocidos con fecha de revisión futura son planes, no eventos ya realizados. No se infiere cierre de un aviso antiguo por ausencia de datos.

SQLite/WAL/backups sin cifrado; DPAPI/ACL no aíslan procesos de la misma cuenta ni impiden manipulación por control del almacenamiento. Mantener datos sintéticos. Revisión médica pendiente de docs/v101/CLINICAL_REVIEW.md intacta. Integración opcional de Internet corresponde a otro integrante: ver OPTIONAL_INTERNET_RAG_CONTRACT.md, sólo documentación, sin código nuevo de red.

## Resultado real de cierre

692 pruebas aprobadas, cero fallos/errores/omisiones; 59 dirigidas aprobadas sobre assets finales. Cinco tests pytest nuevos contienen, entre otros, doce escenarios DOM simulados; no sumarlos de nuevo al total. Advertencia existente de deprecación Starlette/httpx. El último ajuste de navegación preventiva fue comprobado por la suite dirigida final después de aplicarse, sin cambios del motor Python/conocimiento durante la regresión.

26 checkpoints, 50 replays clínicos y 26 de monitorización correctos; auditoría válida; mismo hash semántico de misión que R2. Cinco checkpoints consultados por HTTP real, reader rechazado para escritura, cruce de checkpoint entre astronautas y origen externo rechazados. FULL/LOW_POWER/CRITICAL verificados en adaptador local offline, cero solicitudes al modelo y resultados clínicos sin cambio. No prueba de desconexión física/navegador ni validación de vuelo.

Cambio exacto: cinco archivos existentes modificados y tres nuevos de código/tests/herramienta; CHANGE_MANIFEST.json. Código recuperable en candidate-code-v101-ux.zip/CODE_FREEZE_UX.json, sin bases, credenciales o pesos. Requiere corpus/documentación original conservada; no es instalador autónomo. No restaurar sobre las carpetas R2/v1.0.1 congeladas. Backup privado original v1.0.1 en work/v101-ux/v101-db-backup y de esta demo en astronaut-db-backup, sin cifrado SQLite.

Estado: preparado para demostración e integración de investigación con datos sintéticos. Antes de presentar como experiencia verificada por una persona, completar MANUAL_VISUAL_QA.md y ensayo de cinco minutos. Revisión clínica/autoridad de misión, cifrado/aislamiento, voz física y recursos no estructurados siguen pendientes. No se añaden autorizaciones por aprobar tests.
