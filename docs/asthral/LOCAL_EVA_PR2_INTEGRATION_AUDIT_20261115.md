# ASTHRAL — Auditoría local de EVA PR #2 e integración

**Fecha:** 2026-11-15

**Checkout:** `C:\Users\Gianni\Documents\Codex\ASTHRAL_AUTONOMOUS_MISSION_20261115`

**Rama / HEAD al iniciar:** `feature/asthral-autonomous-mission` / `256fef85`

## Resultado del PR #2

No fue posible leer el PR `https://github.com/GiaDiGr/ASTHRAL/pull/2` desde esta sesión. GitHub devolvió HTTP 404 para la página, `.patch` y `.diff`; el endpoint de archivos no fue accesible y el lector de diagnósticos conectado de Codex devolvió `GitHub could not complete the request`. El checkout local no contiene `refs/pull/2`; tampoco apareció un commit local visible que identifique a Marfe o a EVA.

Esto significa que **no se verificaron los commits, autores, archivos ni funcionalidades del PR**. No importé código ni atribuí a Marfe una implementación que no pude inspeccionar. Por tanto, Start EVA, las cuatro tarjetas, los escenarios de alerta EVA, la finalización de EVA y su reporte médico continúan **sin verificar y sin integrar**. En el frontend local tampoco existe actualmente un botón `Start EVA` ni esas cuatro tarjetas. La búsqueda y recuperación documental, el seguimiento clínico y el resumen sintético existente no sustituyen un reporte médico de EVA.

No ejecuté `fetch`, `pull`, `merge`, `commit` ni `push`. Para completar la integración fielmente se necesita que esta sesión pueda leer el PR o que se adjunte el diff/los archivos del PR. El siguiente pase deberá registrar los SHA de los commits, la lista exacta de archivos y la atribución original antes de incorporar solamente los componentes que no dupliquen servicios locales.

## Servicios locales que debe reutilizar la integración

- `web-local/src/experience.js` contiene el monitor determinista, registro, episodios y seguimiento, resumen agregado sintético y edición temporal del contexto de misión.
- `web-local/src/mission-support.js` contiene prevención/recuperación, radiación, NASA CCMC DONKI, caché pública y avisos con reconocimiento local.
- El navegador usa el mismo perfil e historial local. Los eventos DONKI son contexto público, no una medición de dosis personal ni una alerta operacional de tripulación.
- La exportación agregada actual se restringe a datos sintéticos del demo. El backup persistente contiene datos cifrados; ninguno de los dos es un reporte clínico de EVA.

## Hallazgo en el servidor local y reproducción

El primer E2E contra `127.0.0.1:8952` no llegó a exportar el resumen porque ese servidor entrega un build antiguo. Su `index.html` coincide con la fuente actual, pero `app.js` coincide con `build-output-explicit-energy-*`, no con el código actual, y `mission-summary.js` devuelve 404. El flujo paró al buscar el botón de exportación; no hubo error de página, consola ni solicitudes registradas por ese intento. No detuve ni modifiqué el servidor preexistente.

Para verificar la fuente actual generé un directorio nuevo, sin reemplazar builds anteriores:

`web-local/build-output-eva-integration-review-20261115`

El build reportó **107 archivos / 140.710.182 bytes**, 254 casos de paridad y módulos clínicos `BYTE_IDENTICAL`. Serví ese directorio en loopback `127.0.0.1:8953` y comparé los bytes servidos con la fuente para `index.html`, `app.js`, `experience.js`, `mission-summary.js` y `mission-support.js`; los cinco fueron idénticos.

## Verificaciones de esta ejecución

Los escenarios de navegador usaron perfiles efímeros y datos sintéticos. No se usaron datos médicos reales. Ningún resultado de software constituye validación clínica, operacional o de vuelo.

