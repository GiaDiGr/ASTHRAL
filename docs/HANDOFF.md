# VIGILE 0.3.0 — entrega de integración NASA Space Apps

Fecha: 2026-10-15, America/Lima. Proyecto: `C:\Users\Gianni\Desktop\Vigile`. Se conserva el motor existente; no se construyó frontend ni LLM. Todos los datos de la demostración son sintéticos. Esta entrega verifica software: **no valida clínica ni operación espacial**.

## Resultado y pruebas

- Baseline antes de cambios: 157/157 pruebas.
- Suite final: **172/172**, cero fallos; 15 pruebas nuevas, incluidas dos recorridos end-to-end (TestClient y servidor HTTP real), repetición en bases nuevas, adaptador, control de acceso y bloqueo de red externa. JUnit: `docs/integration-tests.xml`.
- Advertencia restante: Starlette/TestClient depreca httpx; no se ocultó ni cambió una dependencia para silenciarla.
- La demostración registra **38 mediciones, dos baselines, dos tendencias, 12 hallazgos y dos episodios**; prueba coocurrencia MSI06, seguimiento, auditoría y replay.
- Siete evaluaciones permanecen INCONCLUSIVE: cobertura temporal incompleta, fase incompatible, NOT_MEASURED, INVALID, calibración expirada, unidad incompatible y fuera de rango técnico.
- Tres comparadores originales ejercitados: AER-003 (retención aeróbica), MUS-002 (retención de fuerza), ENV-002 (promedio horario CO2). El resultado REQUIREMENT_NOT_MET se conserva como incumplimiento normativo sintético, no enfermedad ni severidad clínica.
- OPERATIONAL continúa REQUIRES_VALIDATION; solicitudes de tratamiento siguen sin ejecutarse, incluso con un authorization_id declarado por el cliente.
- Cliente reader externo: 12 resultados autorizados, siete inconclusos, sin datos crudos ni acceso de escritura. Frontend de ejemplo consulta registros y verifica replay después de reiniciar el servidor real.
- Misma semilla y mismo código/corpus producen el mismo dataset y los mismos IDs de hallazgos deterministas en bases nuevas. Timestamps de auditoría, UUIDs de registros auxiliares, tokens y rendimiento NO son reproducibles bit a bit.
- `pip check`: sin conflictos. 106 originales conservan sus hashes; archivo del código v0.2 en `work/releases/v0.2.0-before-integration.zip`.

## Comandos exactos

