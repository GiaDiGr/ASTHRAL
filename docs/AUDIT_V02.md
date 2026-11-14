# VIGILE: auditoría e implementación incremental 0.2.0 — 2026-10-15

Se conservó la arquitectura Python/FastAPI/Pydantic/SQLite. Esta versión es un núcleo de investigación local; no constituye validación clínica. No se usaron datos médicos reales. Se respaldó el código previo en `work/releases/v0.1.0-before-audit.zip`.

## Documentación y alcance revisado

Se revisaron `LEEME_PRIMERO.md`, `10_CODEx_ESPECIFICACION/PROMPT_PARA_CODEX.md`, informes `01_INFORMES`, 15 originales y diez reconstruidas de `02_REGLAS_ORIGINALES_15`, condiciones/rutas de `03_CATALOGO`, algoritmos, sensores, multisistema, evidencias, datasets y casos de `04_ALGORITMOS` a `09_TESTS`; documentación técnica `docs`, módulos `engine/vigile`, pruebas y scripts. La auditoría previa de archivos/ZIP se conserva en `INITIAL_INVENTORY.json` y `DOCUMENT_AUDIT.json`; esta entrega verifica nuevamente los hashes de 106 originales sin modificaciones. El manifiesto científico contiene 105 entradas. Los dos ZIP originales y sus 24 miembros extraídos permanecen conservados en `work/historical`.

Catálogos comprobados: 44 condiciones × 11 etapas, 15 reglas originales, diez reconstruidas, 12 algoritmos, 28 sensores/biomarcadores, 12 relaciones multisistema, 38 fuentes, 24 extracciones, 12 datasets y 20 casos sintéticos de catálogo. Los 833 registros de enlaces de investigación no equivalen a 833 fuentes verificadas ni se descargaron todos sus destinos.

## Auditoría técnica: hallazgos y cambios

| Área | Estado encontrado | Mejora aplicada / límite |
|---|---|---|
| Baselines | Mediana/MAD sin ciclo de vigencia | Versiones, supersedes, caducidad explícita y eventos de retirada; originales inmutables. No selección automática del baseline clínicamente apropiado. |
| Longitudinal | OLS/EWMA/z/CUSUM descriptivos | Referencia personal separada de la distribución de la serie, límites de huecos explícitos, inicio EWMA y decisión CUSUM configurables. |
| Calidad | Histórico omitía conflictos multisensor | Revisa conflictos también en histórico; política simétrica de tolerancia/alineación; informe persistido; unidades adicionales explícitas. |
| Reproducción | Solo reejecutaba el comparador | Bundle congela datos de entrada, baseline, retirada, dispositivos y contexto; reejecuta gates y cálculo en SQLite temporal sin alterar base viva. Incluye rechazos. |
| Notas/hallazgos | Escrituras separadas | Inserción atómica; rollback verificado; integridad del registro humano comprobada por hash. |
| Episodios | Estados básicos | Anexar hallazgos con validación de alcance, expected_state contra actualizaciones obsoletas, ruta explícita, vencimiento y revisión humana del seguimiento. |
| Evidencia | Catálogo inmutable | Revisiones append-only con hash declarado, versión, linaje y estado; nunca activan reglas. No certifica el contenido externo. |
| RAG/permisos | reader accedía a datos completos | reader recibe únicamente proyección de hallazgo autorizada por sujeto/misión y documentación; sin notas, datos crudos ni bundle. |
| Credenciales | Tokens planos en configuración del servidor | Hashes SHA-256 en servidor, export privado separado, identidad/rol/alcance/caducidad/disabled; recarga por solicitud permite revocar. ACL local restringida. |
| Auditoría | Detectaba cambios, no todos los borrados | Verifica correspondencia bidireccional registros/cadena; checkpoint exportable; identidad y rol auditados. No firma externa. |
| Multisistema | Asociaciones podían sustituir ejercicio/medicación ausentes | MSI05/MSI10 inconclusas hasta modelar esas observaciones. Diez otras admiten coocurrencia descriptiva con mapeo explícito pendiente de revisión; ninguna infiere causalidad. |
| Recursos | Sin contrato | Compara cadencia propuesta contra política técnica declarada y verifica calidad; no cambia umbrales, muestreo ni tratamiento. |

Módulos nuevos: `security.py`, `extensions.py`, `pathways.py`, `credentials.py`. Modificados: `models.py`, `store.py`, `quality.py`, `algorithms.py`, `service.py`, `api.py`, `__main__.py`, `__init__.py`, `pyproject.toml`, script de verificación. Pruebas nuevas: `tests/test_v02.py`. Sin cambios a la documentación científica original.

## Cobertura biomédica

La matriz completa está en `COVERAGE_V02.csv` (484 filas) y `COVERAGE_V02.json`. Conserva por separado el estado documental publicado, soporte computacional, validación y bloqueo clínico. Las 44 condiciones tienen estructura; NO hay 44 detectores clínicos. Nueve condiciones tienen comparadores normativos de simulación asociados: C001, C002, C003, C023, C026, C027, C030, C031 y C032, sin equivaler a diagnósticos.