| Verificación | Resultado real | Límite |
|---|---|---|
| Pytest completo | **947 aprobadas, 19 omitidas, 0 fallidas**, 221,74 s. Una advertencia de obsolescencia Starlette/httpx. | Omitidas: 2 por falta de `argon2`; 13 por falta de `cv2`; 2 por falta de `torch`; 2 por dependencias nativas de voz ausentes. |
| Node completo | **99 aprobadas, 0 fallidas, 0 omitidas**, 11,63 s. | Permanecen avisos `MODULE_TYPELESS_PACKAGE_JSON` por módulos ES importados desde un paquete sin `type: module`. |
| Flujo sintético de misión en navegador | `SYNTHETIC_CROSS_MODULE_MISSION_FLOW_FOLLOWUP_AND_ENCRYPTED_EXPORT_PASSED`; **14 pasos**, 35,255 s, runtime Python listo en 13,281 s. Sin errores de página/consola ni solicitudes fallidas. | Verifica el flujo de misión existente; no incluye EVA. Reporte: `work/browser-mission-isolated-build-20261115/report.json`. |
| NeuroGuard | `SYNTHETIC_NEUROGUARD_BROWSER_FLOW_PASSED`; 9 comprobaciones, sin errores de página/consola/solicitudes. | Autoinforme y tareas experimentales sintéticas; no diagnóstico. `work/browser-neuroguard-pr2-audit-20261115/report.json`. |
| MotionGuard | `GENUINE_INFERENCE_EXECUTED_NOT_BIOMECHANICAL_VALIDATION`; modelo Pose Landmarker Lite 0.10.21 ejecutado con CPU sobre 3 clips. Wall-push: **24/25** ángulos válidos; knee-pushups: **33/75**; squat: **0/26**, estado `INSUFFICIENT_TRACKING`. | No hay ground truth. El squat no produce ángulos ni ciclos; no se elevaron umbrales ni se infirió una medición. `work/browser-pose-pr2-audit-20261115/report.json`. |
| Offline | `PUBLIC_CACHE_OFFLINE_RELOAD_AND_LEXICAL_RETRIEVAL_VERIFIED`; **76 archivos** verificados, recarga desconectada y recuperación local de citas; runtime listo en 2,17 s. | La persistencia del navegador puede ser desalojada; no se probó restauración de perfil personal. `work/browser-offline-pr2-audit-20261115/report.json`. |
| Voz offline | Vosk quedó `READY`. Cinco de seis audios sintéticos coincidieron; el caso de sueño se transcribió como “a seven hours” en vez de “as seven hours”, quedó `unresolved` y no se guardó. Todos los casos reportan `record_saved: false`. | Reconocimiento no perfecto; no se cambió el parser para adivinar la intención. Estado: `RECOGNITION_EXECUTED_REVIEW_MISMATCHES`. `work/browser-voice-pr2-audit-20261115/report.json`. |
| SLM generativo | `BLOCKED_NO_WEBGPU_ADAPTER`; no existe adaptador WebGPU en Chromium headless y el botón de carga permaneció deshabilitado. | No se descargó ni simuló generación. El motor determinista y RAG funcionan por separado. `work/browser-model-pr2-audit-context/work/browser-model-acceptance/report.json`. |
| DONKI | `PUBLIC_EVENT_SYNC_ACK_RELOAD_VERIFIED`; 40 eventos públicos, 0 problemas reportados por el adaptador, avisos no reconocidos 29→28 y reconocimiento persistido tras recarga. | La telemetría de Playwright también registró dos solicitudes `ERR_ABORTED` (CME y notifications); deben considerarse aparte del contador de errores del adaptador. No es exposición individual ni escenario EVA. `work/browser-donki-pr2-audit-context/work/browser-donki-acceptance/report.json`. |
| Aceptación general del frontend | `PARTIAL_WORKFLOW_PASSED_NOT_FULL_ACCEPTANCE`; ejercicio, selección USDA, nutrición/hidratación y navegación de sueño, bienestar, clima espacial, radiación, evaluación e historial pasaron; sin errores de página/consola/solicitudes. | El script se declara parcial, no aceptación completa. `work/browser-acceptance-pr2-audit-20261115/report.json`. |

