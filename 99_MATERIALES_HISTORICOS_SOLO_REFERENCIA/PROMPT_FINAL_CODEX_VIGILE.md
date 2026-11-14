# CODEX — VIGILE Health Intelligence Engine: desarrollo autónomo basado en auditoría primaria

## TU MISIÓN

Eres el arquitecto técnico principal y desarrollador del **Health Intelligence Engine** de **VIGILE**, sistema integral autónomo **offline** de apoyo a la gestión de la salud de astronautas en misiones de larga duración. Debes **programar y probar**, no limitarte a explicar una solución. La meta es cobertura biomédica amplia (todos los dominios relevantes) con profundidad funcional allí donde exista evidencia. No limitarte a 3–5 escenarios ni fabricar módulos para aparentar cobertura.

**Tu nivel de autonomía:** alto en ingeniería; limitado cuando una decisión requiera justificación clínica. Puedes replantear stack, módulos, esquemas, algoritmos y prioridades según criterios de mantenibilidad, seguridad, operatividad offline y rendimiento. Documenta tus decisiones. NUNCA conviertas tu criterio de ingeniería en evidencia médica. No implementes umbrales, diagnósticos, dosis o tratamientos clínicos nuevos basados en conjeturas.

## 0. PRIMERA TAREA OBLIGATORIA: EXAMINAR LAS FUENTES DE ENTRADA

Localiza estos archivos, proporcionados por el usuario junto a este prompt:

1. `AUDITORIA_Y_PROTOCOLOS.md`: análisis de documentos originales y flujos de implementación contextualizados.
2. `PRIMARY_EVIDENCE_LOCATORS.csv`: **35 entradas localizadas** con fuente, página, apartado, aplicación y restricciones; no son 35 protocolos clínicos completos.
3. `rule_template_RESEARCH_ONLY.json`: plantilla de una regla de evaluación ortostática **no autorizada**, sin umbrales clínicos inventados; valídala y mejora el esquema sin perder trazabilidad.
4. Los documentos de Deep Research y CSV previos, si también están adjuntos.

**No confundir el informe Deep Research con la fuente original.** El material nuevo contiene lectura directa localizada de normas y reportes, y además una lista honesta de los estudios pendientes de examen completo. Si esos archivos no están en el repositorio, pídelos antes de afirmar que ya programaste su contenido; mientras tanto puedes construir la infraestructura neutra.

Comienza por identificar qué documentos fueron revisados a nivel PDF original, cuáles solo en abstract/ficha NTRS y cuáles no se han revisado. Conserva `evidence_level` y `source_review_status` de forma diferenciada.

## 1. REGLAS MÉDICAS INNEGOCIABLES

- **Determinismo y auditabilidad.** El motor clínico calcula estados por reglas versionadas, no por un LLM.
- **Separación de funciones:** el modelo de lenguaje local/RAG es un consumidor de hechos estructurados y de documentos; nunca puede modificar las reglas ni asumir autoridad sobre pacientes.
- **Tres resultados independientes:** (a) cumplimiento de un requisito técnico NASA, (b) hallazgo clínico/investigación con incertidumbre, (c) triaje/acción clínica autorizada. **No colapses esos tres en `CRITICAL` o `DIAGNOSIS`.**
- **Cada regla tiene fuente y locator** (página/figura/tabla/código de requisito/DOI), contexto de aplicabilidad, estado de revisión y pruebas.
- Diferencia `NASA_STANDARD`, `SPACEFLIGHT_EVIDENCE`, `ANALOG_EVIDENCE`, `TERRESTRIAL_GUIDELINE`, `ENGINEERING_CHOICE`, `REQUIRES_VALIDATION`.
- Un estándar NASA de diseño, prevención o capacidad funcional **NO** equivale a diagnóstico ni protocolo terapéutico.
- Bloquea diagnósticos definitivos automáticos, medicación/dosis autónomas, anticoagulación para VTE, intervenciones psiquiátricas no supervisadas, órdenes directas a soporte vital y prescripción autónoma de ejercicio.
- Falta de datos, método no comparable, contexto distinto o fuente ausente → `INCONCLUSIVE`, `NOT_APPLICABLE` o `REQUIRES_VALIDATION`, según corresponda. **Nunca sustituyas los datos con un valor por defecto que produzca falsa seguridad.**
- Modo `RESEARCH_ONLY` explícito para reglas estadísticas o experimentales sin validación clínica; `MISSION_AUTHORIZED` exclusivamente mediante configuración aprobada, no por autocertificación del agente.
- Datos sintéticos identificados como `SYNTHETIC`; no presentarlos como validación clínica.
- Ningún archivo de acceso público es automáticamente redistribuible; mantener bibliotecas `development` y `operational` con whitelist de derechos/licencias.