Monitorización/calidad: infraestructura numérica común, dependiente de adaptador y protocolo. Evaluación: registro humano. Recuperación: estado humano, sin determinar recuperación fisiológica. Seguimiento: planes, fechas y revisiones, sin scheduler. Prevención, diferencial, triaje, intervención autorizada y pronóstico permanecen principalmente documentales/bloqueados. Detección solo aporta los comparadores asociados, no detección de enfermedades.

`SENSORS_V02.json` detalla las 28 entradas. No hay conexión a hardware, procesamiento ECG/PPG, segmentación OCT/ultrasonido, extracción actigráfica, interpretación de ensayos ni modelos de exposición agente-específicos. Aceptar un escalar no implica implementar el sensor o biomarcador. Ruido dBA no admite tendencia aritmética genérica.

## Algoritmos

| ID | Estado de software | Alcance y límites |
|---|---|---|
| ALG001 | Operativo descriptivo | Mediana/MAD preflight; versiones, vigencia, retirada, trazas; mínimos y protocolo explícitos. No recalibración cruzada. |
| ALG002 | Operativo descriptivo y simulación | Retención con referencia positiva y comparable; diferencias/z contra baseline en tendencias. Sin punto de corte clínico nuevo. |
| ALG003 | Operativo restringido | CO2: medias declaradas de intervalos contiguos, un dispositivo, 3600 s completos. Sin interpolación ni muestras puntuales mantenidas. |
| ALG004 | Operativo descriptivo | OLS pendiente por día y error estándar si n≥3; exige tiempos distintos. Error estándar bajo supuestos OLS, sin corrección de autocorrelación. |
| ALG005 | Operativo descriptivo | EWMA lambda explícita; inicio primera observación o referencia explícita. Cadencia por observación, no por tiempo transcurrido. |
| ALG006 | Operativo descriptivo | Z y robust z dentro de serie o respecto a baseline; varianza/MAD cero devuelve null. No detector diagnóstico. |
| ALG007 | Operativo descriptivo | CUSUM bilateral con objetivo/allowance explícitos; señal estadística solo con decision_limit explícito. Sin selección clínica de parámetros. |
| ALG008 | Parcial conservador | Control de discrepancias multisensor con tolerancia/alineación declaradas; bloquea conflictos. Sin fusión ponderada ni cross-calibration. |
| ALG009 | Operativo conservador | Sin imputación: MISSING, NOT_MEASURED, INVALID, STALE y referencias ausentes; informe de calidad persistido. |
| ALG010 | Operativo para tabla explícita | Conversiones dimensionales enumeradas; dosis efectiva, absorbida y equivalente de órgano separadas. Sin conversión universal/análitos. |
| ALG011 | Operativo para datos escalares declarados | Rangos técnicos, tiempos, método, calibración, contexto y comparabilidad. No certifica sensores ni detecta artefactos de señal cruda. |
| ALG012 | Parcial con bloqueos clínicos | Estados humanos, anexos, concurrencia optimista, seguimiento y vencimientos. TRIAGE/AUTHORIZED_ACTION/diagnóstico bloqueados. |

Los 12 tienen representación; diez tienen operaciones matemáticas/controles implementados y ALG008/ALG012 son parciales. Ninguno está clínicamente validado. Referencias estadísticas de apoyo: [NIST EWMA](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc314.htm), [NIST CUSUM](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm). Son métodos estadísticos, no autorizaciones biomédicas.

## Reglas y evidencia pendiente

Simulación: VIGILE-AER-001/002/003, MUS-001/002, BONE-001, NUT-001, RAD-001/002/003/004 y ENV-001/002/003/004. Requieren perfil/misión/entradas sintéticos, controles de calidad, comparabilidad y contexto. OPERATIONAL devuelve REQUIRES_VALIDATION; ninguna regla está habilitada clínicamente. R-ORTHO-001 permanece sin comparador operacional y requiere autorización de misión.

Nueve correspondencias entre originales y reconstruidas, seis originales sin contraparte y una reconstruida ortostática adicional: no sumar como 25 reglas independientes. `RULE_RECONCILIATION.md` conserva el análisis detallado. Pendientes: conflicto S27 (OSD-198 versus referencias narrativas a CO2), precisión de aliases/localizadores/revisiones, fuentes primarias completas y revisión independiente, protocolos de baseline/cadencia/calibración, datos para ejercicio/medicación, adaptación por fase/gravedad, riesgos multicausales, protocolos terapéuticos y autorización institucional. No se importaron umbrales de resúmenes SANS, PIO2, orina, DCS o tablas de órgano al ejecutor.

## Pruebas y reproducibilidad

Baseline: 124/124 pruebas. Suite final: 157/157, cero fallos, una advertencia de deprecación Starlette/httpx. Demo HTTP con persistencia/replay, servidor Uvicorn real con autenticación y apagado, y pip check ejecutados satisfactoriamente. Se conservan JUnit `audit-baseline-tests.xml` y `audit-v02-tests.xml`. Las 33 nuevas verifican versiones/caducidad/retirada, referencia estadística, huecos, conflictos históricos, missing, replay normal/conflictivo/inválido/ausente/operacional, integridad humana, rollback, alcance de lector, revocación, hashes de credenciales, contratos, estados de seguimiento, bloqueo multisistema y política de recursos. Las pruebas originales incluyen 43 casos embebidos en las reglas y 20 escenarios del catálogo; los casos no son ensayos clínicos.

