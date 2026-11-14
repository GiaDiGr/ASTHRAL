# B. Local AI / Knowledge Engine v0.8.0

## Entrega

Se conserva Ollama en loopback y `vigile-qwen3-4b:latest`. No se modificaron Norton, su cuarentena ni la configuración del runtime. El motor determinista mantiene autoridad exclusiva; el asistente solo recibe credenciales reader. No hay herramientas de escritura ni ejecución terapéutica en el modelo.

### Módulos

- `knowledge_v08.py`: índice documental local, fragmentos literales y verificación de procedencia.
- `longitudinal_assistant.py`: consulta de ciclo/predecesor, bloques explicativos con referencias y fallback.
- `ai_evaluation.py`: banco fijo independiente de las respuestas del modelo, métricas separadas.
- `offline_library.py`, `local_assistant.py`, `portal.py`: integración compatible, lectura de ciclos y selector de contexto.
- `web/index.html`, `web/app.js`: ajustes mínimos; contexto clínico o último ciclo, fuentes separadas y JSON plegado.
- `tests/test_v08_ai.py`: recuperación, ataques documentales, rechazo, permisos, modos y API.

## Corpus y procedencia

El índice `engine/local_ai/library-v080.json` contiene 560 fragmentos exactos procedentes de seis archivos:

| Documento | Autoridad declarada |
|---|---|
| `docs/clinical/deep-research-report-2026-10-16.md` | Síntesis de investigación clínica |
| `01_INFORMES/REPORTE_CONSOLIDADO_COMPLETO.md` | Síntesis de investigación espacial |
| `docs/v07/README.md` | Documentación de implementación, no guía clínica |
| `docs/v07/CONTRACTS.md` | Contrato de implementación |
| `engine/vigile/clinical_knowledge/v07-extension.json` | Criterio implementado, no texto del artículo original |
| `docs/v08/sources/ADA2026-short-excerpt.txt` | Fragmento primario breve, tabla 6.4; no artículo completo |

El fragmento primario es de 23 palabras. Su procedencia se verificó el 21-10-2026 en la [publicación ADA 2026](https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/6-Glycemic-Goals-Hypoglycemia-and-Hyperglycemic). El índice no finge tener el texto íntegro de artículos que solo están referenciados en las síntesis. Véase `source-inventory.json` para versiones, hashes y autoridad.

Cada fragmento tiene ID estable, documento, SHA256, offsets de caracteres y línea. En cada búsqueda se verifican tanto el manifiesto como los bytes reales de la fuente y el texto literal. La búsqueda es léxica ponderada con equivalencias español/inglés y máximo dos fragmentos por fuente; no usa embeddings remotos ni descarga documentos al consultar. Se mantuvo el índice anterior intacto.

## Separación de autoridad

Los bloques `ENGINE` describen indicadores, baseline, tendencia, radiación, alertas, calidad, cambios entre ciclos y estados clínicos ya calculados. Sus referencias incluyen ciclo, fecha, hash y las entidades relacionadas. Los `DOCUMENT` aparecen por separado, con autoridad y procedencia. El LLM recibe solo bloques ENGINE para elaborar explicaciones del sujeto; los documentos se entregan como extractos, sin permitir que una guía o documento contradictorio cambie un estado clínico.

Las preguntas sobre faltantes/calidad usan respuesta determinista. Se conservan las categorías clínicas `missing_required`, `optional_not_measured`, `invalid_required` y `required_for_protocol_safety` provenientes del motor. Los indicadores no medidos de vigilancia son descriptivos y no se transforman en requisitos diagnósticos.

La generación se restringe a citas existentes y números presentes; se realiza además una comprobación de soporte con el mismo modelo. Esta comprobación NO es un evaluador clínico independiente. Los rechazos de formato, soporte o interpretación no autorizada conservan los resultados extractivos. La ausencia de generación no implica ausencia de enfermedad.

## Banco independiente y resultados

Las 16 preguntas fijas y expectativas se escribieron sin generarlas con el modelo evaluado. Incluyen baseline, cambios, alertas, hipoglucemia, radiación, microgravedad, sueño, faltantes, preguntas sin evidencia, diagnóstico no respaldado, tratamiento e inyección; hay paráfrasis y español/inglés. Los fixtures adversos adicionales cubren documento contradictorio, inyección documental y fuente/manifiesto manipulado. Los tests unitarios usan dobles controlados. Además, `evaluate_adversarial.py` ejecutó tres fixtures con Ollama real en FULL: contradicción documental, inyección documental y biblioteca ausente; 3/3 checks aprobados, registrados en `bank-adversarial-real.json`. Para inyectar el fallo se sustituye deliberadamente la capa de biblioteca; no se modifica el corpus activo. Se comprueba que solo ENGINE alcanza el generador, que no cita el documento adverso, que se aparta la inyección y que la fuente ausente se declara. Esto no mide resistencia general ni errores semánticos no detectados.

