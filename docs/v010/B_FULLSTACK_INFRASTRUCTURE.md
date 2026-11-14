# B. Desarrollo Full-stack / Infrastructure v0.10.0

Cierre de entrega: 24 de octubre de 2026, America/Lima. Mediciones iniciales: 23 de octubre. Prototipo integrado de investigación; exclusivamente datos sintéticos.

## Resultado y continuidad

Se reutilizaron FastAPI, SQLite, el BFF reader y los paneles existentes. No se reconstruyó el sistema. Se mantienen las siete rutas clínicas, el diferencial, monitorización espacial, biblioteca RAG v0.8, Ollama 0.40.6 y `vigile-qwen3-4b:latest` en 8891. No se modificaron criterios, dosis, autorizaciones ni tratamientos. No se ejecutaron las 12 preguntas reservadas.

Base de entrega: `engine/data/portal-v0100-integrated`. Backend 8895; portal 8896. Las bases anteriores, incluida `portal-v090-release`, se conservan. Las carpetas `portal-v0100-release` y `portal-v0100-final` son preparaciones intermedias, no la base activa; sus archivos también se conservan.

Huella final Python: `c896211d20b52ade1279aeb306421891f5e29b542f910074d542321c4b815db9`.
Conocimiento clínico: `b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e`.

## Interfaz y defectos corregidos

Cinco áreas mediante los paneles originales: estado general, monitorización, evaluación clínica, seguimiento y asistente. Navegación de teclado con foco visible; en pantalla estrecha la navegación permanece accesible con desplazamiento horizontal propio, sin ocultar secciones. Campos etiquetados, detalles técnicos desplegables, tablas desplazables y contraste reforzado.

Se corrigieron la respuesta pendiente del chat/replay al cambiar de sujeto, el botón que podía habilitarse desde una respuesta obsoleta, datos del contexto anterior visibles mientras se cargaba otro, el resumen que podía ocultar una urgencia clínica si no existían ciclos de monitorización y un desbordamiento horizontal en criterios. El chat borra su historial al cambiar de sujeto, evaluación, contexto o ciclo.

Los indicadores del ciclo seleccionado se presentan desde el resultado del motor y su ID de medición, no desde una muestra futura o inválida llegada después. Las series del ciclo utilizan sus IDs de entrada; no unen ausencias ni imputan valores. Se muestran unidad, baseline, cambio descriptivo, calidad y estado temporal. Los resultados inválidos y no medidos no se convierten en normalidad. Los ciclos históricos, episodios y planes de seguimiento permanecen consultables; no se infiere recuperación automática.

Las fechas se muestran con America/Lima y zona PET/GMT-5 explícita; timestamps originales y hashes permanecen en detalles. El criterio DKA de la demostración conserva bicarbonato/cetonas urinarias como alternativas no medidas y potasio como seguridad pendiente. La interfaz no recalcula ni modifica ese resultado.

## Seguridad del portal

- Sesiones con tokens aleatorios de 256 bits, identificadores almacenados como SHA-256, máximo 128 sesiones.
- Inactividad 900 s, límite absoluto 28800 s. Renovación explícita con rotación de cookie; no prolonga el límite absoluto ni reinicia los contadores de solicitudes. El sondeo de estado no renueva la inactividad. Reiniciar el portal invalida sus sesiones en memoria.
- Cookie HttpOnly y SameSite=Strict. Secure solo si el transporte es HTTPS; en HTTP de loopback no se afirma protección TLS.
- Validación exacta de Origin en POST, rechazo cross-site y Host distinto de 127.0.0.1, políticas CSP/no-store/nosniff/referrer/permissions.
- Cuerpo máximo 16 KiB, preguntas acotadas, historial máximo 3 entradas. 120 lecturas/minuto y 12 consultas de asistente/minuto por sesión, más rechazo de inferencia concurrente. 429 explícito, sin normalidad clínica.
- Login acotado y verificación de identidad reader en backend. No hay proxy arbitrario ni rutas de escritura del motor desde el portal. Los permisos por sujeto/misión se siguen verificando en el backend.
- Errores seguros: 401 sesión, 403 origen/permisos, 404 resultado/documento desconocido, 413 tamaño, 422 entrada/respuesta inválida, 429 saturación, 502 servicio/credencial reader inaccesible, 503 almacenamiento o biblioteca. No se exponen excepciones internas ni rutas secretas.
- La nueva proyección de episodios/seguimiento filtra por sujeto y misión antes de relacionar planes. No se concede ningún permiso researcher al navegador ni al modelo.
- El navegador conserva solamente su cookie de sesión. Reader/backend tokens se leen en el servidor. El lanzador de Ollama filtra variables de entorno VIGILE y nombres que indiquen tokens, secretos, contraseñas o API keys; no cambia configuración global.

