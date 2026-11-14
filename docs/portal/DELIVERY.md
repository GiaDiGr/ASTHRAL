# VIGILE 0.5.0 — Entrega de integración

16 de octubre de 2026. Ampliación sobre v0.4, sin reconstrucción del motor ni cambios de criterios médicos. Datos exclusivamente sintéticos. No constituye validación clínica u operacional.

## Resultado

Dashboard local responsive con perfiles y misión, mediciones y calidad, gráfico temporal SVG, baseline, tendencias persistidas, hallazgos separados del diagnóstico, observaciones de la evaluación, árboles de criterios, dimensiones independientes, diferencial ordinal, pruebas pendientes, bloqueos, documentos de protocolos, historial y hashes. Las series de monitorización compartidas no se atribuyen a una evaluación salvo entradas explícitas o measurement_bindings. La interfaz no ejecuta tratamientos.

Portal FastAPI separado del backend: navegador → sesión local → portal/BFF → API con credencial reader y scopes. El navegador nunca recibe el token reader. HTML/CSS/JavaScript y SVG sin CDN, Node, compilación ni dependencias nuevas. Se mantienen Python, FastAPI, Pydantic, SQLite, HTTPX y pytest.

Interfaz LocalInference y adaptador Ollama configurables. Recuperación de criterios y referencias de la biblioteca clínica autorizada y resultados del motor. El modelo únicamente selecciona IDs de extractos existentes; no se presenta texto médico libre generado. Distingue ENGINE, DOCUMENT y selección del modelo. Sin modelo disponible, devuelve UNAVAILABLE con evidencia documental, sin fingir inferencia. No hay Ollama/modelo local identificado en esta instalación: la inferencia real no fue verificada ni se descargaron pesos. El RAG no indexa todavía todos los informes/PDF ni incorpora búsquedas vectoriales.

## Verificación ejecutada

- Antes de cambios: 251 pruebas aprobadas y clinical-demo original ejecutada (28 solicitudes ASGI, replay y auditoría válidos).
- Final: **275 pruebas aprobadas, 1 warning, 32.26 segundos**. Incluye 24 casos adicionales de portal, permisos, scopes, sesión, CSRF, fuentes, fallos, inferencia simulada para probar el adaptador, rechazo de cloud y salidas inválidas, bloqueo de sockets en prueba aislada y repetibilidad. XML: tests-v05.xml.
- TCP real: navegador y cliente HTTPX → portal → backend; tres escenarios y una reevaluación; lectura autorizada, escritura reader 403, scope ajeno 403, CSRF 403, cuatro replays concordantes y cadena de auditoría válida. live-verification.json contiene resultados y tiempos reales.
- Navegador: acceso local, carga de métricas/gráfico, escenarios DKA/anafilaxia/mareo, selección de evidencia y mensajes de ausencia de modelo. Prueba manual, no suite automatizada de navegadores.
- Se conserva el warning de deprecación Starlette/TestClient con HTTPX. No se sustituyó el transporte de toda la suite en esta entrega.
- original-preservation.json contrasta los hashes de los 106 archivos inventariados y el informe clínico. No se modificó documentación científica original.

La medición TCP inicial de 9 peticiones al portal dio mediana 77.10 ms y máximo 523.99 ms. La comprobación de continuidad del 18 de octubre dio mediana 44.07 ms y máximo 344.73 ms, incluyendo inicio de sesión y recuperación documental; SQLite 262144 bytes. Los hashes de los archivos coinciden con la versión probada el 16 de octubre; no se repitió innecesariamente la suite sin cambios. Los servicios se reiniciaron y los cuatro replays, permisos y auditoría volvieron a pasar. No son mediciones de CPU, RSS, carga sostenida, inferencia ni hardware de vuelo.

## Ejecutar desde cero en esta instalación

