> Configuración vigente tras la corrección de consistencia: [CONSISTENCY_AUDIT.md](CONSISTENCY_AUDIT.md). Usar `portal-consistency-v061`; los comandos previos con `portal-v06-final` corresponden a la demostración histórica conservada.

# Recuperación de la IA local — 19/10/2026

La captura del usuario confirmó que Norton puso `llama-server` en cuarentena como `IDP.Generic`, mediante protección comportamental. No se determinó si era un falso positivo. No se restauró ese ejecutable, no se añadieron exclusiones y no se desactivó Norton.

Se instaló una distribución portátil oficial alternativa, Ollama v0.40.6. El ZIP coincide con el SHA256 publicado por GitHub: `e359637575302f288d76c0007c408a4be9c7376d59c4f28684d63b232a44b427`. Windows informó `Valid` para la firma Authenticode de `ollama.exe`. Esto verifica procedencia/integridad, no garantiza ausencia de vulnerabilidades.

Se reutilizó el GGUF Qwen3-4B-Instruct-2507 Q4_K_M existente. No se descargaron nuevos pesos. La importación creó una copia del modelo en `engine/local_ai/ollama-models`. Alias local: `vigile-qwen3-4b:latest`. Configuración: `OLLAMA_NO_CLOUD=1`, `OLLAMA_HOST=127.0.0.1:8891`. El log confirma cloud deshabilitado.

## Cambios

- `engine/tools/start_ollama_vigile.py`: arranque portátil sin descargas ni cambios globales; rechaza puertos ocupados y ejecutables ausentes.
- `engine/data/portal-v06-final/portal-config.json`: proveedor `ollama`, puerto 8891, alias con `:latest`, modo FULL; retirada la clave específica de llama.cpp. Respaldo `portal-config.before-ollama.json`.
- No se modificó ningún archivo de `engine/vigile`, reglas clínicas ni investigación. Se conservan la base de demostración y sus hashes reproducibles.

## Verificación

- Suite: **298 passed, 1 warning**, 46,39 s. La advertencia corresponde a la deprecación Starlette/httpx.
- Inferencia real inicial correcta. Primer arranque/carga: unos 93 s; no es una medida de latencia estable.
- Portal real: FULL `ANSWERED` en 8352 ms; LOW_POWER `ANSWERED` en 8175 ms. Una consulta sintética por modo; no son percentiles ni una evaluación clínica.
- CRITICAL: respuesta extractiva sin inferencia. Cambiar a CRITICAL no garantiza descargar de GPU un modelo previamente cargado; Ollama usa el tiempo de residencia de la solicitud anterior.
- Reader no puede escribir; acceso fuera de ámbito y Origin externo rechazados; modo inválido rechazado. Cuatro evaluaciones reproducidas y registros sin cambios. Detalles en `ollama-recovery-verification.json`.
- Runtime detenido y arrancado nuevamente, con ejecutable disponible. Esta comprobación puntual no garantiza que futuras actualizaciones del antivirus no lo bloqueen.

## Arranque después de reiniciar el equipo

Ejecutar desde PowerShell. No repetir los comandos de servidor si sus puertos ya están ocupados.

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe .\tools\start_ollama_vigile.py
```

En otra terminal, mantener el backend abierto:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir .\data\portal-v06-final --port 8895
```

En una tercera terminal, mantener el portal abierto:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile.portal --config .\data\portal-v06-final\portal-config.json --port 8896
```

Abrir http://127.0.0.1:8896/ . El código del portal está en `engine/data/portal-v06-final/portal-access.txt`; nunca introducir el token reader en el navegador. Seleccionar FULL y consultar los datos faltantes de la evaluación sintética. Para verificar pruebas:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
```

## Límites y seguridad

Ollama escucha sólo en loopback, pero su API local no exige la clave del antiguo llama.cpp. Otros procesos de la misma máquina pueden acceder al runtime: se requiere aislamiento del proceso/cuenta para un despliegue serio. No compartir el puerto por LAN ni proxy público. La configuración cloud no equivale a un aislamiento de red impuesto por firewall. No se ha certificado ausencia absoluta de tráfico de red del proveedor.

La cuenta reader y las sesiones del portal conservan sus controles. SQLite permanece sin cifrado; un atacante con control del almacenamiento puede manipular registros y recalcular una cadena de auditoría sin anclaje externo. El asistente puede equivocarse incluso pasando comprobaciones semánticas; se mantienen evidencia, fallbacks y separación de la autoridad determinista. Las pruebas sintéticas no constituyen validación clínica u operativa. Las referencias anteriores a llama.cpp en DELIVERY.md son históricas; este documento establece la configuración vigente.

Fuentes oficiales: https://github.com/ollama/ollama/releases/tag/v0.40.6 ; https://docs.ollama.com/windows ; https://docs.ollama.com/import ; https://docs.ollama.com/faq

## CONTEXTO PARA CONTINUAR CON CHATGPT

VIGILE v0.6 recuperado mediante Ollama portátil v0.40.6, sin modificar el motor. Backend 8895, portal 8896, runtime 8891, todos loopback. Modelo local `vigile-qwen3-4b:latest`; biblioteca y DB v06-final existentes. Mantener Norton activo y la cuarentena antigua. No ejecutar el instalador/launcher antiguo para restaurar llama-server. Los módulos externos usan los contratos reader existentes; el navegador se conecta al portal y no recibe credenciales backend. Prioridades pendientes: aislamiento de procesos, análisis de la detección original por el proveedor si se desea reutilizar llama.cpp, mediciones de rendimiento prolongadas, evaluación adversarial de respuestas y validación biomédica independiente.