## Almacenamiento: estado real

Los tres archivos de credenciales de la **base nueva** están protegidos con Windows DPAPI de usuario. El directorio nuevo y el de integridad tienen ACL para usuario actual y SYSTEM. Se comprobó que `reader-token.txt` hereda únicamente esas entradas. Las credenciales históricas se conservan en su formato original: esta compatibilidad no significa que todas las copias antiguas estén cifradas ni revocadas.

DPAPI utiliza la protección del usuario Windows; otros procesos de la misma cuenta pueden solicitar descifrado. No es una frontera entre procesos del mismo usuario. Referencia primaria: [Microsoft CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/seccrypto/example-c-program-using-cryptprotectdata).

Copias SQLite mediante snapshot de lectura y API backup; comprobación de integrity_check, igualdad de registros/auditoría y SHA-256 del archivo. Restauración en una carpeta nueva, sin sobrescribir una base. Se restauraron 244 registros de v0.9 y se reprodujeron sus 39 evaluaciones/ciclos con el código original archivado. El resultado está en `archived-v09-replay-check.json`; huella original `db3684fe14e362e69d496b882669fdcc2a0ef661db134ed8c6339ff18eb6dab1`.

Anclaje externo HMAC-SHA256 de un checkpoint de registros y auditoría, con clave aleatoria protegida por DPAPI. Ubicación fuera de las bases: `%LOCALAPPDATA%/Vigile/integrity`. Verificación de prefijo firmado y de la cadena completa; admite nuevos registros posteriores y los distingue del checkpoint. Una regresión demuestra que recalcular la cadena interna tras manipular registros no coincide con el anclaje externo.

Esto **no** impide al atacante que controle la misma cuenta, el código y la clave recalcular también el anclaje. No es almacenamiento WORM, HSM ni firma de un tercero. Las claves no se incluyen en el paquete de código. Debe diseñarse recuperación de claves y reaprovisionamiento en otro equipo: copiar un archivo DPAPI no garantiza poder descifrarlo en otra cuenta/máquina.