Abrir PowerShell, sin necesidad de activar el entorno:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile integration-demo --seed 42
```

El segundo comando ejecuta la demostración completa: genera fixtures, inicia Uvicorn en un puerto loopback libre, ingresa datos mediante HTTP, evalúa, consulta como reader, mide recursos, cierra ordenadamente y reabre SQLite para verificar persistencia/auditoría. Imprime la carpeta nueva bajo `engine/data/integration-runs/<id>`. No modifica la base principal ni deja el servidor activo. `--output <carpeta_nueva>` permite elegir destino; **rechaza un destino existente** para no sobrescribir datos ni credenciales.

Para generar solo el dataset sin escribir archivos:

```powershell
& .\.venv\Scripts\python.exe -m vigile simulate --seed 42
```

Para guardarlo, usar un nombre nuevo:

```powershell
& .\.venv\Scripts\python.exe -m vigile simulate --seed 123 --output data\synthetic-seed123.json
```

La demo de entrega ya está persistida en `engine/data/spaceapps-demo`. Para conectar los módulos al mismo conjunto:

```powershell
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir data\spaceapps-demo --port 8765
```

En otra consola, desde engine:

```powershell
& .\.venv\Scripts\python.exe examples\reader_client.py --token-file data\spaceapps-demo\reader-token.txt
& .\.venv\Scripts\python.exe examples\frontend_client.py --token-file data\spaceapps-demo\frontend-token.txt
```

Ambos clientes usan http://127.0.0.1:8765. Detener el servidor con Ctrl+C. Para la base principal, usar `python -m vigile serve --port 8765` sin integration-dir. `init` sigue disponible; no hay migración destructiva del esquema SQLite 1.

## Simulador y adaptador

`vigile/simulator.py`: `generate(seed)` retorna `SyntheticDataset` de esquema `vigile.synthetic.v1`. Fecha de origen fija 2025-01-01 UTC, seed configurable, datos sintéticos explícitos. Incluye preflight, adaptación, trayectorias longitudinales en microgravedad, postflight, fuerza/VO2 y ambiente, ausencias, inválidos, calibración defectuosa y unidades/rangos incorrectos. Las curvas, rangos técnicos, ventanas y parámetros estadísticos son elecciones de fixtures, no protocolos ni modelos fisiológicos. No presupone que los instrumentos declarados existan a bordo.

La misión persistida es un contexto inmutable IN_MISSION/MICROGRAVITY. Las mediciones conservan su propia fase; preflight se usa para baseline y postflight para descripción. Intentar evaluar una medida postflight con el contexto in-flight queda inconcluso. No se cambia silenciosamente la misión ni se certifica recuperación. El versionado de contexto de misión será un trabajo posterior.

`vigile/adapters.py`: interfaz `MeasurementSource.measurements() -> Iterable[Measurement]`. El contrato de entrega estable es `POST /measurements` con el modelo Measurement/OpenAPI; futuros sensores, archivos y servicios deben transformarse a ese modelo conservando procedencia/calidad. El adaptador funcional `SyntheticAdapter` valida por completo el envelope (referencias, duplicados, synthetic, versión) antes de enviar datos. Mantiene las mediciones inválidas para probar gates, sin limpiarlas ni imputarlas. Archivo máximo 10 MiB y 10000 mediciones; API máximo 1 MiB por solicitud.

Importación contra una base preparada para recibir IDs nuevos:

```powershell
& .\.venv\Scripts\python.exe -m vigile import-synthetic --dataset examples\synthetic-seed42.json --url http://127.0.0.1:8765 --token-file C:\ruta\privada\token-researcher.txt
```

El archivo de token debe contener solo un secreto researcher/clinician previamente aprovisionado por el administrador. **No usar reader ni entregar ese archivo al RAG.** El importador registra misión, perfil y dispositivos, por lo que necesita ese rol de preparación; un sensor que envíe únicamente observaciones debe usar operator con alcance restringido. No reimportar los mismos IDs: respuesta 409. La importación no es una transacción global; ante fallo se detiene y puede dejar un prefijo persistido. No hay reintentos automáticos de POST, promesa de exactly-once ni sustitución de datos. Revisar recibos/IDs antes de recuperar una importación parcial.

`LocalClient` usa HTTPX instalado, conexión persistente, sin proxies heredados ni redirects; exige URL http con host literal 127.0.0.1. No reenvía credenciales fuera de loopback. Transcripción desactivada por defecto; la demo la activa únicamente para fixtures. No usar ese mecanismo de transcripción con datos personales.

## Contrato frontend

| Necesidad | Ruta y semántica |
|---|---|
| Astronauta | GET /profiles?mission_id=sim-mission; GET /profiles/sim-crew. Perfil mínimo id/misión/synthetic, sin demografía inventada. |
| Mediciones | GET /measurements?subject_id=sim-crew&mission_id=sim-mission&limit=100; quality de ingestión no sustituye la reevaluación a as_of. |
| Baselines | GET /baselines?subject_id=...&mission_id=...; GET /baselines/{id}/status?as_of=... devuelve disponibilidad, retirada o expiración. La lista es histórica. |
| Tendencias | GET /trends?subject_id=...&mission_id=...; detalle /research-records/trend/{id}. Pendiente y z son descriptivos. |
| Hallazgos | GET /findings?... y /findings/{id}; explanation reejecuta bundle solo con versión compatible. |
| Episodios/rutas | GET /episodes?...; /episodes/{id}/pathway; /capabilities/coverage. Cobertura documental no es detector clínico. |
| Seguimiento | GET /followups/{id}/status?as_of=...; SCHEDULED/OVERDUE/COMPLETED_BY_HUMAN no determina recuperación clínica. |

Mostrar por separado medición, calidad, incumplimiento normativo, observación humana, hipótesis y diagnóstico bloqueado. Alertas solo como presentación del estado/result/reason existente, nunca gravedad, diagnóstico o umbral creados por UI. INCONCLUSIVE no es normalidad y datos retirados no deben mostrarse como baseline activo. Hay paginación limitada de mediciones/RAG, no general.

`frontend-token.txt` es operator con alcance sim-crew/sim-mission. El ejemplo solo hace GET, pero **ese token también permite registrar mediciones/perfiles según el contrato existente**: es un secreto de integración, no una credencial pública. Usar un backend intermediario o almacenamiento seguro y aprovisionamiento por usuario al integrar la UI. No ponerlo en código, repositorio, URL o LLM. No hay rol dashboard de lectura completa separado. No se habilitó CORS: para navegador usar backend del mismo origen/proxy local; no agregar Allow-Origin:* ni abrir el servicio a la red por defecto.

## Contrato LLM/RAG offline

Solo token reader individual con subject_ids/mission_ids asignados en servidor. Endpoints: GET /rag/findings?subject_id=...&mission_id=... y /rag/findings/{id}; catálogos, /rules, /evidence/{id}, /evidence/rules/{id}, /evidence-issues, /capabilities/coverage. Las respuestas minimizadas incluyen estado, razón y referencias existentes; no datos crudos, notas, identidad del sujeto, dispositivos o bundle. Aun minimizadas, son datos autorizados que requieren protección.

El RAG explica esas decisiones y sus limitaciones; no evalúa reglas por cuenta propia, no completa datos faltantes, no convierte un incumplimiento en diagnóstico ni modifica autorización. Texto documental es dato no confiable, no instrucción de sistema. Reader no accede a /profiles, /measurements ni /findings completos y todo POST se deniega. No hay credenciales write en `reader_client.py` ni en sus respuestas. Proporcionar **solo reader-token.txt** a un proceso bajo una identidad OS independiente; no montar la carpeta completa de integración, la base, el código ejecutable ni los otros secretos. Todavía no hay implementación de LLM/RAG.

## Ejemplos de solicitudes/respuestas

Archivo completo, sin headers secretos: `docs/API_EXAMPLES_V03.json`; esquemas exactos: `docs/openapi.json`. Los IDs de hallazgo se obtienen de las respuestas, no deben codificarse como constantes.

```http
GET /rag/findings?subject_id=sim-crew&mission_id=sim-mission
Authorization: Bearer <reader-token>
```

Extracto de una respuesta existente:

```json
{"result":"INCONCLUSIVE","reason":"INSUFFICIENT_TEMPORAL_COVERAGE","diagnosis":null,"limitations":["RESEARCH_ONLY","NO_DIAGNOSIS","NO_TREATMENT_AUTHORIZATION"]}
```

Evaluación usando la autoridad determinista y credencial de investigación aprovisionada por separado:

```json
{"rule_id":"VIGILE-AER-003","subject_id":"sim-crew","mission_id":"sim-mission","as_of":"2025-04-01T12:00:00Z","bindings":{"premission_aerobic_capacity":"baseline-vo2","current_aerobic_capacity":"longitudinal-vo2-2"},"mode":"SIMULATION"}
```

POST /evaluations retorna hallazgo con id/bundle y REQUIREMENT_NOT_MET para este fixture. mode OPERATIONAL retorna REQUIRES_VALIDATION. La demo revoca el token de preparación al terminar; reader y frontend no pueden ejecutar ese POST de evaluación. No elevar rol en el cuerpo: autorización pertenece al servidor.

401 sin identidad, 403 rol/alcance, 404 referencia, 409 ID inmutable, 413 tamaño, 422 contrato/contexto inválido. Un 200 con result bloqueado sigue siendo una decisión bloqueada. En caída de conexión durante escritura, consultar el ID persistido antes de repetir; no asumir ausencia de commit.

## Optimización y computación espacial

`integration-demo` mide latencia cliente HTTP por solicitud, tiempo de inicio, pared del recorrido, CPU y working set del **PID real** del servidor (el ejecutable del venv en Windows puede ser un redirector) y tamaño SQLite/WAL. `latencies.json` contiene rutas/tiempos sin tokens; `report.json` contiene métricas y metodología. Se usan contadores Windows GetProcessTimes/GetProcessMemoryInfo sin dependencia psutil. En otros sistemas los contadores de proceso se declaran no disponibles, no cero. No mide consumo eléctrico, temperatura, fiabilidad radiológica, memoria del LLM, ni capacidad de vuelo.

Medición inicial de entrega, Windows 11 / Python 3.13.16 / 32 CPUs lógicas, 38 mediciones y 90 solicitudes secuenciales:

| Métrica | Valor observado |
|---|---:|
| Arranque | 1.690 s |
| Workload secuencial | 2.070 s |
| Latencia mediana / p95 / máxima | 19.20 / 35.34 / 111.35 ms |
| CPU del servidor durante workload | 0.5156 s |
| CPU media, un núcleo como 100% | 24.90% |
| Working set máximo observado | 64.04 MiB |
| SQLite vivo + WAL/SHM | 1.595 MiB |
| SQLite tras cierre | 572 KiB |

Una ejecución, sin concurrencia ni ensayo de carga; no son SLA ni requisitos espaciales. Variarán por caché, carga del host y hardware. La latencia del workload excluye el arranque y la descarga posterior de OpenAPI. Memoria pico corresponde al servidor hasta finalizar el workload, no a todo el equipo.

Offline: ejecución completa con guard de sockets Python que rechaza destinos externos y DNS externo, manteniendo loopback; prueba negativa de conexión externa. El guard es un instrumento de prueba, **no firewall OS ni aislamiento contra código malicioso**. No se apagó la red del usuario. El motor no necesita Internet; corpus y dependencias son locales. Probar en la plataforma destino con red físicamente/operativamente deshabilitada sigue siendo necesario.

| Componente | Política de recursos |
|---|---|
| Auth/alcance, calidad, reglas, evidencia, persistencia y auditoría | Críticos: no omitirlos para ahorrar recursos. Si no se puede conservar la decisión, propagar error y no comunicar éxito. |
| RAG/UI, transcripción demo, descarga de catálogo y benchmark | Prescindibles para evaluar reglas; se pueden suspender. |
| Tendencias/baselines descriptivos | Se pueden diferir, sin sustituir resultados ni usar referencias retiradas; no declarar normalidad durante retraso. |
| Cadencia/adquisición | Conservar timestamps y huecos; no imputar ni inventar medias cuando se reduzca muestreo. |

POST /resources/assessments compara cadencia propuesta contra política **declarada por el integrador**: FULL/LOW_POWER/EMERGENCY_POWER son modos técnicos, no severidades. 120 s propuestos frente a 60 s declarados produce POLICY_CONFLICT en la demo; calidad insuficiente produce INCONCLUSIVE. No cambia dispositivos/umbrales ni impone límites de CPU/memoria. No hay scheduler energético, load shedding automático o simulación de disco lleno/OOM: se requiere definir y probar esos comportamientos antes de operación.

## Estructura y dependencias

```text
Vigile/
  01_... a 10_... y 99_...       investigación original conservada
  engine/vigile/                motor existente, modelos, API, reglas, auditoría
    simulator.py                generador y envelope tipado v1
    adapters.py                 MeasurementSource, SyntheticAdapter, LocalClient
    integration.py              orquestación HTTP y métricas de integración
  engine/tests/test_integration_release.py
  engine/examples/reader_client.py
  engine/examples/frontend_client.py
  engine/examples/synthetic-seed42.json
  engine/data/spaceapps-demo/    base sintética y configuración privada reutilizable
  engine/data/integration-runs/  ejecuciones aisladas; no subir a Git
  engine/requirements.lock, wheelhouse/, scripts/install_offline.ps1
  docs/                         contratos, OpenAPI, ejemplos, pruebas y métricas
  work/releases/                código previo archivado sin secretos/base clínica
