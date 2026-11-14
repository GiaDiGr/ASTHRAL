# VIGILE 1.0.0 · investigación · revisión R2

Incremento sobre v0.11, conservando motor, misión de dos astronautas/54 días y Ollama `vigile-qwen3-4b:latest`. No hay validación clínica, operacional ni espacial ni ejecución terapéutica. **La prueba física de micrófono se interrumpió y sigue pendiente**; WAV→STT→asistente→TTS sí se ejecutó con motores reales. La inteligibilidad/naturalidad requiere valoración humana.

Resultados: 633 pruebas aprobadas (0 omitidas), 1 advertencia de deprecación Starlette/httpx; 26 ciclos, 50 evaluaciones, 76 replays actuales y 76 antiguos con su código archivado. Mismos hashes de solicitudes/resultados semánticos de la misión original. Dos pruebas usaron Vosk/SAPI reales; las demás pruebas de adaptador/Node se identifican como simuladas. Ver RESULTS.json, XML y e2e-r2/results.json.

Datos actuales: `engine/data/mission-v100-r2`. `mission-v100-final` conserva R1, no es la revisión actual. El ID `mission-v011` se mantiene porque se reutiliza la misma misión.

## Iniciar este equipo

PowerShell, terminal privada:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$py = '.\.venv\Scripts\python.exe'
& $py tools\setup_voice.py
# Sólo si Ollama NO está ya escuchando en 8891:
& $py tools\start_ollama_vigile.py
& $py -m vigile.product_demo serve --output data\mission-v100-r2
```

Portal http://127.0.0.1:8898/ y backend http://127.0.0.1:8897/health. El supervisor rechaza puertos ocupados; Ctrl+C detiene sólo sus hijos. No cambiar Norton ni restaurar cuarentena. No ejecutar otro launcher si Ollama está activo.

Obtener el código del portal en otra terminal privada, sin escribirlo en informes/archivos/chat:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
.\.venv\Scripts\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/mission-v100-r2/portal-access.txt'))"
```

No poner tokens reader/acquisition en el navegador. Los secretos DPAPI son de esta cuenta y se regeneran al preparar otra misión.

## Demostración reproducible y pruebas

Usar salidas NUEVAS:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$py = '.\.venv\Scripts\python.exe'
& $py -m pytest -q --junitxml=..\work\v100\my-tests.xml
& $py -m vigile.product_demo prepare --output data\mission-v100-my-demo --seed 42
& $py ..\work\v100\evaluate_product_voice.py data\mission-v100-my-demo ..\work\v100\my-voice-results
& $py -m vigile.product_demo serve --output data\mission-v100-my-demo
```

La preparación y 76 replays no necesitan Ollama. El harness oral usa modelos reales y guarda WAV sintéticos explícitamente: revisa el transcript contra una referencia antes de enviarlo; **no es autocorrección del producto ni prueba de micrófono físico**. El runtime no conserva grabaciones por defecto. Seleccionar idioma, pulsar Hablar, terminar, revisar/editar y enviar manualmente; reproducir sólo por botón. Conservar texto ante cualquier fallo.

**No ejecutar nuevamente evaluate_reserved_once.py**. El banco se utilizó UNA vez tras congelar R1. R2 contiene correcciones posteriores y no tiene un banco ciego inédito. RESERVED_USED.json y resultados completos preservan la procedencia.

## Equipo compatible nuevo

Windows y Python 3.13 probado (declarado >=3.11), System.Speech/.NET Framework y voces locales Microsoft David Desktop EN/Helena Desktop ES ya instaladas; navegador con getUserMedia/AudioWorklet en localhost, micrófono y salida. No se cambia configuración global automáticamente.

Durante instalación con red autorizada:

```powershell
Set-Location engine
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-v100.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e ".[integration,test,voice]"
# Descarga EXPLÍCITA de dos Vosk Apache-2.0 (~81 MB decimales comprimidos):
.\.venv\Scripts\python.exe tools\setup_voice.py --download-models
.\.venv\Scripts\python.exe -m vigile.product_demo prepare --output data\mission-local --seed 42
```

Para instalar sin red, preparar antes wheelhouse compatible completo (incluyendo build de srt, que aquí se construyó desde fuente) y modelos verificados; usar pip --no-index --find-links. El paquete no incluye Python, Windows/vozes, Ollama ni pesos Qwen/Vosk: **no es instalador autosuficiente**. Provisionar Ollama y modelo exacto por separado con licencias/canales autorizados, endpoint loopback 8891 y alias indicado; no usar antiguos descargadores llama.cpp ni cuarentena. No se promete generación Qwen bit a bit entre hardware/runtimes.

## Entrega

AUDIT.md: hallazgos, cobertura, seguridad y dictamen. VOICE_AND_AI.md: métricas/licencias/limitaciones. INTEGRATION_CONTRACTS.md y OpenAPI: interfaces. DEMO.md y HUMAN_REVIEW.md: guion/revisión independiente. RESULTS.json y trazas: resultados reales. CANDIDATE_R1_FREEZE.json/R2_FREEZE.json y changes.json: hashes/procedencia. VIGILE_v100_START_HERE.md: entrada del equipo.