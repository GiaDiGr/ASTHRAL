# VIGILE v0.7.0 — entrega funcional

Biomedical / Health Intelligence conserva su arquitectura Python/FastAPI/Pydantic/SQLite. Añade un ciclo experimental por petición, seis vistas de vigilancia (cinco dominios espaciales y electrolitos/oxigenación), una séptima ruta clínica restringida y tres escenarios longitudinales. No ejecuta tratamientos. Las comprobaciones son de software con datos sintéticos, no validación clínica ni operativa espacial.

## Ejecutar y reproducir

Desde PowerShell:

```powershell
Set-Location C:\Users\Gianni\Desktop\Vigile\engine
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m vigile.monitoring_demo --output data\v070-reproduction-01
```

La carpeta de salida debe ser nueva. El segundo comando ejecuta la recepción por API, lectura reader, restricciones de escritura, 15 ciclos y sus reproducciones; guarda SQLite, OpenAPI, solicitudes, respuestas y tiempos. No necesita Ollama ni conexión externa. Los valores, fechas e identificadores sintéticos son fijos. Las latencias y los registros operativos de auditoría dependen de la ejecución.

Para preparar otra demostración con el portal y conservar la configuración local actual:

```powershell
.\.venv\Scripts\python.exe -m vigile.monitoring_portal_demo --output data\portal-v070-reproduction-01 --reuse-config data\portal-v070\portal-config.json
```

Los servicios actuales ya están activos. Tras detener únicamente las instancias VIGILE que ocupen esos puertos, iniciar en dos terminales:

```powershell
Set-Location C:\Users\Gianni\Desktop\Vigile\engine
.\.venv\Scripts\python.exe -m vigile serve --integration-dir data\portal-v070 --port 8895
```

```powershell
Set-Location C:\Users\Gianni\Desktop\Vigile\engine
.\.venv\Scripts\python.exe -m vigile.portal --config data\portal-v070\portal-config.json --port 8896
```

Portal: http://127.0.0.1:8896/; backend: http://127.0.0.1:8895/. El código de acceso sigue en `engine/data/portal-v070/portal-access.txt`; no compartirlo ni copiarlo a informes. Para usar la reproducción nueva, sustituir ambos directorios por `portal-v070-reproduction-01`. No iniciar servicios duplicados en los mismos puertos.

Requisitos: Python >=3.11 (verificado con Python 3.13), dependencias existentes de `pyproject.toml`; `httpx` y `pytest` para las demostraciones ASGI y las pruebas. No se añadió dependencia externa. Si se crea otro entorno: `python -m pip install -e ".[test,integration]"`. La instalación puede necesitar red; la operación posterior del motor no.

## Ciclo implementado

`POST /monitoring/cycles` recibe mediciones nuevas y observaciones de contexto; compone adquisición, control de calidad, baseline elegido explícitamente, estadística existente, reglas normativas aplicables, rutas clínicas pertinentes, pruebas pendientes, episodios y planes de seguimiento. Una transacción con savepoints evita persistencia parcial. Identificador y contenido iguales permiten reintento; reutilizar el identificador con otro contenido se rechaza. `previous_run_id` debe identificar el último ciclo del sujeto/misión.

Cada decisión usa `as_of`, `history_start`, `clinical_window_start`, contexto y política declarados. El sistema no inventa frescura clínica ni intervalos de control: el dispositivo establece edad máxima; las observaciones manuales usan la ventana declarada, sin equivaler a frescura validada. Un adaptador debe llamar este endpoint al recibir un lote. El antiguo `POST /measurements` sigue siendo adquisición sin lanzar ciclos implícitos; no se añadió un daemon ni un planificador médico.

Los baselines se seleccionan por ID para evitar escoger silenciosamente una versión incorrecta. Se comprueban ámbito, vigencia, retirada, método, protocolo y anterioridad. Pendiente definir políticas clínicas independientes de cadencia, selección y expiración. Las tendencias usan pendiente por día y EWMA/CUSUM por observación; sus parámetros son configuración estadística, no límites diagnósticos aprendidos. Sin límite CUSUM validado no se emite señal clínica.

Eventos distinguen `CLINICAL_CRITERIA`, `NORMATIVE_REQUIREMENT`, `DATA_QUALITY` y `DESCRIPTIVE_CHANGE`. Toda evaluación conserva su registro. `notify` cambia cuando cambia el estado; un evento URGENT/EMERGENCY con evidencia pertinente nueva vuelve a notificar. Un cambio numérico descriptivo no genera alerta clínica. La ausencia de datos no cierra episodios. El seguimiento tiene fecha explícita del solicitante, no una pauta inventada. Las reevaluaciones conservan `parent_id`; no se autodeclara curación ni se completa un seguimiento clínico por un resultado favorable.

