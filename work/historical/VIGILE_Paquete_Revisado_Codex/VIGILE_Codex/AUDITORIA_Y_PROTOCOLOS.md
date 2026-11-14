# VIGILE — auditoría primaria y traducción a software

**Corte:** 13 octubre 2026. **Estado:** revisión inicial verificable de fuentes primarias; NO constituye una auditoría exhaustiva de todas las referencias del Deep Research ni validación clínica. Se examinó texto de las normas NASA-STD-3001 Vol. 1 Rev. C (87 páginas) y Vol. 2 Rev. F (389 páginas), del Evidence Report óseo 2024 (60 páginas), del Evidence Report sueño/circadiano 2016 (82 páginas), y el resumen original del estudio de Lee y cols. (2025). Otras fuentes se contrastaron por su ficha institucional, pero NO se atribuyen páginas no examinadas. El archivo `PRIMARY_EVIDENCE_LOCATORS.csv` contiene **35 entradas de localización primaria** verificadas a nivel de apartado, requisito o tabla, no 35 protocolos completos.

## 1. Fuentes originales directamente consultadas

- **STD1:** NASA-STD-3001, Volume 1, Rev. C (2023), [PDF oficial](https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf). Las páginas citadas corresponden al número **impreso** de la norma, coincidente con el número de página PDF en la edición consultada.
- **STD2:** NASA-STD-3001, Volume 2, Rev. F (14 julio 2026), [PDF oficial](https://standards.nasa.gov/system/files/tmp/NASA-STD-3001%20Vol%202%20Rev%20F.pdf). Se cita número impreso/PDF.
- **BONE:** NASA HRP, *Risk of Bone Fracture due to Spaceflight-induced Changes to Bone* (2024), [PDF original](https://ntrs.nasa.gov/api/citations/20240005190/downloads/2024%20FINAL%20HRP-F07-ERft%20R2%20Fracture.pdf). El número de página citado es el impreso en el informe; para estos pasajes coincide con la numeración PDF.
- **SLEEP:** NASA HRP, *Risk of Performance Decrements ... Sleep Loss, Circadian Desynchronization and Work Overload* (2016), [PDF original](https://ntrs.nasa.gov/api/citations/20160003864/downloads/20160003864.pdf). Página según número impreso de informe, que puede diferir de la posición física en PDF.
- **OI:** Lee et al., *Cardiovascular responses to standing with and without lower body compression garments after long-duration spaceflight*, *J Appl Physiol* 2025, [registro PubMed y resumen original](https://pubmed.ncbi.nlm.nih.gov/40338620/) (DOI 10.1152/japplphysiol.00646.2024). **Se revisó el resumen, no todo el texto**.

## 2. Hallazgos primarios específicos para traducir a código

### 2.1 Transversales: modelo de datos y gobernanza

**STD1, pp. 21–22, §3.1.5 [V1 3004].** El estándar incluye entre las capacidades de asistencia a bordo: datos clínicos, historia y examen, signos vitales y tendencias, imágenes/ECG, procedimientos, medicamentos, recursos y apoyo médico autónomo. **Traducción:** separar `observations`, `encounters`, `assessments`, `diagnostics`, `procedures`, `inventory`, `protocol_registry` y `clinical_decision_record`. El estándar requiere las capacidades a nivel del programa; **no ofrece un algoritmo universal de diagnóstico ni prescribe medicamentos**.

**STD1, pp. 53–54, §6.5.1/6.5.2 [V1 6008–6009].** CHOC y documento técnico médico específico de la misión (MORD histórico). **Traducción:** cada regla clínica tiene `mission_profile_id`, modalidad de gravedad, versión de fuente y estado de autorización. El prototipo no debe presentarse como CHOC real autorizado.

**STD1, p. 55, §7 [V1 7001–7003].** Historial recuperable para análisis de tendencias, transmisión adecuada y seguridad de registros. **Traducción:** persistencia SQLite transaccional, historial inmutable de evaluaciones/decisiones, versiones, control de acceso, cifrado según contexto, y trazabilidad de unidad, procedencia, calidad y tiempo de cada dato. El detalle de implementación (SQLite, técnica de cifrado) es una elección de ingeniería, no obligación literal de usar esa tecnología.

**STD2, p. 46, §5.2.1 [V2 5053].** Prevenir errores de operador, facilitar corrección y limitar daños. **Traducción:** bloqueo de acciones de riesgo, confirmación, explicación de contradicciones y reversión de acciones administrativas; nunca ejecutar dispositivos médicos/sistemas ambientales solo porque una regla se activó.

### 2.2 Capacidad aeróbica: un flujo casi listo para software

**STD1, pp. 32–34, §4.1 [V1 4001–4004].** Requisitos **diferentes** que se evalúan conjuntamente según misión:

1. EVA microgravedad: VO₂max ≥ **32,9 ml/min/kg** en misión (p. 32, V1 4001).
2. EVA superficie extraterrestre: VO₂max ≥ **36,5 ml/min/kg** (p. 33, V1 4002).
3. Independientemente del anterior, VO₂max en misión ≥ **80 %** de la capacidad pre-misión (p. 33, V1 4003).
4. Recuperación post-misión dirigida a alcanzar el valor pre-misión (p. 34, V1 4004).

**Flujo de evaluación VIGILE:**

`Identificar contexto mission/EVA → verificar presencia de VO2max y baseline emparejables (método, unidades, fecha, calidad) → calcular ratio current / baseline → comprobar V1 4003 → comprobar V1 4001 y/o V1 4002 solo si corresponden → producir REQUIREMENT_MET / REQUIREMENT_NOT_MET / NOT_APPLICABLE / INCONCLUSIVE → registrar evidence_id exacto → abrir seguimiento/preparación de evaluación por equipo médico si no cumple → repetir evaluación según agenda autorizada`.

**Importante:** `REQUIREMENT_NOT_MET` no equivale a `DIAGNOSIS` ni indica intervención física autónoma. No extrapolar VO₂max medido en ejercicio terrestre a un predictor preciso de EVA sin validar el método indirecto.

### 2.3 Fuerza muscular: monitorización por prueba funcional

**STD1, p. 38, §4.6.1/4.6.2, Table 4.6-1, [V1 4023–4024].** La tabla 4.6-1 recoge requisitos de fuerza preflight de deadlift y bench press dependientes de EVA/egress. V1 4024 establece conservar en misión **al menos 80 %** de la fuerza baseline. **STD1 p. 39, V1 4025** manda orientar recuperación postflight al baseline.

**Flujo:** `identificar test (músculo/junta/modalidad/equipo) → baseline del mismo test → verificar comparabilidad → fuerza_actual/baseline ≥0,8 → estado de cumplimiento → tendencia por grupo muscular → seguimiento de ejercicio/adherencia → remisión a plan prescrito por CMO`. Un 80 % global nunca debe calcularse mezclando fuerza de músculos o protocolos de prueba incompatibles.

### 2.4 Salud ósea: evaluación periódica, no sensor continuo

**STD1, p. 39, §4.7.1/4.7.2, [V1 4026–4027].** Baseline de BMD por DXA en cadera total y columna lumbar; durante misión, contramedidas para mantener **≥95 %** del valor preflight en cadera y columna, y **≥90 %** en cuello femoral. **STD1 p. 40 [V1 4028]** fija meta de recuperación al baseline.

**BONE, p. 9, Table 1:** contiene bandas de T-score adaptadas a cohortes NASA, provenientes de documentación histórica. **No importarlas como norma vigente sin reconciliar con Vol. 1 Rev. C.**

**BONE, pp. 13–14 y pp. 21–22:** DXA no muestra toda la pérdida y recuperación ósea; QCT y biomecánica/FEM añaden información. **BONE p. 10** define conceptualmente `Factor of Risk = applied load / bone strength`; sin cargas y resistencia estimadas y validadas no existe cálculo clínico útil de probabilidad de fractura.

**Flujo:** `fecha y región anatómica → imagen DXA/QCT con método y calidad → comparar mismo sitio/método con preflight → ratio y pérdida porcentual → requisito específico V1 4027 → contextualizar con biomarcadores y ejercicio si disponibles → seguimiento; no diagnosticar osteoporosis ni predecir fractura por la única variación DXA`. Si no hay DXA/QCT a bordo, no inventar estimaciones de BMD desde datos de pulsera.

### 2.5 Radiación: contabilidad dosimétrica rigurosa

**STD1, pp. 40–41, §4.8 [V1 4029–4030].** ALARA; dosis efectiva de carrera debida a radiación espacial **<600 mSv**, con definición dosimétrica NASA específica y considerando exposiciones anteriores y proyectadas. **STD1, p. 41, Table 4.8-1** lista límites temporales y orgánicos en **mGy-Eq o mGy** (no intercambiables con mSv).

**Flujo:** `recibir evento dosimétrico (fecha, ubicación, unidad, tipo de dosis, estimación/incertidumbre, instrumento) → validar conversiones y comparabilidad → acumular dosis efectiva solo si existe modelo/medida apropiada → contrastar con V1 4030 → llevar separadamente ventanas 30 días/año/carrera para órganos según tabla → registrar alertas de cumplimiento y escalar al responsable de radioprotección`. No diagnosticar síndrome agudo por extrapolación de valores de dosis crónica.

### 2.6 Ambiente de cabina: valores numéricos con contexto temporal

**STD2, p. 48, Table 6.1-1.** Ofrece **frecuencias de muestreo de ejemplo**, no todas exigencias obligatorias: constituyentes atmosféricos 5 s, presión 1 s, temperatura/humedad 1 minuto.

**STD2, p. 49 [V2 6002]:** al menos **30 %** de gas diluyente de cabina en el contexto especificado.

**STD2, pp. 49–51 [V2 6003] y Table 6.2-1:** presión parcial inspirada de O₂ con bandas de exposición y duración; **no confundir % de O₂ ambiental, ppO₂ seca y PIO₂ fisiológica**.

**STD2, p. 51 [V2 6004]:** el promedio **de una hora** de ppCO₂ de cabina debe ser **≤3 mmHg**. Fuera de condiciones nominales los límites son específicos del programa.

**STD2, p. 52 [V2 6006]:** presión total de exposición indefinida **34,5 kPa < P ≤103 kPa**, con condiciones en su texto.

**STD2, p. 58 [V2 6020]:** almacenar automáticamente por cada compartimento aislable presión, humedad, temperatura, ppO₂ y ppCO₂ durante operaciones con tripulación.

**Flujo CO₂:** `observation(room_id, timestamp, ppCO2, mmHg, quality) → validación temporal/sensor → calcular media móvil de 60 min con cobertura mínima definida y documentada → si cobertura insuficiente INCONCLUSIVE → si media ≤3 mmHg REQUIREMENT_MET → si >3 REQUIREMENT_NOT_MET + NOTIFY_ENVIRONMENT_OPERATOR; no inferir una emergencia o enfermedad concreta sin condiciones y protocolo`. El mínimo de cobertura temporal y tratamiento de lagunas son **decisiones de ingeniería**, no valores normativos encontrados.

### 2.7 Sueño/fatiga: el informe no autoriza un solo umbral universal

**SLEEP, p. 7, §III Introduction.** Cuatro ejes: duración habitual de sueño, tiempo despierto, inercia de sueño, fase circadiana. **SLEEP, pp. 15–16**, describe luz, cambios bruscos de horarios y eventos de misión. **STD1, p. 36 [V1 4014]** exige límites de jornada, actividad y sueño establecidos por programa, pero **no define un umbral universal diario**.

**Flujo:** `actigrafía + diario + duty schedule + exposición a luz + quality → sueño/tiempo despierto y variabilidad intraindividual → tendencia y contexto de tarea crítica → evaluación de riesgo de fatiga como investigación o con límites de misión autorizados → seguimiento longitudinal`. No reemplazar una evaluación clínica de trastornos del sueño ni inferir fase circadiana exacta de manera universal.

### 2.8 Cardiovascular / intolerancia ortostática: contexto post-gravedad

**Lee et al. (2025), abstract PubMed, sección Methods.** En 87 persona-misiones ISS, procedimiento de **2 min de reposo prono y 3,5 min de bipedestación**, realizado preflight y postlanding en R+0, +1, +3, +7, +14 y +30; estudió ΔHR/ΔMAP y prendas de compresión. **Es una prueba de reexposición a gravedad y recuperación en tierra; NO un test aplicable tal cual a astronautas flotando en microgravedad.**

**Flujo:** `verificar gravity_environment = postlanding/1g o protocolo clínicamente aprobado para otra gravedad → consentimiento/supervisión si corresponde → adquirir HR/BP/postura/síntomas → comparar ΔHR/ΔMAP con el baseline contextual → mostrar hallazgo observacional con calidad, incertidumbre y comparadores → derivación a criterio autorizado; no diagnosticar ni prescribir compresión/fármacos automáticamente`. Como solo se revisó el resumen, **no están auditados los procedimientos finos del texto completo ni umbrales clínicos**, por lo que el flujo queda RESEARCH_ONLY.

## 3. Qué NO puede atribuirse a la NASA sin revisión adicional

- Una regla universal `z-score < -1.5` como diagnóstico clínico, aunque aparezca exploratoriamente en estudios cognitivos.
- `quality_required=0.90` o `0.95` en el ejemplo previo JSON: **sin justificación documental**; eliminar esos números como umbrales clínicos.
- `EWMA`, MAD, reglas multivariable, pesos o ventanas de persistencia como algoritmos clínicos validados para astronautas: **son elecciones de ingeniería**, salvo prueba específica.
- Diagnosis psiquiátrica, anticoagulación, dosificación, intervención farmacológica autónoma, ajuste de planes de ejercicio y predicción de fractura.
- Tratar los límites de diseño ambiental/PEL como diagnósticos de enfermedad o un protocolo terapéutico.
- Considerar el protocolo de bipedestación como prueba durante vuelo sin gravedad.

## 4. Protocolo ejecutable de SOFTWARE que sí se desprende de estas fuentes

`Entrada → identificar contexto (astronauta, misión, gravedad, fase, cabina, tarea) → normalizar/unidades y controlar calidad → revisar que exista baseline válido/comparable → registrar medidas y tendencias → evaluar requisitos NASA aplicables y reglas secundarias autorizadas → clasificar por separado [cumplimiento normativo, hallazgo de investigación, severidad clínica aprobada, incertidumbre] → generar evaluación guiada si se sustenta → seleccionar únicamente documentos/protocolos aprobados → acción recomendada a CMO (NO actuación automática) → programar reevaluación → guardar evidencia, versión y auditoría`.

Este protocolo es una **síntesis de arquitectura de VIGILE basada en fuentes**, NO un manual clínico de NASA existente. Para intervenciones médicas no se encontró en los textos revisados un protocolo operativo universal y completo; es imprescindible autorización profesional y requisitos específicos de misión.

## 5. Estado de otras fuentes importantes

Las fuentes siguientes son prioritarias, pero **su documento completo todavía requiere extracción y verificación página a página**; no se inventan páginas:

- [ExMC CDSS Architecture HRP-48032 Rev. B (2023)](https://ntrs.nasa.gov/citations/20220017869): registro NASA confirmado; pendiente revisar íntegramente el PDF y sus figuras, arquitectura MDA, módulos y posibles restricciones de derechos.
- [EIMO Concept of Operations (2025)](https://ntrs.nasa.gov/citations/20250000009): registro NASA confirmado; presentación adjunta por revisar; no hay un protocolo farmacológico integral en el resumen.
- [CHP-IDSP Project Updates (2025)](https://ntrs.nasa.gov/citations/20250004859): registro NASA confirmado; integrar los tipos de fuentes de datos mencionados; PDF de presentación por revisar.
- [NASA Muscle/Aerobic Evidence Report (2023)](https://ntrs.nasa.gov/citations/20220019338): página de NTRS confirmada y resumen analizado; PDF completo por revisar, particularmente tareas, dispositivos, respuestas individuales y evidencias.
- [NASA Behavioral Health Evidence Report (2025)](https://ntrs.nasa.gov/citations/20250001454): ficha verificada; DOCX original no auditado.
- [NASA Cognition and Fine Motor Skills Test Batteries (2019/2020)](https://ntrs.nasa.gov/citations/20205008023): ficha y resumen verificados; PDF, tabla de subtests, normalización, practice-effects y permisos de reproducción pendientes.
- NASA ISS Cognition 2024, datos NASA OSDR/ESA, SANS, inmunología, riñón, dosimetría avanzada: pendientes de extracción primaria estructurada.

En la siguiente revisión priorizar por **potencial de reglas clínicas nuevas**, no solo por arquitectura: músculo y sueño completos, Cognition original, sensores de SANS, evidencia inmunológica, cálculos renales, daño radiológico agudo, nutrición, protocolos de triage públicos y catálogos de instrumentos.

## 6. Riesgos y prioridad

**Se puede implementar ya con evidencia localizada:** estructura de datos/seguridad, trazabilidad, cumplimiento de requisitos de VO2max/fuerza/BMD, contabilidad dosimétrica modelada, CO2 en ventana 1h, presión y condiciones de cabina, tendencias y evaluación contextual (no diagnóstica).

**Se puede hacer como investigación con etiquetado:** baselines robustos, EWMA, sleep fatigue risk, cognición research scores, comparación ortostática postlanding, modelos biomecánicos teóricos.

**Bloqueado para medicina autónoma:** tratamiento farmacológico, anticoagulación, diagnóstico definitivo desde wearables, manipulación automática del soporte vital, estimar densidad ósea de un wearable, mostrar como clínicamente validado un scoring no validado.

**No equivale a revisión profesional:** estas fichas son para un prototipo científico de hackathon. Ninguna regla se convierte automáticamente en sistema clínico autorizado por aparecer en norma pública.