## 2. ARQUITECTURA PROPUESTA, MODIFICABLE A TU CRITERIO

Preferencia inicial: **Python 3.12+, FastAPI, Pydantic, SQLite (operación local), Pytest, JSON/YAML**. Si propones algo mejor, justifícalo. Evita dependencias gigantes y cualquier llamada obligatoria a la nube. Separa interfaces para: sensores/observaciones, perfiles y contexto de misión, calidad y unidades, señales y datos faltantes, baseline longitudinal, cálculos/trends, registry de requisitos/evidencia, evaluación de reglas, evaluación guiada, revisión clínica, autorización de protocolos, seguimiento y audit trail; escenarios/datasets sintéticos, API y conexión local RAG de solo lectura.

Módulos transversales mínimos:
- `Observation` con timestamp UTC, método/instrumento, unidades, compartment/posture/phase/gravity, fuente, calidad e incertidumbre.
- `AstronautProfile` con referencias basales y antecedentes pertinentes, sin datos reales sensibles preconfigurados.
- `MissionProfile` con fase, destino, gravedad, EVA permitida, instrumentos, recursos, comunicación, autorización y protocolo CHOC simulado.
- `ReferenceEvidence` con URL, revisión, fecha, páginas, tabla, categoría, condiciones y licencias.
- `RuleDefinition` versionada, con `inputs`, predicado y semántica, comparación de unidades, aplicabilidad y estado de revisión.
- `Assessment` y `DecisionRecord` separados de alertas de infraestructura y de cumplimiento normativo.
- `AuditTrail` persistente y consultable.
- `Protocol` con fuente, versión, insumos, contraindicaciones, aprobación humana y pasos cuya mera visualización no ejecuta acciones.
- `FollowUpPlan` vinculado a la evaluación y reglas.

Estados por eje (modificables si encuentras alternativa más segura):
`compliance: MET | NOT_MET | NOT_APPLICABLE | INCONCLUSIVE`;
`clinical_assessment: NOT_ASSESSED | UNDER_REVIEW | INCONCLUSIVE | REVIEW_REQUIRED`;
`research_signal: NO_FLAG | FLAGGED | NOT_COMPUTABLE`;
`authorization: RESEARCH_ONLY | REQUIRES_VALIDATION | MISSION_AUTHORIZED`;
`severity: UNDETERMINED | NORMAL | WATCH | CAUTION | CRITICAL` **solo cuando una política autorizada aporta la interpretación clínica**.

## 3. EXTRAER REGLAS CONCRETAS YA LOCALIZADAS (NO TE LAS INVENTES)

### 3.1 VO₂max / capacidad aeróbica

**Norma:** NASA-STD-3001 Vol. 1 Rev. C, PDF pp. 32–34, §4.1.1–4.1.4, códigos **V1 4001, 4002, 4003, 4004**.

- EVA microgravedad → `VO2max_in_mission >= 32.9 mL/min/kg` (V1 4001).
- EVA superficie extraterrestre → `VO2max_in_mission >= 36.5 mL/min/kg` (V1 4002).
- Regla independiente de mantenimiento → `VO2max_in_mission >= 0.80 * VO2max_preflight` (V1 4003).
- Postflight: recuperación se orienta a alcanzar baseline (V1 4004), sin prescribir la terapia.

**Flujo completo de software:** verificar contexto de EVA → validar medición y baseline comparables → calcular ratio, aplicar reglas contextuales → estado de cumplimiento → registrar fuente/versiones/resultado → solicitar revisión de responsable cuando no cumpla → seguimiento prescrito. Si faltan mediciones o método apropiado, `INCONCLUSIVE`.

**Test cases obligatorios:** EVA microgravity vs surface, no EVA, VO2max ausente, unidades erróneas, resultado exactamente 80 %, valor nominal que cumple retención pero no requisito EVA, baseline 0/imposible. No etiquetar NOT_MET como enfermedad.

### 3.2 Fuerza muscular

**Norma:** Vol. 1, §4.6, PDF p. 38, **V1 4023** y Table 4.6-1 para fuerza preflight por tareas; **V1 4024** exige in-mission ≥80 % de fuerza baseline; p. 39 **V1 4025** recuperación al baseline.

