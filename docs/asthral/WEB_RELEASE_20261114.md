# ASTHRAL Web — cierre de integración browser-local (2026-11-14)

## Identidad y estado

El producto se llama **ASTHRAL** (Astronaut Support Tool for Health Risk Assessment and Logistics). `C:\Users\Gianni\Desktop\Vigile` se conserva como la ruta de trabajo histórica solicitada; no es el nombre vigente del producto. El paquete Python `vigile`, sus imports, identificadores de reglas y los documentos de investigación originales conservan esos nombres por compatibilidad y procedencia. La marca visible y la documentación nueva dicen ASTHRAL.

Esta entrega es un **prototipo de investigación** con escenarios y perfiles completamente sintéticos. No representa validación clínica, certificación de vuelo ni aceptación operacional.

## Verificación realizada

- Backend de referencia: **782 aprobadas, 0 fallidas**, una advertencia preexistente de deprecación Starlette/httpx, en 4367.46 s (1 h 12 min 47 s). Evidencia: `reports/backend-release-regression.txt`.
- Suite browser-local: **49 aprobadas, 0 fallidas**, 13.47 s. Incluye recarga de service worker con recursos precargados sin red, almacén cifrado, concurrencia, integridad, límites de retrieval y verificación WASM. Evidencia: `reports/browser-final-tests.txt`.
- Recorrido de interfaz en el preview de Cloudflare `https://browser-complete-release.asthral-web.pages.dev/` (release `b8ff15cb`): perfil sintético, evaluación DKA, persistencia cifrada y recarga con bloqueo del perfil; al desbloquear con la clave local de prueba, el historial y el resultado reaparecieron.
- Caso DKA sintético introducido en la interfaz: diabetes conocida, glucosa 180 mg/dL, beta-hidroxibutirato 4.2 mmol/L, pH venoso 7.22; bicarbonato, cetonas urinarias y potasio sin medir. Resultado observado: criterios DKA satisfechos, urgencia EMERGENCY, ninguna alternativa diagnóstica imprescindible pendiente; bicarbonato y cetonas urinarias se muestran como alternativas no medidas; potasio permanece como requisito de seguridad independiente y el protocolo está bloqueado. No hay ejecución terapéutica.
- La captura `screenshots/dka-alternatives-potassium-safety.jpg` registra la salida de interfaz. Las capturas auxiliares de viewport de móvil/tablet son emulación de Chromium, no dispositivos físicos.
- El propietario informó que la instalación offline funcionó en Samsung/Chrome con la URL `https://decec363.asthral-web.pages.dev/`, después de instalar recursos y apagar Wi-Fi en modo avión. Es aceptación reportada por el usuario, no instrumentación remota ni ensayo del preview posterior `b8ff15cb`. En pruebas automatizadas, el service worker también sirve el root y los recursos almacenados sin red.
- Inferencia local de Qwen3-4B en Chromium: una respuesta pasó el validador de referencia con TTFT 16.77 s, tiempo total 55.87 s y decodificación 1.9189 tokens/s. Es una observación de ese equipo/ejecución; no se extrapola a teléfonos. Datos: `reports/model-benchmarks-4b-accepted.json`.

## Publicación Git y Pages

- Repositorio privado del propietario: `https://github.com/GiaDiGr/ASTHRAL`.
- Commit publicado y verificado en `main` en el cierre previo: `af091dddf7038bd4ca9a9402d8a7ba1cdf6e661e` (`ASTHRAL: publish complete portable workspace`). El repositorio contenía 3222 archivos y el push fue aceptado.
- Preview de Cloudflare subido desde `web-local/dist`: `https://b8ff15cb.asthral-web.pages.dev/`; alias de rama: `https://browser-complete-release.asthral-web.pages.dev/`.
- Esta verificación no promovió el preview a producción estable. Persisten pruebas físicas y revisión independiente pendientes.
- `.gitignore` ya no tiene la regla amplia de denegar todo: incluye fuentes, investigación, documentación, fixtures y artefactos portables. Conserva exclusiones puntuales para credenciales, bases de datos/perfiles médicos locales, entornos instalados, secretos, logs y pesos/runtime de modelos grandes. No deben publicarse credenciales ni registros personales, incluso en repositorios privados. El manifiesto y las instrucciones permiten reinstalar los recursos excluidos en otra computadora.

## Límites y pendientes

- No se revisaron de forma clínica independiente las reglas o el resultado DKA; el caso comprueba consistencia de software con entradas sintéticas solamente.
- No hay promoción a producción estable ni aceptación humana completa de apariencia, accesibilidad y navegadores físicos.
- El Samsung reportado verifica desconexión para el preview `decec363`; repetir en el alias `b8ff15cb` si se requiere aceptación de esa versión.
- Micrófono/transcripción y TTS en navegador, Safari/iOS, batería/temperatura y rendimiento del 4B en móvil siguen sin aceptación física. La voz permanece experimental.
- La base SQLite del backend Windows continúa sin cifrado. El perfil browser-local cifra su serialización con AES-GCM, pero el navegador desbloqueado, el SO, extensiones y el mismo origen están fuera de esa protección. La auditoría hash-chain no impide reescritura por un atacante que controle el almacenamiento/código.
- No se incluyen credenciales, bases privadas, tokens, pesos de modelos de varios GB ni binarios de runtimes en Git. La copia del equipo nuevo debe recrear entornos y descargar los assets siguiendo los manifiestos versionados.

## Reproducción

En Windows, desde la raíz del checkout ASTHRAL:

```powershell
Set-Location engine
.\.venv\Scripts\python.exe -m pytest -q
Set-Location ..
$env:FAKE_INDEXEDDB_MODULE = 'file:///' + ((Resolve-Path 'work/browser-local/toolchain/node_modules/fake-indexeddb/build/esm/index.js').Path.Replace('\','/'))
& 'C:\Users\Gianni\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test web-local/tests/*.test.mjs
engine\.venv\Scripts\python.exe web-local\serve.py
```

La suite Python completa tarda más de una hora en el entorno del propietario. En un clon limpio, instalar primero las dependencias indicadas en `README.md`; el módulo `fake-indexeddb` se instala localmente en `web-local` para los tests de JavaScript. La demostración de interfaz local se abre en `http://127.0.0.1:8960/`.

## Artefactos de revisión

El paquete `artifacts/ASTHRAL_WEB_FINAL_REVIEW_20261114.zip` adjunta capturas verificables, resultados de suites, el caso sintético DKA y el benchmark local aceptado. No incluye perfiles cifrados ni credenciales.