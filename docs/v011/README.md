# VIGILE v0.11 — Ejecutar y verificar

Requisitos comprobados: Windows, Python 3.13.16 en engine/.venv, FastAPI 0.143.1, Pydantic 2.14.1, Uvicorn 0.54.0, httpx 0.28.1 y pytest 9.1.1. El proyecto declara Python >=3.11, pero esta entrega se ejecutó con 3.13. DPAPI/ACL de la preparación requieren Windows. No se instalaron nuevas dependencias. Una instalación nueva usa los extras `.[integration,test]`; guardar wheels previamente si se necesita instalar sin conexión. SQLCipher no está disponible.

Desde PowerShell:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$py = '.\.venv\Scripts\python.exe'
# Iniciar la base ya verificada. Si 8897/8898 ya están activos, no ejecutar otra instancia.
& $py -m vigile.mission_demo serve --output data\mission-v011-final
```

Abrir http://127.0.0.1:8898/; backend http://127.0.0.1:8897/health. Los servicios anteriores 8895/8896 se conservan. Ctrl+C detiene sólo los dos hijos del supervisor de misión. El launcher rechaza puertos ocupados y no mata procesos ajenos.

En otra terminal privada, consultar el código del **portal nuevo**, sin escribirlo en archivos ni informes:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/mission-v011-final/portal-access.txt'))"
```

No introducir el token reader en el navegador ni credenciales en el chat del modelo. DPAPI vincula estos archivos a la cuenta Windows actual; no son un mecanismo de distribución de claves al equipo.

## Repetir la demostración completa

El directorio de salida debe ser **nuevo**. No sobrescribir bases previas. Estos comandos no necesitan Ollama ni red externa:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$py = '.\.venv\Scripts\python.exe'
& $py -m vigile.mission_demo run --output data\mission-v011-repeat-42 --seed 42 --model-config data\portal-v0100-integrated\portal-config.json
& $py -m vigile.mission_review --output data\mission-v011-repeat-42 --report ..\docs\v011\my-offline-review.json
```

run crea la base, adquiere muestras por API, calcula baselines, ejecuta 26 ciclos, captura historia y comprueba 76 replays. Sólo copia configuración pública de modelo de --model-config, **ninguna credencial histórica**. Genera cuatro secretos nuevos DPAPI, ACL, mission-report.json, summary.json y openapi.json. El directorio existente produce error deliberado. Para servir la repetición, detener antes el supervisor de 8897/8898 y cambiar --output; la carpeta final queda intacta.

Integración real opcional con el Ollama ya existente, sin reconfigurarlo:

```powershell
& $py -m vigile.mission_review --output data\mission-v011-final --report ..\docs\v011\my-real-review.json --real-inference
```

El archivo de informe también debe ser nuevo. Ocho preguntas y comparación de modos, sin banco reservado. Fallos/rechazos se registran; aceptar generación no es un requisito clínico. La indisponibilidad se inyecta en el adaptador, no deteniendo Ollama.

## Suite y protección

```powershell
& $py -m pytest -q --basetemp=..\work\v011\pytest-my-verification --junitxml=..\docs\v011\my-tests.xml
# Verificar el anclaje final (su prefijo permanece válido si se añaden auditorías):
& $py -m vigile.local_protection verify-anchor --database data\mission-v011-final\vigile.sqlite3 --anchor "$env:LOCALAPPDATA\Vigile\integrity\mission-v011-final.anchor.json" --key "$env:LOCALAPPDATA\Vigile\integrity\audit-key.dpapi"
```

Usar una carpeta nueva para --basetemp: pytest administra ese directorio. No apuntarlo a documentación o bases.

Copias verificadas: engine/data/backups/mission-v011-final y mission-v011-final-restored. SQLite/WAL/copias no están cifrados. DPAPI/ACL no aíslan procesos de la misma cuenta; HMAC no resiste control conjunto de almacenamiento/código/clave.

## Estructura y equipo

- engine/vigile/mission_demo.py: CLI y orquestación mediante motores existentes.
- mission_context.py: fases sintéticas append-only; mission_frames.py: checkpoints de recepción.
- mission_review.py: revisión reader y preguntas/modes, sin autoridad clínica.
- inference_failures.py: clasificación pública acotada de fallos.
- dashboard_api.py, portal.py, security.py y web/: contratos/vistas históricas y controles de contexto.
- monitoring.py, clinical_engine.py, service.py: resolución y congelación del contexto de misión; criterios sin cambios.
- engine/tests/test_mission_v011.py: 21 pruebas nuevas, además de las 561 anteriores.
- docs/v011: informes A/B, contratos, guion, resultados reales, OpenAPI, capturas y manifiesto.

INTEGRATION_CONTRACTS.md asigna interfaces a cada integrante. No copiar secretos, base ni modelos a un repositorio público. El ZIP es código/paquete de revisión, no instalador completo ni corpus/modelo redistribuido. Conservar la versión de código para los replays.

## CONTEXTO PARA CONTINUAR CON CHATGPT

Versión 0.11.0 implementada sobre 0.10, sin nuevas enfermedades ni terapias. Base final nueva mission-v011-final, servicios 8897/8898, Ollama 8891/modelo vigile-qwen3-4b:latest. 0.10 permanece en 8895/8896 con código archivado y 39 replays verificados. Misión de 54 días/2 astronautas: 26 ciclos, 50 evaluaciones, 6 baselines, 129 medidas, 17 dispositivos ficticios; 76 replays coincidentes. Semilla 42 reproduce solicitudes y vector semántico, no UUID/credenciales/auditoría binarios. Frames congelan conocimiento recibido; contextos versionan fases bajo la misma misión. DKA mantiene alternativas OR no bloqueantes y potasio de seguridad separado. Causas del fallback son explícitas; no se relajaron guards. Entrega: 582 pruebas aprobadas, una advertencia Starlette/httpx. RESULTS.json contiene hashes y resultados medidos de modelos/modos/rendimiento. SQLite/backups sin cifrar, procesos de misma cuenta sin aislamiento y HMAC falsificable si clave/código/almacenamiento se comprometen. Pendientes: revisión clínica y de seguridad independientes, cifrado/migración, aislamiento, retención de snapshots y evaluación separada de explicaciones. No interpretar pruebas de software como validación clínica, operativa o espacial.