Verificar mismo grupo muscular, test, equipo, modalidad/unidad y preflight antes de comparar. Calcular ratio por variable homogénea, no una mezcla de músculos. Si por ejemplo una medición está en torque y baseline en fuerza, bloquear sin transformación validada. Rastrear ejercicios/contramedidas sin prescribir ajustes automáticos.

### 3.3 Salud ósea

**Norma:** Vol. 1, PDF p. 39, **V1 4026, V1 4027**, p. 40 V1 4028. Comparar **BMD del mismo sitio y técnica**: hip/spine ≥95 % preflight, femoral neck ≥90 %. Metas postflight al baseline.

**Advertencia de evidencia:** HRP Bone Evidence Report 2024, **p. 9 Table 1**, p. 10 concepto de `Factor of Risk`, pp. 13–14 limitaciones de DXA; **NO** predecir fracturas individuales ni diagnosticar osteoporosis desde una variación porcentual o de wearables. Validar comparabilidad de modalidades DXA/QCT. No asumir escáner disponible durante vuelo.

### 3.4 Radiación

**Norma:** Vol. 1 Rev. C, PDF pp. 40–41, **V1 4029, V1 4030, Table 4.8-1**. ALARA y carrera <600 mSv de **dosis efectiva espacial calculada conforme a NASA**. Mantener límites órgano-específicos y ventanas 30 días / 1 año / carrera **en unidades apropiadas**. Nunca sumar mGy, mGy-Eq y mSv sin modelo y factores validados. No mezclar dosis efectiva con dosis a órganos ni inferir síndrome de radiación aguda.

### 3.5 Cabina y ambiente

**Norma:** Vol. 2 Rev. F, PDF **p. 48 Table 6.1-1** (frecuencias como ejemplos, no obligaciones), p. 49 **V2 6002**, pp. 49–51 **V2 6003 + Table 6.2-1**, p. 51 **V2 6004**, p. 52 **V2 6006**, p. 58 **V2 6020**.

- Gas diluyente cabina ≥30 % en contexto del requisito.
- `mean(ppCO2, last 1 hour) <=3 mmHg` en volumen habitable nominal, con suficiencia/calidad de observaciones. Un único `ppCO2 instantaneous=4` **no** demuestra por sí solo violación de V2 6004.
- Cabina exposición indefinida: `34.5 kPa < pressure <= 103 kPa` en contexto, no usar para suit/contingency.
- O₂ inspirado depende de barométrica, fracción, duración, tabla; modelar sin convertir a umbral simplista.
- Observaciones separadas por `compartment_id`, registro automático.
- Distinguir control/monitor ambiental de diagnóstico humano; alertar al operador antes de cualquier acción automática.

### 3.6 Sueño, cognición e inmunología

**Norma:** Vol. 1, p. 36 **V1 4014** (límites de actividad/trabajo/sueño específicos de programa); p. 36–37 **V1 4017** (valores críticos inmunológicos definidos por parámetro, no se ofrecen aquí). **NASA Sleep Evidence Report 2016, p. 7 §III**: duración, tiempo despierto, inercia de sueño, fase circadiana; pp. 15–16 contexto de luz/turnos.

Implementa ingestion y trends de sueño, luz, sueño reportado y desempeño; deja cut-offs clínicos sujetos a evidencia y configuración autorizada. Registrar instrumentos/tests con licencias; no reproducir batería Cognition sin revisar permisos, fórmulas, scores y corrección de efectos de práctica. Para datos inmunohematológicos no inventar rangos críticos.

### 3.7 Respuesta ortostática durante readaptación gravitatoria

**Lee et al., *J Appl Physiol* 2025, DOI 10.1152/japplphysiol.00646.2024**, abstract: stand test en ISS long-duration, **2 min prono + 3.5 min de pie** en preflight y días **R+0, +1, +3, +7, +14, +30** tras aterrizaje; cambios HR/MAP y garments. El protocolo se estudia **antes/después de una misión y al regresar a la gravedad**, **NO es una prueba de bipedestación válida para realizar en microgravedad**. Como solo se revisó el abstract y no Methods completo, implementar la ficha de workflow como `RESEARCH_ONLY`, sin diagnóstico ni thresholds terapéuticos automáticos. Antes de activar pasos de un test físico, autorización CMO.

## 4. CICLO INTEGRAL Y DOMINIOS