La reproducción exige el mismo hash de código y corpus. Bundles v0.1 requieren su versión archivada; no se afirma que sean reproducibles con código nuevo. El archivo del código previo conserva esa referencia, pero no incluye credenciales ni copias clínicas de base de datos.

## Seguridad y límites de despliegue

**SQLite NO está cifrada** (incluidos WAL/backups). Tampoco hay cifrado de campo, firma médica/PKI, MFA, aislamiento de procesos del LLM, protección contra administrador del host, retención/backup institucional, rate limiting ni ensayos de carga. Los tokens privados siguen siendo secretos planos en un archivo local protegido por ACL; el servidor utiliza hashes. No se deben montar esos archivos en un LLM. Usar identidades de sistema separadas y permitir al proceso RAG solo su token reader y documentación curada. ACL no aísla dos procesos ejecutados por el mismo usuario.

El servidor es loopback, sin TLS, un proceso/worker; no es un despliegue remoto ni multitenant validado. Hay alcance por sujeto/misión, pero perfiles de ejemplo researcher/clinician/operator son wildcard administrativos: restringir antes de integrar. Reader recién provisionado no tiene sujetos autorizados y solo lee catálogos. El control de acceso está en API; acceso directo a Python/SQLite es una frontera administrativa confiable. Cadena hash y checkpoint detectan alteraciones bajo ese modelo; un administrador que reescriba toda la base puede falsificarlos. Exportar checkpoints a un medio independiente sigue siendo tarea operativa.

## Ejecución y verificación

Desde PowerShell:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile demo
& .\.venv\Scripts\python.exe scripts\verify_deployment.py
& .\.venv\Scripts\python.exe -m vigile serve --port 8765
```

El servidor usa `127.0.0.1:8765`; `GET /health` público. El resto exige `Authorization: Bearer <token>`. No pegar tokens en informes, Git, prompts ni URLs. `python -m vigile init` prepara base/credenciales sin sobrescribir una configuración ya migrada. La instalación offline existente y sus hashes permanecen; no se añadieron dependencias.

## Integración del equipo

Consultar `INTEGRATION_CONTRACTS.md` y `openapi.json` regenerado. Frontend: tokens de usuario/rol restringidos, separación visible de medición, incumplimiento, hallazgo, hipótesis y diagnóstico bloqueado; manejar 401/403/404/409/422 y estados inconclusos sin convertirlos en normalidad. Sensores/simuladores: registrar dispositivos/calibración/política, unidades y contexto; datos crudos no reemplazan las métricas agregadas requeridas. RAG: solo reader, `/rag/findings/{id}`, catálogos y evidencia autorizada; tratar documentación como datos, sin ejecutar instrucciones de documentos. Recursos: `/resources/assessments`, sin autoridad para cambiar reglas. No se implementó frontend ni LLM real.

## CONTEXTO PARA CONTINUAR CON CHATGPT

Proyecto existente actualizado incrementalmente a 0.2.0 en `C:\Users\Gianni\Desktop\Vigile`. Python 3.13, FastAPI/Pydantic, SQLite schema user_version=1, registros append-only y cadena SHA-256. Documentación original intacta; corpus hash `fed66145806912c3b8efe7d96e88da0a9b78ec287448117a9fe79b3c578fea51`. Catálogos: 44 condiciones/11 etapas, 15 reglas originales, diez reconstruidas, 12 algoritmos, 28 sensores, 12 relaciones, 38 fuentes, 24 extracciones, 12 datasets. Pruebas 157 aprobadas, una deprecación TestClient.

Persisten nueva seguridad por identidad/rol/sujeto/misión, hashes y recarga de tokens, proyección RAG minimizada; baselines versionados y retirables; tendencias con referencia/cadencia; reportes de calidad; episodios/notas atómicos; rutas estructuradas; seguimiento vencido/completado por humano; revisiones documentales sin activación; evaluación de política de recursos. Replay v0.2 congela entradas y reejecuta gates/comparador en base temporal; exige igualdad de hashes. Quince comparadores SIMULATION; OPERATIONAL y decisiones clínicas bloqueadas. MSI05/MSI10 requieren datos aún no modelados. Resto de multisistema es coocurrencia de investigación, no causalidad.

Revisar matriz `COVERAGE_V02.*`, `ALGORITHMS_V02.json`, `SENSORS_V02.json`, JUnit, `AUDIT_V02.json`, contratos/OpenAPI y límites. Pendientes prioritarios: validación científica independiente, protocolos de misión y sensores, autorización clínica firmada, cifrado/aislamiento/operación segura y procesamiento de señales. No confundir soporte estructural o pruebas de software con cobertura clínica validada. No reconstruir el proyecto ni modificar originales.