La misión de 14 pasos verificó baseline, replay determinista, ejercicio pausado/reanudado/completado, KSS, radiación sintética, seguimiento pendiente, resumen sintético agregado, contexto de microgravedad, citas locales con hash, fixture DONKI histórico y backup cifrado vacío. El resumen contenía 5 mediciones sintéticas, 1 baseline, 1 ciclo de monitorización, 2 seguimientos, 10 entradas preventivas y 3 filas de radiación, sin identificadores ni valores clínicos.

## Corrección del harness de voz

`tools/browser_voice_acceptance.py` antes aceptaba únicamente una URL posicional y escribía siempre en `work/browser-voice-acceptance`. El primer intento con `--output` no fue reconocido y reemplazó el informe existente con un error de navegación. Corregí el harness para admitir `--url` y `--output`, mantener la URL posicional heredada y rechazar directorios de salida no vacíos. Después ejecuté la prueba correctamente en una carpeta nueva y regeneré `work/browser-voice-acceptance/report.json` y `actual-state.png` con el resultado válido más reciente. No encontré otra copia local del informe anterior para restaurar sus tiempos exactos; la evidencia regenerada preserva el resultado funcional actual.

## Pendientes prioritarios

1. Obtener acceso de lectura al PR #2 o recibir su diff; inspeccionar SHA, autoría, archivos, pruebas y licencia antes de editar el código EVA.
2. Integrar EVA en el contexto de misión reutilizando baseline, registro, DONKI/avisos y reporte existentes, sin duplicar persistencia ni convertir clima espacial en dosimetría personal.
3. Añadir y ejecutar aceptación específica de Start EVA, cuatro tarjetas, escenarios sintéticos, finalización y reporte de EVA una vez conocida la implementación original.
4. Investigar el tracking insuficiente de los clips de MotionGuard con videos y referencias apropiadas; mantener abstención mientras no haya datos de referencia.
5. Resolver o documentar el error de transcripción de sueño con evidencia de voz y conservar revisión humana; probar el generador local solamente en un navegador/dispositivo que ofrezca WebGPU o con una ruta CPU real verificada.
6. Reproducir los E2E desde el build aislado, no desde el servidor antiguo en `8952`.

## Cambios y límites

El único archivo de código editado en esta continuación es `tools/browser_voice_acceptance.py`. Se añadieron el build aislado, informes y capturas en rutas nuevas `work/` y se regeneró el informe de voz canónico indicado arriba. Los cambios sucios previos se conservaron, excepto `work/browser-voice-acceptance/report.json` y `actual-state.png`, que fueron regenerados después del error del harness; no fue posible recuperar sus bytes anteriores. No se modificaron criterios médicos, protocolos, Ollama, Norton ni servicios remotos. No se hizo ninguna publicación.

El build local verificado queda disponible en `http://127.0.0.1:8953/` mientras el servidor de prueba permanezca activo. No constituye una versión con EVA integrada.

## Reproducción local

Desde la raíz del checkout, con los entornos que se usaron para esta ejecución:

```powershell
$enginePython = 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe'
$browserPython = 'C:\Users\Gianni\AppData\Local\Programs\Python\Python313\python.exe'
$node = 'C:\Users\Gianni\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'

& $enginePython -m pytest engine\tests -q -rs
& $node --test web-local\tests\*.test.mjs

$env:ASTHRAL_BUILD_OUTPUT = Join-Path (Get-Location) 'web-local\build-output-eva-integration-rerun-20261115'
& $enginePython web-local\build.py
& $browserPython tools\serve_browser_build.py $env:ASTHRAL_BUILD_OUTPUT --port 8953
```

En otra consola, para repetir los recorridos de navegador sin reemplazar estos informes, use una carpeta de salida nueva en cada ejecución:

```powershell
& $browserPython tools\browser_mission_integration_acceptance.py `
  --url http://127.0.0.1:8953/ `
  --output work\browser-mission-next-run

& $browserPython tools\browser_voice_acceptance.py `
  --url http://127.0.0.1:8953/ `
  --output work\browser-voice-next-run
```