Métricas separadas:

- RAG: recuperación del documento esperado entre los cinco primeros en 6 preguntas; referencias verificadas contra bytes; no se estimó precisión semántica general ni recall de todo el corpus. La interfaz recupera hasta tres fragmentos, por lo que top-5 del banco no equivale a cobertura de pantalla.
- LLM: invocaciones solicitadas, generación aceptada, fallback, rechazo de acciones y estados sin información. `inference_attempted` significa llamada a la capa conversacional; puede detenerse antes de llamar al modelo por falta de contexto relevante. No equivale siempre a una inferencia de Ollama.
- Los errores semánticos no detectados se registran como `NOT_MEASURED_REQUIRES_INDEPENDENT_REVIEW`. No se reporta cero alucinaciones ni fiabilidad clínica. Un fallback tampoco demuestra que se haya detectado una alucinación: puede deberse a formato, truncamiento o comprobación conservadora.

Los JSON `bank-release-*.json` conservan pregunta, expectativas, respuesta completa, fuentes, checks y latencias por caso. `RESULTS.md` resume las cifras finales. Los archivos `bank-full.json` y `bank-low-critical.json` son corridas preliminares conservadas, anteriores a la corrección de falso rechazo.

### Defectos descubiertos durante la evaluación

1. La consulta inglesa de radiación no recuperaba el documento esperado. Se añadieron equivalencias coverage/cobertura y limitations/limitaciones y diversidad por documento, sin cambiar la expectativa.
2. Una consulta informativa sobre dosis radiológica registrada se rechazaba por el patrón genérico de dosis terapéutica. Se distingue la lectura de una dosis registrada y se mantiene el rechazo de prescripción incluso si la consulta menciona radiación. Se añadieron dos regresiones y el banco exige que preguntas legítimas no sean rechazadas.
3. Hubo dos interrupciones `RemoteProtocolError` en comprobaciones preliminares con el backend local. Las repeticiones completaron las verificaciones; una prueba de 60 GET persistentes y 60 con conexión cerrada no reprodujo el error. Causa no demostrada; no se atribuye al antivirus ni se declara resuelta por un cambio inexistente.

## Modos y funcionamiento offline

FULL permite generación verificada; LOW_POWER conserva la política existente de contexto reducido; CRITICAL evita incluso comprobar disponibilidad del modelo y mantiene motor/extractos. Los bancos reales se ejecutan con bloqueo de conexiones externas en su proceso y solo permiten loopback. Esto verifica el cliente de evaluación; no prueba ausencia de tráfico externo de todo Windows ni convierte Ollama en un proceso aislado por el sistema operativo.

Las consultas reader no alteraron registros persistidos y se denegó escritura/acceso fuera de ámbito. Se preservaron credenciales existentes sin incorporarlas al corpus o prompts. La UI distingue vigilancia sin evaluación clínica y mantiene detalles técnicos plegados. La captura `assistant.png` y los ejemplos permiten revisar la presentación.

## Pendientes

1. Auditoría especializada independiente de relevancia, contradicciones, respuestas y omisiones, con un banco más amplio reservado para evaluación; el banco actual es de desarrollo y se ha usado para correcciones.
2. Evaluar ataques documentales más diversos con Ollama real y proveedores documentales manipulados en un entorno aislado. Las expresiones regulares no garantizan inmunidad a prompt injection.
3. Mejorar selección/contexto de la generación: el modo reducido puede omitir un bloque relevante aunque el resultado determinista siga visible; revisar respuestas insuficientes y falsos negativos del verificador.
4. Investigar desconexiones HTTP bajo carga y añadir recuperación explícita solo tras reproducir su causa; nunca reintentar ciegamente operaciones de escritura.
5. Completar corpus primario bajo condiciones de acceso/licencia adecuadas y revisión editorial clínica. Las síntesis y contratos no sustituyen guías originales.
6. Aislar procesos y almacenamiento, cifrar SQLite/gestionar claves y proteger auditoría externamente. No se hizo auditoría profunda de RAM, VRAM ni energía.

Listo para integración de investigación con contratos de lectura; no certificado para diagnóstico, tratamiento o vigilancia autónoma de astronautas.