Python >=3.11; la instalación usada dispone de Python 3.13 y .venv. Para instalar en otra máquina con paquetes disponibles: `python -m pip install -e ".[test,integration]"`. La instalación inicial puede necesitar red; la operación no necesita Internet. Conservar repositorio completo, catálogos originales y JSON de conocimiento. No copiar credenciales entre equipos. requirements-installed.txt registra versiones observadas, no es un lockfile multiplataforma.

Terminal 1, generar una demo NUEVA (el directorio elegido no debe existir) e iniciar backend:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
$demo = 'data\portal-demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
& .\.venv\Scripts\python.exe -m vigile.portal_demo --output $demo
Write-Output $demo
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir $demo --port 8765
```

Terminal 2, elegir la carpeta impresa en la terminal 1 (este comando toma la última demo nueva):

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
$demo = (Get-ChildItem .\data -Directory -Filter 'portal-demo-*' | Sort-Object Name -Descending | Select-Object -First 1).FullName
Get-Content (Join-Path $demo 'portal-access.txt')
& .\.venv\Scripts\python.exe -m vigile.portal --config (Join-Path $demo 'portal-config.json') --port 8766
```

Abrir http://127.0.0.1:8766 e introducir exclusivamente el código portal-access.txt. No introducir reader-token.txt ni compartir archivos de secretos. Cada terminal se detiene con Ctrl+C; reiniciar el portal invalida sesiones. No lanzar varias instancias sobre los mismos puertos.

La demo ya preparada y comprobada está en `engine/data/portal-v05-final`, con backend 8875 y portal http://127.0.0.1:8876. Su config ya apunta a 8875. Para reiniciar esa demo, usar `serve --integration-dir data\portal-v05-final --port 8875` y `vigile.portal --config data\portal-v05-final\portal-config.json --port 8876` en terminales separadas, una vez detenidos los procesos actuales. running-processes.json identifica los lanzadores actuales; comprobar procesos/hijos antes de detenerlos, nunca matar otros procesos por nombre.

## Visualizar las tres demostraciones

1. Seleccionar clinical-crew / clinical-earth. El rótulo SIMULACIÓN debe permanecer visible. El gráfico usa mediciones almacenadas, no imágenes ni datos ficticios de presentación.
2. Cetoacidosis diabética: criterios cumplidos y emergencia; datos de seguridad, recursos y autorización bloquean el protocolo. Abrir árbol y documento del protocolo; preguntar «¿Por qué está bloqueado el protocolo?».
3. Anafilaxia: emergencia por la vía de criterios ya implementada, sin tratamiento habilitado. Consultar fuentes y requisitos.
4. Mareo y taquicardia: seis rutas permanecen inconclusas; la hipótesis externa de arritmia y ECG se priorizan sin inventar diagnóstico. «Datos pendientes» recupera la explicación del ECG.
5. Reevaluación DKA: datos de potasio introducidos por el simulador; conserva evaluación padre, hashes y bloqueo de seguridad. «Cambios recientes» recupera diferencias de dimensiones.

Los datos clínicos usados aparecen dentro de cada evaluación. Los valores de monitorización del panel superior corresponden al sujeto y no cambian al seleccionar una evaluación histórica.

## Activar un modelo local existente (opcional)

Solo si el equipo dispone ya de Ollama y pesos locales compatibles con sus recursos. No se midieron RAM/GPU de esta computadora ni se recomienda un tamaño sin esa información.

```powershell
$env:OLLAMA_NO_CLOUD = '1'
ollama serve
```

En otra terminal, listar modelos ya instalados con `ollama list`, establecer en portal-config.json `model` al nombre exacto local y conservar `model_url` como `http://127.0.0.1:11434`; reiniciar portal. No hay descarga automática. El adaptador exige entrada local GGUF de tamaño positivo y rechaza nombres cloud/metadata remota. Consultar el estado y verificar una respuesta con inference_executed=true antes de afirmar inferencia real. Cada modelo requiere evaluación propia de pertinencia, latencia y memoria.

