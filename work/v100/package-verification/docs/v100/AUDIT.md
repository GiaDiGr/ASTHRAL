# Auditoría final de integración · 2026-10-27

Se revisaron los documentos A/B, README, DEMO, RESULTS y contratos de v0.11, código/pruebas, RAG, recursos y seguridad. Se usaron auditorías biomédicas previas como antecedentes sin repetir íntegramente su revisión documental. Registro exacto de cambios: changes.json. Registry verificó el manifiesto científico original; no se cambiaron umbrales, catálogo ni conocimiento clínico (hash b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e).

Punto recuperable: before-v100.zip SHA256 f60b913922a84464591e7b337ff0c93181bde1796b45f2372f10d3c608ecbf6d y engine/data/backups/v011-before-v100. Los 76 replays antiguos coinciden usando work/v100/v011-runtime. Bases, documentos originales, configuración de Ollama, Norton y cuarentena conservados.

## Correcciones

| Problema | Cambio y verificación |
|---|---|
| Prosa con números/normalidad no respaldados; confusión baseline/previo | Hechos Pydantic con originales, contexto, unidad, procedencia/hashes y gramática verificable. Generación real acotada; criterios clínicos siguen deterministas. |
| Artículo español «La» rechazado | Artículos/variable permitidos sin relajar unidad, números o rol; regresiones positivas y negativas. |
| Recuperación poco pertinente | BM25 bilingüe/encabezados/diversidad después de verificar hashes/offsets/autoridad; resultados y fallos completos. |
| IDs de astronauta limitados a v07 | Reconocer misión integrada; negar otro sujeto explícito. |
| Banco R1: «otro astronauta»/riesgo vital devolvía hechos propios irrelevantes | R2 rechaza contexto genérico y riesgo no implementado; deriva interpretación diagnóstica al motor. No hubo fuga ni cálculo de riesgo, pero sí fallo de pertinencia. Banco usado, no reejecutado; regresiones posteriores no son evaluación ciega. |
| Coste de snapshots descartados tras parsearlos | Filtrado SQL de tipos, exclusión de replay_records anidados ya descartados y extracción de índice JSON sin snapshot completo. Sin borrar historia. |
| Alerta oculta al entrar al Asistente | Banner persistente de prioridad existente fuera de tarjetas; DKA verificado en navegador, sin nuevo algoritmo clínico. |
| Voz inexistente | Vosk y SAPI reales, revisión manual, WAV acotado, tickets sólo de texto aprobado. Captura física aún pendiente. |

## Cobertura integrada

«Probado» se refiere a software sintético, no a validez clínica/espacial.

| Ruta/componente | Cobertura y restricciones |
|---|---|
| Diabetes | Ruta/confirmación preexistentes conservadas; revisión clínica independiente pendiente. |
| DKA | AND/OR, alternativas no bloqueantes, seguridad de potasio, urgencia y reevaluación; sin tratamiento/diagnóstico firmado. |
| Hipotensión ortostática y POTS | Condiciones/ventanas/contexto y NOT_APPLICABLE conservados; no extrapolar a microgravedad. |
| AKI | Criterios y pruebas previas conservados; validez externa pendiente. |
| Anafilaxia | Estados, urgencia/protocolo separados; recursos/autorización/ejecución bloqueados. |
| Hipoglucemia | Criterios/faltantes y fuentes fijadas; extracto primario parcial, no validación. |
| Diferencial/pruebas | Prioridades/razones deterministas; no probabilidades ni órdenes autorizadas. |
| Baselines/tendencias/vigilancia | Dos sujetos/fases de misión; 26 ciclos, 50 evaluaciones, 76 replays. Datos inválidos/ausentes no normales; señales descriptivas no enfermedad. |
| 44 condiciones / 12 algoritmos investigados | Catálogo estructural y restricciones anteriores conservados; NO equivale a 44 rutas ejecutables. No catálogo nuevo. |
| Episodios/seguimiento | Historial/pendientes/reevaluación; sin cierre por dato ausente ni recuperación automática. Plan sintético no acredita revisión sanitaria. |
| RAG/LLM/voz | Lectura de resultados autorizados y explicación limitada; sin autoridad clínica. |

## Seguridad y límites

Reader/ámbito en servidor; BFF con cookie HttpOnly/SameSite=Strict, Origin exacto, cuotas y sesiones acotadas. No credenciales en navegador/prompts/audio. Sólo audio autenticado admite cuerpo grande; restantes POST conservan 16 KiB. Transcript no escribe mediciones ni ejecuta tratamientos. TTS sólo por ticket aleatorio ligado a sesión/objetivo, TTL 300 s, máximo 32; nunca texto libre del cliente. Audio PCM16 mono 16k: 0.2–40 s, límites de bytes/formatos; SAPI por JSON stdin, no comandos derivados del texto, sin SSML y entorno mínimo.

Tracks/playback se detienen en cancelación/cambio de contexto/modo/idioma/logout/pagehide/ocultación. Node prueba carreras simuladas, NO hardware. Cancelar UI no mata necesariamente un cómputo de servidor ya iniciado; finaliza acotado y se descarta respuesta tardía. Memoria Python no garantiza borrado forense.

SQLite/WAL/backups **sin cifrado**. DPAPI/ACL no aíslan procesos de la misma cuenta. HMAC externo detecta cambios del prefijo si clave/anclaje permanecen confiables; no resiste control de almacenamiento+código+clave. Nuevo anclaje R2 fuera de DB verificado; clave histórica conservada, credenciales históricas no revocadas globalmente. Ollama loopback no es aislamiento contra otros procesos locales. Hace falta cifrado/gestión de claves/cuenta aislada antes de datos reales. No cambios globales de firewall/cuentas/antivirus. Guardia Python de red no es firewall ni prueba de ausencia de tráfico de todo Windows.

## Rendimiento y procedencia

Prefijos originales pareados días 0/14/21/47, tres repeticiones secuenciales de cómputo con SQLite en memoria, carga de prefijo fuera del tiempo. Día 47 mediana 2.9102→0.4991 s; resultados clínicos/descriptivos/eventos iguales. DB final 37,883,904 bytes frente a 37,879,808 anteriores; no se eliminó historia. Misión R2 total 23.011 s: comparación con total antiguo NO controlada (caché/carga/fechas diferentes). Sin potencia instrumentada/hardware espacial.

R1 congelado antes del banco; 12 respuestas/raw/tiempos retenidos y USED. R2 corrige problemas después del banco y no dispone de nueva evaluación ciega. Hash implementación R2 f01f897bfd3e07328d25817ae6a9062d47cc9e12b66783ad6340286df70e09bf. El hash legacy usa .py; el manifiesto completo incluye además JSON/PS1/web/config.

## Dictamen

Integrable como prototipo local con contratos/regresiones comprobados. No cerrar todos los criterios v1.0: falta sesión física micrófono/altavoz EN/ES, inteligibilidad/pertinencia humana, nuevo banco ciego para R2, aislamiento y revisión clínica independiente. No apto para pacientes ni vuelo; ejecución terapéutica bloqueada.