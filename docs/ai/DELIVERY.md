> Configuración vigente tras la corrección de consistencia: [CONSISTENCY_AUDIT.md](CONSISTENCY_AUDIT.md). Usar `portal-consistency-v061`; los comandos previos con `portal-v06-final` corresponden a la demostración histórica conservada.

> Actualización 19/10/2026: consultar [OLLAMA_RECOVERY.md](OLLAMA_RECOVERY.md). Norton confirmó la cuarentena; la IA funciona ahora mediante Ollama oficial. Este informe conserva las mediciones y el incidente anteriores.

# VIGILE 0.6.0 — Integración local, estado de entrega

18 de octubre de 2026. Desarrollo incremental sobre v0.5.0. No se modificaron criterios diagnósticos. **La integración ejecutó inferencia real, pero la demostración FULL quedó bloqueada al desaparecer el ejecutable llama-server.exe durante la prueba de reinicio. Actualmente está operativo CRITICAL. No se declara una entrega FULL estable.**

## Qué funciona y qué está bloqueado

- Qwen3-4B-Instruct-2507 Q4_K_M fue descargado, verificado y ejecutado realmente mediante llama.cpp b11721 Vulkan en esta computadora. Se obtuvieron explicaciones originales con citas sobre DKA, anafilaxia y datos pendientes; no fueron respuestas simuladas.
- Generación JSON restringida, referencias a IDs existentes, rechazo de números no sustentados, lenguaje de tratamiento/diagnóstico independiente y enlaces inventados. Una segunda consulta al modelo comprueba soporte de cada afirmación frente exclusivamente a sus citas. Esto reduce errores, **no demuestra corrección semántica ni elimina alucinaciones**. Las respuestas rechazadas no se muestran como explicaciones válidas.
- RAG reutiliza los endpoints reader, resultados, criterios y fuentes v0.5, y añade 193 fragmentos del informe local de investigación con documento, línea, offset y SHA-256. No incorpora todos los PDF ni verifica automáticamente la verdad científica de cada párrafo. El texto documental no modifica permisos ni reglas.
- Frontend existente ampliado con modo de operación, evaluación activa, explicaciones MODEL_EXPLANATION separadas de ENGINE/DOCUMENT y referencias. Historial de hasta tres preguntas por evaluación en memoria; no es una historia clínica ni conversación persistente. No hay credenciales clínicas en JavaScript.
- FULL y LOW_POWER ejecutaron inferencia real. CRITICAL fue probado con el proceso del modelo físicamente detenido: dashboard, RAG extractivo, cuatro replays, controles reader y auditoría siguieron funcionando, sin cambiar registros clínicos.
- Al restaurar FULL, el archivo `engine/local_ai/llama-b11721/llama-server.exe` ya no existía. Se detectó Norton 360 instalado; no apareció un evento equivalente en Defender ni una entrada coincidente en los reportes de texto consultados de Norton. **La causa exacta está pendiente; no se afirma que sea una cuarentena confirmada.** No se restauró el binario, no se desactivaron protecciones y no se añadieron exclusiones. Se solicitó al usuario el mensaje de seguridad, si existe.

## Hardware y selección

| Elemento | Observación real |
|---|---|
| CPU | Intel Core i9-13900HX, 24 núcleos, 32 procesadores lógicos |
| RAM instalada | 34029125632 bytes, aproximadamente 31,7 GiB |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| VRAM | 8188 MiB; 7956 MiB libres al inventario inicial |
| Driver NVIDIA | 617.42 |
| Disco C libre inicial | 136765726720 bytes, aproximadamente 127,4 GiB |

Se compararon llama.cpp y Ollama. No se encontraron instalaciones/modelos reutilizables en los directorios habituales. Se eligió llama.cpp portable para evitar un servicio global y utilizar un GGUF local fijado por hash; conserva autenticación propia, loopback y `--offline`. El adaptador Ollama existente se conserva y se añadió soporte conversacional, pero **Ollama no fue instalado ni probado con un modelo real** en esta iteración.