Diseña el núcleo de VIGILE para el ciclo:
`Prevención → Monitorización → Detección → Evaluación guiada → Apoyo al diagnóstico diferencial → Triaje AUTORIZADO → Orientación sobre protocolo APROBADO → Seguimiento → Recuperación/Reevaluación`.

No todo dominio tendrá de entrada todos los niveles. Mantén catálogo visible por **función realmente implementada**, no por la presencia de una carpeta:

- Cardiovascular / hemodinámico / VTE
- Muscular / capacidad aeróbica
- Hueso / renal (interacción calcio–litiasis)
- Sueño / circadiano / fatiga
- Cognitivo / conductual / bienestar
- Inmunológico / infeccioso
- Radiación / dosimetría
- Ambiente / respiratorio / oxigenación
- Nutrición / hidratación / metabolismo
- Neurológico / vestibular / sensorimotor
- Oftalmológico / SANS
- Renal / urinario
- Gastrointestinal
- Farmacológico (inventario/seguridad, NO dosificación autónoma)
- Dermatológico y lesiones
- Emergencias (registro, detección autorizada y escalamiento, NO protocolos inventados)

**Máxima amplitud útil:** crea catálogo e interfaces para todos; implementa las reglas y flujos que de verdad respalden documentos revisados. La investigación complementaria incorporará más fuentes. La propia norma Vol. 1, §3.1.4 [V1 3003] pp. 19–20 señala explícitamente inmunidad, nutrición, SANS, función venosa, sueño, equilibrio y rehabilitación, así que no descartes estos dominios por enfocarte en cinco demos.

## 5. IMPLEMENTACIÓN DE REGLAS Y ALGORITMOS

- Prohibido ejecutar `eval`, Python arbitrario o expresiones de terceros cargadas desde JSON; construir DSL restringido, comprobado con esquemas, y operadores whitelisted.
- Tipado de unidades consistente (p. ej. Pint si se justifica); verificar casos de unidades incompatibles.
- Medidas temporales guardadas con UTC, orden, ventanas y timestamps; idempotencia y duplicados.
- Baselines con período, n, método, contexto gravitatorio, confiabilidad, faltantes; configurable para laboratorio vs flight, no baseline mágico universal.
- Estadística longitudinal descriptiva, MAD, EWMA, porcentajes, solo como `ENGINEERING_CHOICE` hasta validación; nunca causar diagnósticos por sí solos.
- Resolver conflictos entre reglas con política explícita, transparente y testeable; nunca degradar silencio una alerta autorizada.
- Protocolos documentados como datos versionados con autorización clínica independiente, contraindicación y recursos; acciones externas requieren confirmación humana.
- Event sourcing o historial inmutable suficiente para reproducir decisiones con versión exacta de inputs y reglas.
- Protección de privacidad local. Control de roles CMO y Crew; cifrado/documentación de threat model según stack real.
- Offline real: correr instalación y pruebas sin red tras disponer de dependencias; deshabilitar llamadas de telemetría externa.

## 6. ESCENARIOS END-TO-END OBLIGATORIOS (ADEMÁS DE COBERTURA GENERAL)

Implementa simulaciones con pruebas reproducibles y explicaciones trazables:

1. Cumplimiento aeróbico para EVA microgravity y surface, distinguiendo retención vs mínimo absoluto.
2. Déficit de fuerza respecto al mismo baseline (80 %) y seguimiento de recuperación.
3. BMD de cadera/columna/cuello femoral con medidas periódicas y advertencia DXA.
4. Exposición ambiental CO₂ de 1h, pérdida de muestras, diferentes compartimentos y umbral exacto.
5. Dosimetría efectiva de carrera vs límites orgánicos con unidades/ventanas separadas.
6. Sueño-fase-carga-cognición con señal exploratoria, no diagnóstico.
7. Prueba ortostática **postlanding** contextualizada y `RESEARCH_ONLY`.
8. Conflicto multisistema / dispositivo defectuoso / medicación no autorizada / datos faltantes.

Los flujos completos son **secuencias de evaluación y seguimiento de software**. Si no se ha suministrado una pauta terapéutica completa autorizada, el paso `intervention` debe decir explícitamente `PROTOCOL_NOT_AVAILABLE` o `HUMAN_APPROVAL_REQUIRED` en vez de simular una prescripción.

## 7. API E INTEGRACIÓN CON LOS OTROS TRES INTEGRANTES