El servicio Ollama es un proceso independiente: una URL loopback por sí sola no impide que ese servicio use Internet. Desactivar cloud y aplicar aislamiento/reglas de salida del sistema operativo antes de datos sensibles. Referencias oficiales: [API tags](https://docs.ollama.com/api/tags), [API chat](https://github.com/ollama/ollama/blob/main/docs/api.md), [FAQ y OLLAMA_NO_CLOUD](https://github.com/ollama/ollama/blob/main/docs/faq.mdx).

## Seguridad y límites

Credenciales reader confinadas por diseño al proceso portal; permisos sujetos/misiones aplicados por backend. Sesión HttpOnly/SameSite=Strict, origen estricto en POST, límite de cuerpo/pregunta/sesiones/intentos, CSP sin recursos externos, errores sin secretos, rutas explícitas sin proxy arbitrario. Las preguntas y respuestas no se persisten; la auditoría de decisiones clínicas permanece en el motor. No hay auditoría persistente de conversaciones.

SQLite y secretos en archivos no están cifrados. Un atacante con control de almacenamiento/código puede reescribir auditoría y hashes locales. El portal no instala ACL de Windows, contenedores, firewall ni anclaje externo. Los procesos ejecutados como el mismo usuario podrían leer archivos de otros procesos: separación lógica no equivale a aislamiento del sistema operativo. HTTP loopback, sesión única de rol reader y ausencia de TLS son apropiados solo para el prototipo local; no publicarlo en red. Falta revisión independiente de seguridad, accesibilidad y carga. No hay autorización terapéutica ejecutable.

Dashboard devuelve como máximo 1000 mediciones y 100 evaluaciones, sin paginación; la lectura interna aún recorre registros SQLite y puede costar memoria en bases grandes. Refresco manual, sin streaming ni alertas de fondo. No imputa datos faltantes, no calcula nuevos umbrales y no cambia decisiones. Baselines/tendencias mostrados son registros históricos: no implican vigencia clínica automática. Las seis rutas v0.4 y las 44 condiciones estructurales mantienen sus límites; ninguna obtiene validación clínica por estas pruebas.

Prioridades: 1) revisión clínica independiente y gobernanza de misión; 2) aislar procesos/secretos, cifrado y auditoría anclada; 3) seleccionar y evaluar un modelo local con pruebas de grounding y prompt injection; 4) ampliar recuperación documental autorizada y trazabilidad de conversaciones; 5) paginación, carga, accesibilidad y pruebas de navegador automatizadas; 6) sensores reales calibrados y validación contextual independiente.

## CONTEXTO PARA CONTINUAR CON CHATGPT

VIGILE 0.5.0 conserva Engine/Store/Registry, schema SQLite 1 y capa clínica v0.4. Cuatro nuevos módulos: dashboard_api.py, local_assistant.py, portal.py, portal_demo.py; tres assets web y test_portal.py. Modificados api.py/security.py para proyecciones reader y rutas; __init__.py/service.py/pyproject.toml para versión/empaquetado y README. No se cambiaron criterios ni protocolos científicos. 275 pruebas verdes. La demo final tiene tres casos, reevaluación, 21 mediciones y un baseline. Todos los tratamientos bloqueados. Frontend operativo; RAG extractivo limitado; inferencia real pendiente por ausencia de modelo.

CONTRACTS.md y openapi-v05.json definen límites por componente. clinical-demo/transcripts conservan solicitudes reales sin credenciales. Reproducir con los comandos anteriores. Cada cambio de código Python altera implementation_hash: regenerar demos nuevas para comparar con código actual; conservar código histórico para reproducir snapshots anteriores, sin alterar hashes almacenados. No reconstruir ni migrar destructivamente la base. Los módulos externos deben consumir contratos, no abrir SQLite ni escribir reglas. El LLM recibe solo proyecciones autorizadas y nunca credenciales de escritura.