Modelo: Qwen3-4B-Instruct-2507, 4B parámetros, Q4_K_M, archivo de 2497280448 bytes. Modelo base Apache-2.0, runtime llama.cpp MIT; licencias preservadas en local_ai. Cuantización de lmstudio-community, revisión fijada `4edb920b6f14e3b9284d4502a6485103d72cde05`. No se supone aptitud médica por nombre, benchmark general o licencia.

SHA-256 modelo: `8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc`.
ZIP runtime: 32315391 bytes; SHA-256 `b2dab62833cc07aae4a1f28752874668b6a98d304a7f8ca6c1421a0d1e1a7075`.

Referencias técnicas: [modelo base y licencia](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [cuantización fijada](https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF/tree/4edb920b6f14e3b9284d4502a6485103d72cde05), [runtime publicado](https://github.com/ggml-org/llama.cpp/releases/tag/b11721), [contrato llama-server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). El tamaño y los hashes se contrastaron con las APIs de los distribuidores antes de descargar.

## Modos

| Ajuste | FULL | LOW_POWER | CRITICAL |
|---|---|---|---|
| Inferencia | Sí, si runtime disponible | Sí, si runtime disponible | Nunca |
| Bloques máximos al modelo | 10 | 5 | 0 |
| Caracteres por bloque | 850 | 650 | Consulta extractiva |
| Salida máxima generador | 700 tokens | 400 tokens | 0 |
| Contexto al iniciar runtime | 6144 | 3072 | No iniciar |
| Hilos al iniciar runtime | 8 | 4 | No iniciar |
| Batch / microbatch | 512 / 256 | 256 / 128 | No iniciar |
| Cuantización | Q4_K_M | Q4_K_M | No aplicable |
| Reglas clínicas | Idénticas | Idénticas | Idénticas |

Cambiar modo en el portal altera los presupuestos de la petición, **no reinicia llama.cpp ni libera automáticamente su KV/VRAM**. Para reducir la reserva de memoria, reiniciar el runtime con LOW_POWER; para liberar memoria, detenerlo. El benchmark sí reinició FULL→LOW_POWER y detuvo el proceso para CRITICAL. La cuantización se fija al cargar el modelo; no se anuncia una reducción dinámica inexistente. LOW_POWER es un perfil de recursos, no una medición de ahorro eléctrico.

## Pruebas y rendimiento

Antes de cambios: 275 pruebas aprobadas en 25,43 s. Final: **298 aprobadas, 0 fallos, 1 warning en 39,03 s**. Se corrigió una lectura de fixture sin UTF-8 en Windows. Persistió el warning Starlette/TestClient sobre HTTPX. XML y verification.json conservan resultados.

23 casos nuevos: referencias falsas, números no sustentados, inyección de instrucciones, HTML/URLs, lenguaje de tratamiento, comprobación semántica rechazada, biblioteca ausente/manipulada, límites LOW_POWER, CRITICAL sin red, CSRF, scopes y ausencia de herramientas en payloads. Las pruebas unitarias de generación usan mocks explícitos; se distinguen de las ejecuciones reales siguientes.

Arranque FULL hasta /v1/models disponible: **9,42 s**. Pruebas iniciales reales observaron aproximadamente **69–73 tokens/s** en respuestas breves, según timings del runtime; no es un benchmark general ni una garantía de latencia.

Último recorrido TCP con el modelo real, tiempos totales impresos durante ejecución:

| Modo | DKA | Anafilaxia | Datos pendientes | Resultado |
|---|---:|---:|---:|---|
| FULL | 4714 ms | 1808 ms | 2743 ms | 2 respuestas admitidas, 1 rechazada por controles |
| LOW_POWER | 1989 ms | 1887 ms | 2728 ms | 2 respuestas admitidas, 1 rechazada por controles |
| CRITICAL | 186 ms | 166 ms | 475 ms | 3 consultas extractivas, sin inferencia |

Incluyen llamadas de verificación y recuperación; una respuesta rechazada también consume tiempo. Hubo otras tareas/pruebas en el equipo. No deben compararse como ensayo controlado de eficiencia. El proceso de benchmark terminó al fallar la restauración del ejecutable, antes de guardar el informe completo de muestras RAM/VRAM/CPU. **Esas mediciones no se reportan como disponibles**. El script ahora guarda checkpoints por modo para no perderlos al repetir. No se midieron energía eléctrica, autonomía ni hardware espacial.

Verificación posterior con runtime ausente: cuatro consultas CRITICAL, cuatro replays coincidentes, escritura reader 403, scope ajeno 403, modo inválido 422, origen no autorizado 403, recuperación documental disponible y registros clínicos idénticos. 106 archivos originales y 17 archivos clínicos/conocimiento v0.5 conservan contenido exacto. Vista CRITICAL comprobada en navegador.

## Offline y seguridad

La inferencia real se ejecutó con un modelo en disco, `--offline`, sin UI ni agent/tools/MCP del runtime, un entorno heredado limitado y únicamente URLs 127.0.0.1. El cliente del recorrido real bloqueó conexiones no loopback. **No se desconectó físicamente la red ni se impuso un firewall de salida al proceso nativo**: la sesión no es administrador. Por tanto, se verificó operación local en modo offline de llama.cpp, no aislamiento de red del sistema operativo. Queda pendiente repetir en un entorno desconectado o con firewall por proceso supervisado.

Tres secretos distintos: código del portal, bearer reader clínico y API key del runtime. El modelo no recibe credenciales ni herramientas, y no conoce endpoints de escritura. El launcher filtra variables de entorno en vez de heredar tokens del usuario. No hay cambios de autorización clínica ni tratamiento ejecutable. Las afirmaciones generadas, incluso con citas válidas y segunda revisión LLM, pueden contener errores semánticos: no deben usarse como autoridad clínica. El motor sigue siendo la única fuente de resultados.

SQLite, archivos de secretos y backups siguen sin cifrado. Un administrador del disco/código puede reescribir hashes y auditoría. No se implementaron aislamiento de filesystem por usuario/contenedor, anclaje externo ni ACL específicas. HTTP loopback no debe publicarse en red. El mismo usuario del SO puede acceder a archivos de distintos procesos. No se declara resuelta la seguridad por tener prompts o hashes.

## Inicio actual, sin depender del LLM

Demo v0.6: backend 8895, portal http://127.0.0.1:8896, datos `engine/data/portal-v06-final`. La configuración queda en CRITICAL hasta resolver la desaparición del runtime. Los servicios ya están iniciados; no duplicarlos en los mismos puertos.

Para iniciar después de detener los servicios actuales, terminal 1:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir data\portal-v06-final --port 8895
```

Terminal 2:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
Get-Content .\data\portal-v06-final\portal-access.txt
& .\.venv\Scripts\python.exe -m vigile.portal --config data\portal-v06-final\portal-config.json --port 8896
```

Abrir el portal, introducir únicamente portal-access.txt y seleccionar escenario. Preguntar por criterios, bloqueos o datos pendientes. No compartir reader-token.txt ni runtime-key.txt.

## Inicio con IA, condicionado a resolver el bloqueo

**No ejecutar de nuevo el instalador para eludir una posible cuarentena. Primero identificar por qué falta llama-server.exe y revisar la detección/procedencia con el responsable del equipo. No se recomienda desactivar Norton ni crear exclusiones generales.** El instalador fijado se conserva como herramienta de reproducibilidad para una instalación aprobada o limpia, no como recuperación automática del archivo retirado.

Una vez disponible un runtime verificado y permitido por la seguridad local:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m vigile.local_runtime --mode FULL
# Alternativa, después de detener la instancia anterior:
# & .\.venv\Scripts\python.exe -m vigile.local_runtime --mode LOW_POWER
```

En el portal, seleccionar FULL o LOW POWER. /api/status debe indicar LOCAL_MODEL_READY. Una respuesta real requiere inference_executed=true y generated no vacío. UNAVAILABLE, REJECTED_OR_FAILED o EXTRACTIVE_ONLY nunca se presentan como IA generada. El runtime se inicia oculto y escribe local_ai/runtime-process.json; comprobar PID y ruta exacta antes de detenerlo. Ctrl+C de la terminal lanzadora no detiene necesariamente ese proceso independiente.

Python >=3.11, dependencias Python existentes y runtime nativo portable; no se añadieron paquetes Python. En otra máquina, instalar dependencias desde una wheelhouse offline o preparar previamente `pip install -e ".[test,integration]"`. Transferir archivos públicos/modelo/licencias e índice; generar secretos nuevos, no distribuir la carpeta data de esta computadora.

## Archivos y contratos

Nuevos: vigile/conversational.py, offline_library.py, local_runtime.py y tests/test_conversational.py. Modificados: local_assistant.py, portal.py, web/index.html, web/app.js, metadatos de versión y .gitignore. Modelos/runtimes y secretos están excluidos del control de versiones. La arquitectura Engine/Store/Registry/API permanece.

POST /api/assistant añade history (máximo 3 preguntas, 1200 caracteres cada una), generated, mode, document_issues y metrics. Cada generated contiene text, evidence_ids, references y kind=MODEL_EXPLANATION. ENGINE/DOCUMENT permanecen en retrieved/answer. No interpretar una cita existente como prueba de corrección de toda la frase.

POST /api/mode recibe {mode: FULL|LOW_POWER|CRITICAL}; exige sesión/origen y no admite cambios mientras haya inferencia en curso. No altera criterios ni autorización médica; el modo es del proceso portal, no individual por usuario ni persistente al cambiarlo en UI. La configuración inicial procede de portal-config.json.

El motor clínico y el frontend conservan contratos previos en docs/portal/CONTRACTS.md. Sensores/ingestión no pasan por el LLM. Los integradores no deben abrir SQLite directamente ni entregar credenciales writer al asistente.

## Pendientes para NASA Space Apps

1. Resolver la desaparición del runtime sin debilitar la protección del equipo; repetir arranque, conversación en navegador y benchmark completo.
2. Reducir rechazos y evaluar semántica con revisión humana independiente, especialmente negaciones, árboles OR y distinción entre datos diagnósticos y de seguridad. No bajar controles para mejorar una demo.
3. Repetir operación con red desconectada o aislamiento de salida verificable; recoger RAM/VRAM/CPU y latencia completos, carga concurrente y recuperación de fallos.
4. Aislar procesos/secretos, cifrar almacenamiento y anclar auditoría; ampliar revisión de ataques por documentos e historial.
5. Validar pertinencia de recuperación científica, ampliar corpus autorizado, accesibilidad y continuidad conversacional. No hay validación clínica, operacional ni espacial.

## CONTEXTO PARA CONTINUAR CON CHATGPT

VIGILE 0.6 implementado incrementalmente; 298 tests pasan, criterios intactos. Qwen3 4B Q4_K_M real ejecutó con llama.cpp Vulkan b11721 sobre RTX4060. Modelo y ZIP íntegros; launcher llama-server.exe desapareció durante reinicio FULL tras probar LOW_POWER/CRITICAL. Causa pendiente; Norton instalado, cuarentena no confirmada. No restaurar ni excluir sin resolver causa. Portal v0.6 sigue en 8896 y backend8895, modo CRITICAL funcional; v0.5 anterior en otros puertos se conserva.

Comandos de verificación: `python -m pytest -q`, `python -m vigile clinical-demo`. Índice: `python -m vigile.offline_library --output local_ai\library.json`. Demo nueva: `python -m vigile.portal_demo --output data\NOMBRE_NUEVO`; configurar inference_provider, model, model_url, runtime_key_file, library_manifest y modo según la demo final. Config contiene rutas de secretos, no copiarlas al navegador.

Scripts de benchmark/checks y manifiestos están en docs/ai. Antes de cambios Python, considerar implementation_hash: cualquier cambio requiere demo nueva para reproducir con ese código, conservando snapshots viejos. No tratar respuestas simuladas de tests como inferencia real ni pruebas sintéticas como validación clínica.