**SQLite continúa sin cifrado.** `PRAGMA cipher_version` no informa un proveedor cifrado activo; SQLCipher no está disponible. `encrypted_storage.py` prepara una conexión opcional que rechaza claves/proveedores no verificables y nunca cae silenciosamente a SQLite plano; no está conectada a Store ni se ejecutó migración. Una integración real requiere una compilación SQLCipher compatible, revisión de distribución/licencia, copia previa, migración verificada, restauración y todos los replays. [API oficial SQLCipher](https://www.zetetic.net/sqlcipher/sqlcipher-api/).

## Aislamiento: controles y pendiente

Loopback limita exposición de red, pero Ollama no tiene autenticación propia y otros procesos locales pueden consultarlo. ACL, DPAPI y separación de credenciales reducen exposición entre cuentas/archivos; no se instaló sandbox ni aislamiento de procesos de la misma cuenta. El estado público declara `SAME_USER_NOT_ISOLATED`.

Un aislamiento fuerte exige despliegue bajo identidades separadas y una frontera de red/proceso efectiva: servicio restringido, VM o AppContainer/WFP con política verificada para el runtime y acceso autorizado desde el BFF. Requiere privilegios de administración, componentes compatibles y prueba específica de loopback; una regla de firewall genérica no se presume suficiente. Windows Home y este despliegue no tienen esa solución configurada. No se hicieron cambios globales de firewall, antivirus o Norton; no se restauró ningún ejecutable en cuarentena.

## RAG, explicaciones y compatibilidad

El frontend separa ENGINE, extractos DOCUMENT, explicación generada y fallback/rechazo. Muestra autoridad, versión y procedencia; advierte que pertinencia recuperada no está validada. El endpoint de fragmento exacto verifica manifest, hashes, offsets y fuente admitida; rechaza contenido alterado o en cuarentena y no acepta rutas del sistema de archivos.

Se conserva la limitación de recuperación previamente documentada: pasaje esperado 4/12 top-3 y 8/12 top-5. Una referencia o puntuación no transforma un documento en resultado del paciente ni evidencia definitiva. No se debilitó el filtro del modelo para aumentar aceptación.

El portal añade `inference_trace`: solicitudes de modelo intentadas y aceptación de explicación. El campo histórico `inference_executed` se conserva por compatibilidad, pero no debe usarse como contador de ejecución; algunas rutas lo dejan falso al rechazar una generación. Una solicitud intentada tampoco demuestra inferencia terminada. `runtime.loaded` puede ser true, false o null; CRITICAL declara que no observar o no inferir no significa descargar memoria.

Contratos aditivos en `INTEGRATION_CONTRACTS.md`, `backend-openapi.json` y `portal-openapi.json`. No se retiraron endpoints ni campos existentes.

## Verificación y límites de las pruebas

Suite original: 545 aprobadas. Suite de entrega: **561 pruebas, 0 fallos, 0 errores**, 107.86 segundos. Archivo `release-tests.xml`. Un aviso de deprecación Starlette/httpx; no se actualizaron dependencias durante esta entrega.


Regresiones nuevas: sesiones/rotación/expiración con reloj controlado, límites conservados al renovar, DPAPI y no sobrescritura, backup/restauración/alteración, anclaje frente a auditoría recalculada, capacidad de cifrado sin afirmaciones falsas, 429, 403, 404, límites de cuerpo, 503 de SQLite por fallo inyectado, degradación de estado, reproducción scoped, consulta documental exacta y manifest alterado, metadatos de inferencia. No se borró ni corrompió la base activa para simular un fallo.

Pruebas reales de servicios: caída/reinicio del backend y Ollama, acceso de solo lectura durante caída de IA, recuperación de modos y rechazos sin filtración. Caducidad de sesión se probó con reloj inyectado; no se afirma una espera manual de ocho horas. La prueba sostenida cubre 601 s, no días de operación.

`release-verification.json`: 39 replays coincidentes; comparación exacta de resultados, urgencia, pruebas, diferencial, protocolos, tratamiento y conocimiento en las 24 evaluaciones de v0.9/v0.10; cadena válida, anclaje válido y banco reservado intacto. No se equiparan estos resultados a validación clínica.

## Referencias dependientes de versión

La comparación cruda de dominios no es idéntica byte a byte: 8 ciclos cambian únicamente `normative_finding_id`, la referencia a un hallazgo normativo de la implementación correspondiente. Los demás valores, estados, tendencias y campos de los 15 dominios/ciclos coinciden al excluir solo esa referencia. Eventos y relaciones coinciden. Se conservan las diferencias completas en `monitoring-version-differences.json`; `release-verification.json` muestra tanto la comparación cruda como la igualdad de valores descriptivos. No se promete igualdad de IDs/hash de salida entre versiones. Cada base se reproduce con su propia implementación, y el código histórico archivado reproduce los 39 registros originales.

## Archivos principales modificados y añadidos

| Archivo | Cambio |
|---|---|
| engine/vigile/portal.py | Sesiones, origen, errores, runtime, replay/documentos y traza de intentos |
| engine/vigile/portal_sessions.py | Caducidad, rotación y admisión acotadas |
| engine/vigile/local_protection.py | DPAPI, ACL, copia/restauración y anclaje externo |
| engine/vigile/encrypted_storage.py | Frontera opcional SQLCipher, sin migración habilitada |
| engine/vigile/portal_documents.py | Fragmento exacto verificado |
| engine/vigile/dashboard_api.py | Episodios y seguimiento scoped |
| engine/vigile/local_assistant.py | Allowlist reader para GET replay, sin escritura |
| engine/vigile/api.py | Secretos DPAPI compatibles y versión |
| engine/vigile/web/{index.html,style.css,app.js} | Cinco áreas, contexto, calidad, gráficos, fuentes y sesiones |
| engine/tools/start_ollama_vigile.py | Entorno del runtime sin secretos heredados |
| engine/pyproject.toml | Versión 0.10.0 |
| engine/tests/test_local_protection_v010.py, test_portal_v010.py | 16 regresiones nuevas |
| docs/v09/benchmark_compute.py | Recolector corregido por fecha de creación; original archivado |
| docs/v010 | Informes, contratos, scripts, datos crudos, OpenAPI y capturas |

## Demostración y revisión visual

Capturas en `screenshots/`; pasos reproducibles en `DEMO.md`. Se verificaron escritorio y anchura estrecha, criterios DKA, alternativas ausentes, potasio pendiente, protocolo bloqueado, monitorización longitudinal, ciclo histórico, ausencia/invalidación, historial/replay, modo reducido y respuestas sin generación. Las capturas de caída de Ollama pertenecen a la interrupción controlada; las finales usan la base integrada. Las diferencias de IDs aleatorios entre preparaciones no son un cambio de criterio.

## Condiciones pendientes

1. Antes de cualquier uso clínico: revisión sanitaria independiente, aplicabilidad espacial, suficiencia de sensores, autorizaciones y procesos humanos; tratamientos siguen bloqueados.
2. Aislamiento real de procesos y protección de la interfaz local sin autenticación de Ollama.
3. Cifrado completo de SQLite y plan de recuperación de claves/copias; las copias también son texto plano.
4. Revisión humana de pertinencia documental y omisiones del asistente; los 12 casos reservados siguen sin usarse.
5. La carga sostenida obtuvo 75 fallbacks y ninguna explicación aceptada; no confundir HTTP 200 con éxito generativo. Carga prolongada, presión de recursos, potencia instrumentada y hardware objetivo; no se declaran ahorro energético ni aptitud de vuelo.
6. Auditoría de seguridad externa y pruebas de accesibilidad con usuarios; no se afirma que una inspección visual sustituya esas evaluaciones.

## CONTEXTO PARA CONTINUAR CON CHATGPT

VIGILE v0.10.0 activo en `engine/data/portal-v0100-integrated`; huella Python c896211d20b52ade1279aeb306421891f5e29b542f910074d542321c4b815db9. Motor clínico sin cambios documentales ni numéricos; 24 vectores clínicos idénticos, 39 replays, 561 pruebas aprobadas. Portal con cinco áreas y contratos aditivos reader; Ollama/modelo conservados, sin credenciales de escritura en navegador/LLM. ACL y DPAPI aplicados solo a directorios nuevos; SQLite y backups no cifrados. HMAC externo bajo LocalAppData, vulnerable al control de la misma cuenta/código/clave. SQLCipher preparado pero bloqueado como integración activa. Banco reservado intacto. Arranque, demostración y comandos exactos en README.md y DEMO.md. No ampliar catálogo ni afirmar validación clínica/operativa/espacial a partir de esta entrega.

Comprobación visual final: se corrigió la sincronización entre curva y tabla al cambiar variable, se conservó la evaluación al refrescar el mismo contexto, se mostraron antigüedades relativas al ciclo y se bloquearon selectores mientras cargan datos. Las regresiones reales de tabla verifican VO2 48/44/39 mL/min/kg y frecuencia 65/72/79 bpm con sus IDs de origen. Detalles cerrados omiten contenido de innerText: una primera aserción de inspección se ajustó para abrir la tabla antes de verificar unidades; la tabla abierta pasó la comprobación. Evidencia en screenshots/visual-checks.json.