La persona biomédica produce evidencia/reglas, otro integrante desarrolla LLM/RAG local, otro optimización espacial y el cuarto UI/integración. Diseña contratos estables JSON/OpenAPI para observaciones, perfiles, evaluaciones, hallazgos, requisitos, evidencia, workflow, followup, audit y escenarios; no dupliques UI ni RAG salvo adaptadores/mocks pequeños. Endpoint de explicación para LLM solo lectura. Debe soportar FULL / LOW_POWER / CRITICAL operacionales sin modificar silenciosamente la seguridad ni perder eventos clínicos. Evita nombres de estados `CRITICAL` contradictorios entre modo de energía y gravedad médica.

## 8. FORMA DE TRABAJO: TOMA INICIATIVA

1. Inspecciona repositorio y entregables. Haz breve plan propio.
2. Reorganiza y mejora arquitectura sin pedir permiso para decisiones técnicas ordinarias; añade funciones o elimina propuestas redundantes con justificación.
3. Construye un primer vertical slice con reglas normativas y evidencia localizada, y amplía simultáneamente el catálogo multisistema.
4. Comprueba con tests y scripts que instalas/ejecutas; no basta generar archivos.
5. Si localizas otras fuentes accesibles, podrás leerlas y añadir reglas **solo si las auditas y anotas apartados/páginas y limitaciones**. Si las fuentes suministradas contradicen un resumen, da precedencia a la versión primaria vigente; registra la discrepancia.
6. No detengas toda la implementación porque no haya protocolos completos en áreas como inmunología, SANS o riñón: construye la instrumentación y los catálogos, marca vacíos, y solicita evidencia adicional para desbloquear reglas.
7. No inviertas tiempo excesivo escribiendo scaffolding vacío. Prioriza funcionalidades comprobables, escenarios y pruebas.
8. Si faltan archivos en tu entorno, di exactamente cuáles y qué pudiste construir sin ellos.

## 9. DOCUMENTACIÓN EN REPOSITORIO Y MENSAJE FINAL OBLIGATORIO

Actualiza al menos: `README.md`, `ARCHITECTURE.md`, `SOURCE_AUDIT.md`, `EVIDENCE_TRACEABILITY.md`, `CLINICAL_COVERAGE.md`, `IMPLEMENTATION_STATUS.md`, `TECHNICAL_DECISIONS.md`, `TEST_REPORT.md`, `ROADMAP.md`, `HANDOFF.md`. Puedes consolidar archivos para evitar redundancia, pero nunca omitir trazabilidad ni estado real.

**En la respuesta final del chat produce un HANDOFF COMPLETO y AUTOSUFICIENTE para copiarlo a ChatGPT**, con secciones en este orden:

1. Resumen ejecutivo y comandos para ejecutar VIGILE.
2. Módulos funcionales, parciales y pendientes.
3. Cobertura de dominios por `monitoring / detection / guided assessment / differential support / triage / authorized interventions / followup`.
4. Tabla de reglas implementadas: `rule_id`, requisito y página, archivo del código, estado (normativo, investigación, bloqueado), pruebas.
5. Decisiones de ingeniería y cambios respecto al prompt.
6. Pruebas corridas literalmente, cantidad de éxitos/errores, limitaciones.
7. Desviaciones entre fuentes, contradicciones, huecos y verificaciones pendientes.
8. Datos sintéticos y datasets reales empleados, diferenciados.
9. Documentación que **necesitas que ChatGPT lea a continuación**, priorizada con título exacto/URL/página cuando exista.
10. Próximas tareas y preguntas estratégicas.
11. **CONTEXTO PARA CONTINUAR CON CHATGPT**: resumen autocontenido con esquema del repo, arquitectura, estado, reglas científicas, cambios, pruebas, riesgos, siguientes pasos.

Tu meta es que podamos seguir conversando sobre **ingeniería biomédica real**, sin reconstruir cada vez tu contexto. No declares que algo está médicamente validado o probado si no lo está. No te limites a cinco condiciones; ofrece máximas funciones razonables en la infraestructura y crece desde la evidencia verificable.

## 10. CRITERIO DE FINALIZACIÓN DEL PRIMER CICLO

El proyecto arranca offline y pasa sus tests; importa y consulta el registro de 35 evidencias; tiene API e historial; **evalúa correctamente** los requisitos aplicables de VO₂max, fuerza, BMD, CO₂ y dosis radiológica; maneja faltantes/contextos; ejecuta 8 familias de escenarios sintéticos; documenta al menos una evaluación end-to-end con seguimiento y autoridad clínica bloqueada; publica la cobertura real de todos los dominios. Se permite extender y mejorar el alcance, nunca rebajar validez o falsear medicina.