```

Conservado: Python 3.13.16 x64 probado, FastAPI/Pydantic/SQLite/Uvicorn/pytest. HTTPX ya estaba instalado/fijado; ahora figura también como extra integration del pyproject. No se descargaron nuevas dependencias ni se cambió el lock. Instalación offline desde engine:

```powershell
powershell -NoProfile -File scripts\install_offline.ps1
& .\.venv\Scripts\python.exe -m pip check
```

Requiere Python 3.13 x64 para el wheelhouse suministrado. La aplicación declara >=3.11, pero otras versiones/plataformas no fueron verificadas. Las herramientas de integración usan PowerShell en Windows para ACL; si falla, la demo falla antes de emitir secretos. En POSIX se restringe la carpeta a 0700; esa plataforma no se probó en esta entrega.

## Límites y seguridad

- **SQLite, WAL y backups no están cifrados.** No usar datos personales reales. Los tokens privados son secretos planos protegidos por permisos de carpeta; servidor conserva hashes y recarga configuración por solicitud.
- Demo usa directorio nuevo con ACL de usuario actual, SYSTEM y Administrators. Token bootstrap clinician solo vive en memoria y su hash se revoca al finalizar/fallar. Solo quedan reader y operator limitados a fixtures. No hay credenciales incrustadas en ejemplos o transcripciones.
- Un atacante con control del almacenamiento puede modificar código/SQLite, eliminar triggers y reconstruir toda la cadena de auditoría. La verificación detecta inconsistencias dentro del diseño, no prueba integridad contra ese atacante. Requiere checkpoints externos/firma/backup bajo otra autoridad.
- Misma cuenta OS puede leer archivos de otros procesos: los permisos API no aíslan un LLM con acceso al filesystem. Faltan separación OS/contenedores, gestión institucional de secretos, MFA, TLS remoto, rate limiting, retención y recuperación ante fallos.
- Base y consultas pequeñas, un worker local; búsquedas recorren registros y el replay copia observaciones del ámbito. Falta paginación general y evaluación de crecimiento; no habilitar múltiples workers por simple decisión del integrador.
- C015 del ejemplo MSI06 es una observación humana **simulada** explícita; no hay algoritmo cognitivo nuevo. La relación solo documenta coocurrencia sin causalidad. MSI05/MSI10 siguen bloqueadas por datos no modelados.
- Las 44 condiciones/11 etapas mantienen cobertura estructural; ningún resultado sintético valida sensibilidad, especificidad, diagnóstico, tratamiento, pronóstico o disponibilidad de hardware espacial. Los 15 comparadores y las restricciones científicas de v0.2 permanecen.

## Próximos trabajos priorizados

1. Integrar los tres consumidores contra esta base aislada; acordar IDs, unidades, manejo de INCONCLUSIVE y límites de permisos. Mantener contratos/OpenAPI y pruebas en CI.
2. Aislar RAG y frontend del filesystem/credenciales administrativas; cifrado, gestión/rotación de secretos, checkpoints externos y backup/restore probado.
3. Definir contexto de misión versionado y vinculación longitudinal entre fases; no sobrescribir el contexto actual para conseguir que pasen reglas.
4. Diseñar recuperación de ingestas parciales, paginación e índices; probar concurrencia, disco lleno, interrupción de escritura y agotamiento de recursos.
5. Revisión biomédica independiente de fuentes/protocolos, contradicciones (incluido S27), parámetros por dispositivo y misión. Autorización clínica verificable antes de cualquier activación.
6. Adaptadores de hardware específicos y procesamiento de señales con validación independiente; después medir rendimiento/energía en hardware objetivo.

## CONTEXTO PARA CONTINUAR CON CHATGPT

VIGILE es ahora versión de integración 0.3.0, conservando la arquitectura y SQLite schema 1. Paquete Python existente más tres módulos pequeños: simulator, adapters e integration. 172 pruebas aprobadas; demo real y clientes externos verificados tras reinicio, 106 originales intactos. Dataset seed42: hash `5091e65d64ebe5eebc6701a17d306ef365cc50684769c2cfd7e947a951260f1a`, 38 mediciones en tres fases, dos baselines, dos tendencias, 12 hallazgos, dos episodios. Siete inconclusos preservados y tres incumplimientos sintéticos; tratamiento/OPERATIONAL bloqueados. Replay requiere mismo código/corpus; v0.2 archivado antes de cambiar código. Auditoría/UUIDs/métricas no son bit-a-bit deterministas.

Comandos de continuidad desde `C:\Users\Gianni\Desktop\Vigile\engine`:

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile integration-demo --seed 42
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir data\spaceapps-demo --port 8765
```

Con servidor activo, otra consola:

```powershell
& .\.venv\Scripts\python.exe examples\reader_client.py --token-file data\spaceapps-demo\reader-token.txt
& .\.venv\Scripts\python.exe examples\frontend_client.py --token-file data\spaceapps-demo\frontend-token.txt
```

Frontend consume consultas de profiles/measurements/baselines/trends/findings/episodes/pathway/followups con token operator scoped de ejemplo; no hay frontend visual. RAG consume solo /rag/findings y evidencia con reader, montando únicamente su secreto bajo otra cuenta OS; no hay LLM real. Optimizador usa report/latencies para medición y resources/assessments mediante credencial research administrada por separado, sin autoridad para cambiar reglas. Datos de referencia: `docs/openapi.json`, `API_EXAMPLES_V03.json`, `INTEGRATION_RELEASE.json`, `PERFORMANCE_V03.json`, JUnit y esta entrega. Priorizar integración, cifrado/aislamiento, recuperación operativa y revisión científica; nunca presentar tests sintéticos como validación clínica u operacional.
