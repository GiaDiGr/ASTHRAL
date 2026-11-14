# A. Auditoría Full-stack / Infrastructure v0.10

24/10/2026. Sólo datos sintéticos. Se revisaron los cinco documentos solicitados de docs/v010 y el código de portal, frontend, sesiones, permisos, reader, generación/verificación, proyecciones y almacenamiento. No es una nueva auditoría clínica ni una validación independiente del LLM.

## Referencia preservada

Inicio: 561 pruebas aprobadas en 106 s; 244 registros verificables y backup v0100-before-v011. before-v011.zip conserva el código; archived-v010-replays.json confirma 39 replays (24 clínicos, 15 de vigilancia). Los servidores 8895/8896 usan la versión archivada c896211d20b52ade1279aeb306421891f5e29b542f910074d542321c4b815db9. Base y credenciales anteriores no se sobrescribieron. Sólo se reiniciaron ambos servidores VIGILE identificados y sin conexiones activas; las sesiones anteriores caducan. Ollama no se detuvo ni reconfiguró.

## Defectos corregidos

- El dashboard actual no reconstruía recepción histórica: frames inmutables por ciclo, sin incorporar datos tardíos retroactivamente.
- Contexto de misión estático: fases sintéticas append-only con fecha efectiva, congeladas en los motores existentes.
- Hallazgos y errores tardíos al cambiar contexto: limpieza, controles deshabilitados y descarte por generación de solicitud. Seleccionar ciclo con frame cambia toda la vista.
- Referencia a frame ajeno: autorización del frame en middleware; 403 para acceso cruzado.
- Plan sintético rotulado como humano: aclaración de que no acredita revisión humana ni recuperación.
- ValueError ocultaba causas del fallback: taxonomía pública acotada y etapa; nunca excepciones arbitrarias o secretos.
- Consultas genéricas ignoraban pruebas/documentos existentes: recomendaciones deterministas y extractos explícitos, sin inventarlos ni simular generación.
- Residuos de coma flotante: hasta tres decimales sólo en tarjetas; datos completos y cálculos conservados.

## Los 75 fallbacks

Los registros antiguos no contienen causa exacta por ValueError. No se atribuye retrospectivamente una causa única a los 75 HTTP 200. HTTP 200 no acredita generación aceptada.

fallback-probes-v010.json registra seis reproducciones nuevas de la pregunta de baseline: tres FULL y tres LOW_POWER. Todas hicieron una solicitud y se rechazaron antes del verificador por CLINICAL_CLAIM_REQUIRES_EXACT_ENGINE_TEXT. Sin saturación, timeout ni fallo HTTP de inferencia observados en esas seis. Una salida atribuía un baseline cardíaco y ausencia de significación clínica no establecidos por su soporte. El guard se mantiene intacto.

Un primer preflight del estado del portal excedió diez segundos antes de inferencia; causa no establecida. Se distingue de los rechazos posteriores. Una ejecución de desarrollo aceptó una explicación de reevaluación; la final no aceptó ninguna de sus ocho preguntas. assistant-final-real.json y RESULTS.json conservan resultados reales. No se repitió la auditoría general RAG ni se usaron casos reservados.

## Pruebas y UX

Entrega: 582 pruebas aprobadas en 164,37 s; una advertencia Starlette/httpx (release-tests.xml). Incluye sesiones, expiración/renovación, cookies, origen/cross-site, rate limits, tamaño, errores sin secretos, roles/ámbitos, reader sin escritura, adquisición, persistencia, desconexión, contexto y replays. XML de desarrollo con fallos conservados.

Recorrido visual autenticado con código de prueba propio DPAPI y sólo astronautas sintéticos: escritorio 1280 px y pantalla 390 px, sin desbordamiento global; Tab/Enter llega a Seguimiento. DKA separa criterios, confirmación, urgencia y protocolo. Bicarbonato/cetonas urinarias son alternativas; potasio es seguridad. Gráfico aeróbico: nueve puntos y nueve filas con mismos IDs/unidad. Volver al día 14 excluye muestra fechada en día 11 pero recibida en día 21. Sin errores/warnings de consola observados. Capturas en screenshots/. No certificación WCAG ni revisión exhaustiva de tecnologías de asistencia.

La aprobación automática rechazó guardar el acceso real descifrado en archivo temporal. No se creó. Se usó un portal desechable con código de prueba propio DPAPI, sin copiar accesos reales/históricos; después se detuvo. La escritura de informes con apply_patch agotó su plazo; se utiliza escritura nativa para la misma entrega autorizada.

## Protecciones reales

storage-mission-v011-final.json verifica cuatro archivos DPAPI, ACL, auditoría, backup, restauración nueva y HMAC externo; también anclaje previo y hash reservado. SQLite, WAL y backups siguen sin cifrar. SQLCipher no está instalado; su adaptador opcional no está conectado a Store.

Procesos de la misma cuenta Windows no están aislados; esa cuenta puede descifrar DPAPI. HMAC detecta manipulación limitada si clave/anclaje se conservan; controlar código, almacenamiento y clave permite reconstruir firmas. No es un registro inalterable. Ollama sigue en loopback sin autenticación propia. Credenciales históricas no se revocaron ni copiaron a informes. Norton, cuarentena y políticas globales Windows no se modificaron.

Pendientes: cifrado reconocido con migración/recuperación verificadas; aislamiento aprobado; revisión independiente de seguridad/accesibilidad; evaluación separada de explicaciones sustentadas conservando abstención; retención de snapshots. Integración local de investigación, sin validación clínica, operativa o espacial.