## Vigilancia espacial

| Dominio | Capacidad actual | Fuentes existentes | Límites |
|---|---|---|---|
| Cardiovascular | VO2, pulso, presión, comparación personal; regla AER-003; OH/POTS según contexto | S01, S05 | Incumplimiento normativo no es diagnóstico. Prueba ortostática estándar no aplicable en microgravedad libre; gravedad parcial requiere validación. |
| Musculoesquelético | Fuerza, densidad ósea por sitio, tendencias; regla MUS-002 | S01, S06 | DXA principalmente pre/postvuelo; no se supone disponibilidad en vuelo, diagnóstico de osteoporosis ni fractura. |
| Radiación | Suma explícita de dosis efectiva por intervalos compatibles; cobertura completa/parcial | S01, S16 | Solapamientos, cambio de protocolo o dosímetro no verificado bloquean total. Sin convertir dosis absorbida, órgano o tasa; no extrapola dosis de carrera ni riesgo de cáncer. |
| Sueño/comportamiento | Duración, eficiencia, reacción y escala de fatiga declarada | S10, S12 | Método y escala comparables; sin diagnóstico psiquiátrico ni umbral universal. |
| Inmunológico | Serie de carga viral, analito/muestra identificados mediante sitio y protocolo | S09 | Sin inferir reactivación a partir de PCR aislada; disponibilidad de laboratorio no presumida. |
| Electrolitos/oxigenación | Potasio, SpO2 y presión parcial ambiental descriptivos | SRC-DKA-2024, S14 | No son nuevas rutas diagnósticas. Seguridad de potasio para DKA permanece independiente. |

Cada respuesta separa indicadores disponibles/faltantes, problemas de calidad, fuentes, fase, gravedad, método y limitaciones. No mide masa ósea directamente en vuelo ni establece causalidad entre sistemas. Las reglas de retención aeróbica/muscular reutilizan el 80% del catálogo original, en simulación; no se modificaron umbrales.

## Nueva ruta: hipoglucemia

Fuente añadida: ADA, *Standards of Care in Diabetes—2026*, sección 6, tabla 6.4; DOI https://doi.org/10.2337/dc26-S006. Consulta de la publicación original indexada el 20-10-2026; el acceso directo a PMC mostró CAPTCHA, sin intentar eludirlo. El contenido indexado del editor permitió verificar la clasificación.

Implementación restringida a adultos con diabetes conocida. Nivel 1: glucosa <70 y >=54 mg/dL; nivel 2: <54. Nivel 3 requiere alteración funcional, necesidad de ayuda y atribución clínica al evento hipoglucémico, independientemente del valor de glucosa. Son alternativas AND/OR con cuatro estados, no diagnósticos etiológicos. Se aceptan plasma venoso o método capilar validado declarado; CGM aislado no activa esta ruta restringida. El factor de conversión existente a mg/dL es 18; el redondeo de equivalencias mmol/L requiere atención clínica en los límites.

La prioridad URGENT/EMERGENCY es una política experimental del software, no una escala de triaje validada. Fuera de la población admitida puede persistir una prioridad por glucosa baja sin emitir clasificación diagnóstica. Revisión de medicación, ingesta y ejercicio produce hipótesis externas, no causas confirmadas. Se propone nueva medición y revisión sin imponer un intervalo terapéutico. El protocolo de revisión permanece bloqueado por recursos/autorización, sin dosis ni ejecución.

La extensión `vigile/clinical_knowledge/v07-extension.json` tiene hash fijado; se combina en memoria con los nueve archivos clínicos originales. Los archivos científicos originales permanecen intactos. La ruta está disponible también en `/clinical/evaluations`, diferencial, fuentes y protocolos existentes.

## Escenarios y resultados observables

- A: baseline VO2=50; llega a 39 (78% de retención) con tendencia descendente. Se evalúa la regla normativa y se declara OH no aplicable en microgravedad. Después llega sensor inválido y dato tardío: no se rescata un valor anterior como estado actual normal.
- B: glucosa 50 con diabetes conocida satisface la ruta restringida, nivel mínimo 2 y prioridad urgente. Repetición sin evidencia nueva no notifica; glucosa nueva 49 sí. Ausencia posterior y dos valores simultáneos contradictorios impiden afirmar que los criterios siguen satisfechos; no se cierra el episodio.
- C: cuatro semanas sintéticas de fuerza, sueño, reacción, carga viral, SpO2, potasio y dosimetría. Registra 2.8 mSv de intervalos en la ventana, sin diagnóstico radiológico. Incluye una llegada futura no utilizable en ese ciclo. Faltan indicadores cardiovasculares y de densidad ósea: se muestran como faltantes.

Resultados finales detallados: `test-summary.json`, `tests-final.xml`, `demo-summary.json`, `live-checks.json`. 490 pruebas aprobadas (460 conservadas y 30 nuevas). 15/15 reproducciones de ciclos y 20/20 de evaluaciones clínicas verificadas por HTTP real. Reader puede leer sus ámbitos y no escribir. El asistente local ejecutó inferencia y respondió; consulta de datos faltantes siguió el contrato determinista sin inferencia. Ninguna consulta modificó los registros persistentes.

La prueba generativa encontró `NO_MATCHING_DOCUMENT_EXCERPT`: explicó evidencia estructurada del motor y accedió a la referencia bibliográfica, sin un nuevo extracto de texto completo en el índice RAG. No se amplió ni reconfiguró RAG. El campo versión del servicio portal existente conserva su versión de componente 0.6.0; backend, paquete y vista son 0.7.0.

## Archivos y compatibilidad

Nuevos módulos: `monitoring.py`, `monitoring_models.py`, `monitoring_demo.py`, `monitoring_portal_demo.py`; extensión de conocimiento y `tests/test_monitoring.py`. Modificados: adquisición/unidades, transacciones, episodios, modelos/motor/diferencial/registro clínico, API, seguridad, proyección dashboard y dos assets web. El manifiesto enumera los archivos y hashes exactos.

No hay migración destructiva de SQLite: se agregan tipos de registro. Se conservaron las bases anteriores. La reproducción histórica exige el código y conocimiento originales; no se reescriben sus hashes para hacerlas pasar con v0.7. `before-v07.zip` conserva el código previo. `release-source.zip` conserva esta versión sin credenciales ni bases. El nuevo código y la extensión deben distribuirse juntos.

## Límites y próximos trabajos

1. Revisión clínica independiente de la nueva ruta, prioridades, población, muestras y aplicabilidad espacial. Ninguna prueba sintética sustituye esta revisión.
2. Protocolos aprobados para cadencia, calidad, baselines, confirmación, seguimiento y respuesta humana. La monitorización no constituye un sistema de alarma operacional validado.
3. Sensores reales: calibración, trazabilidad de muestras, artefactos, unidades y autenticación del origen; no basta declarar un método validado.
4. Seguridad de despliegue: SQLite sin cifrado; archivos locales de credenciales requieren ACL y aislamiento. Un atacante con control del almacenamiento puede reescribir una cadena de auditoría; necesita anclaje externo o firma para resistirlo. Mantener procesos, roles y secretos separados.
5. Escalabilidad: snapshots completos y lectura histórica crecen con la misión; no hay archivo incremental ni paginación de ciclos. Máximo 256 mediciones y 256 observaciones por petición, 32 baselines; ventanas/contextos explícitos deben acotar el arrastre clínico. No se ha validado carga de meses de datos continuos ni hardware de vuelo.
6. Investigación antes de activar rutas diagnósticas de potasio/oxigenación o causalidad multisistema. Documentos offline del nuevo criterio deben incorporarse al RAG con licencia y procedencia por su responsable.

El núcleo está listo para integración experimental del equipo, con los límites indicados. No está validado para atención real, autonomía terapéutica ni uso operacional espacial.

## CONTEXTO PARA CONTINUAR CON CHATGPT

Versión v0.7.0 en el proyecto existente; base activa `engine/data/portal-v070`. Backend 8895, portal 8896, Ollama 8891 con `vigile-qwen3-4b:latest` sin cambios. Siete rutas clínicas; cinco dominios espaciales y una vista descriptiva adicional. Sensores/simuladores envían `POST /monitoring/cycles`; frontend lee la nueva proyección `monitoring` del dashboard; RAG conserva reader y consulta evaluaciones/fuentes, sin escritura. El ciclo evalúa reglas de forma determinista y guarda snapshots reproducibles. Usar los comandos de arriba y los ejemplos en `CONTRACTS.md`/`examples/`. Antes de modificar código conservar versión: el hash de implementación cambia con los módulos Python y las reproducciones se bloquean si no corresponde. No ampliar diagnósticos ni habilitar tratamiento sin evidencia y revisión clínica independiente.
