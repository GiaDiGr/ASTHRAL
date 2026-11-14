# VIGILE — Base clínica computable focalizada para diagnóstico, diferencial y protocolos autónomos

## Resumen ejecutivo

Este informe convierte la especificación clínica previa de VIGILE en una primera **base clínica ejecutable y auditable**. Mantiene deliberadamente un alcance estrecho: diabetes/hiperglucemia y cetoacidosis diabética; hipotensión ortostática/POTS; lesión renal aguda; anafilaxia; y un motor diferencial transversal para mareo/taquicardia. Ese alcance coincide con la especificación focalizada aportada para esta iteración y evita volver a expandirse prematuramente a decenas de condiciones. fileciteturn0file0 La arquitectura clínica más amplia y la intención de operar sin dependencia inmediata de Tierra proceden del diseño anterior de VIGILE. fileciteturn0file1

La premisa de autonomía es compatible con la dirección de investigación de NASA, pero no debe confundirse con una autorización de VIGILE. NASA-STD-3001 exige capacidades y recursos para diagnosticar y tratar problemas médicos durante la misión y contempla explícitamente medios para atención médica autónoma y soporte vital avanzado; paralelamente, Exploration Medical Capability investiga CDSS para que las tripulaciones de exploración puedan detectar, diagnosticar, tratar y prevenir problemas cuando la consulta inmediata con Tierra no sea práctica. El concepto EIMO describe una **transferencia gradual** de decisión médica desde Tierra hacia la tripulación y los sistemas de a bordo, no la eliminación de la gobernanza clínica. citeturn19search0turn19search1turn19search2turn19search5

La investigación permite ya construir reglas deterministas sólidas para varias rutas. ADA 2026 aporta criterios cuantitativos y reglas de confirmación para diabetes; el consenso internacional ADA/EASD/AACE/JBDS/DTS de 2024 define DKA mediante tres componentes simultáneos; AHA y los consensos HRS/NIH permiten formalizar hipotensión ortostática y POTS; KDIGO ofrece criterios temporales explícitos para AKI; y WAO ofrece dos vías clínicas bien especificadas para reconocer anafilaxia. citeturn18search0turn21search3turn17search0turn18search3turn27search3turn21search0

La situación de partida para Codex queda así:

| Ruta | Criterios diagnósticos | Confirmación | Diferencial | Protocolo | Aplicabilidad espacial | Estado de implementación recomendado |
|---|---|---|---|---|---|---|
| Diabetes | **VERIFIED** | **VERIFIED** | **VERIFIED** para causas inmediatas relevantes | Confirmación/seguimiento; tratamiento crónico fuera de esta iteración | `REQUIRES_SPACE_SPECIFIC_VALIDATION` | Implementar |
| DKA | **VERIFIED** | **VERIFIED** | **VERIFIED** para cetosis/acidosis y datos faltantes | **PARTIALLY_VERIFIED**; monitorización e insulinoterapia terrestre disponibles | `REQUIRES_SPACE_SPECIFIC_VALIDATION` | Implementar con autorización bloqueada |
| Hipotensión ortostática | **VERIFIED** en gravedad | Medición ortostática válida | **VERIFIED** | Manejo etiológico/no farmacológico inicial | `NOT_APPLICABLE` en microgravedad libre; limitado tras transición | Implementar |
| POTS | **VERIFIED/PARTIAL** | Síntomas crónicos + exclusión de imitadores | **VERIFIED** | Manejo inicial disponible; no automatizar farmacoterapia | `REQUIRES_SPACE_SPECIFIC_VALIDATION` | Implementar como síndrome condicionado |
| AKI | **VERIFIED** con KDIGO 2012 | Baseline/ventana o diuresis | **VERIFIED** en alto nivel | Evaluación etiológica y soporte | `REQUIRES_SPACE_SPECIFIC_VALIDATION` | Implementar |
| Anafilaxia | **VERIFIED** | No requiere una prueba de laboratorio previa | **VERIFIED** | Epinefrina IM de primera línea bien definida | `APPLICABLE_WITH_LIMITATIONS` | Implementar como emergencia |
| Mareo/taquicardia | No es un diagnóstico | No aplica | **Motor determinista propuesto** | Deriva a la ruta apropiada | Dependiente del contexto gravitatorio | Implementar como orquestador |

Una precisión importante sobre AKI: a 16 de octubre de 2026, KDIGO mantiene publicada una **actualización 2026 como borrador de revisión**, mientras el sitio oficial indica que el grupo de trabajo está preparando la publicación definitiva. Por tanto, VIGILE no debe sustituir automáticamente el criterio final de 2012 por el borrador 2026. citeturn17search5turn17search6turn17search8

El resultado clínico tampoco debe ser un único `ClinicalState`. Diagnóstico, urgencia, confirmación, elegibilidad de protocolo y tratamiento son dimensiones independientes. La misma persona puede tener simultáneamente `diagnostic_status=CRITERIA_MET`, `urgency=EMERGENCY`, `confirmation_status=NOT_REQUIRED`, `protocol_status=READY_FOR_CREW` y `treatment_status=NOT_STARTED`. Esta separación es especialmente importante para anafilaxia y DKA, donde una emergencia puede requerir actuación antes de alcanzar una certeza etiológica más amplia. La propuesta siguiente es una inferencia arquitectónica basada en cómo las guías separan diagnóstico, evaluación y tratamiento. citeturn21search0turn24search0

```text
OBSERVACIONES
     ↓
VALIDACIÓN DE CALIDAD Y CONTEXTO
     ↓
┌─────────────────────────────────────────────┐
│ evaluación diagnóstica                      │
│ diagnostic_status                           │
└─────────────────────────────────────────────┘
     ↓                ↓
URGENCIA          CONFIRMACIÓN
     ↓                ↓
DIAGNÓSTICO DIFERENCIAL
     ↓
PRUEBAS QUE FALTAN
     ↓
PROTOCOLO CANDIDATO
     ↓
AUTORIZACIÓN + RECURSOS + CONTRAINDICACIONES
     ↓
ACTUACIÓN
     ↓
REEVALUACIÓN
```

El principio de seguridad central debe ser:

```text
dato ausente ≠ dato normal
cribado positivo ≠ diagnóstico
criterio no satisfecho ≠ enfermedad excluida
criterio terrestre ≠ criterio validado en microgravedad
protocolo respaldado por evidencia ≠ protocolo autorizado para la misión
```

## Base documental y decisiones de alcance

NASA proporciona una justificación operacional fuerte para construir este tipo de sistema. Su estándar de atención durante misión, `[V1 3004]`, exige que los programas proporcionen entrenamiento, capacidades y recursos para diagnosticar y tratar condiciones potenciales teniendo en cuenta guías clínicas, necesidades individuales, expertise médica, parámetros de misión y limitaciones del vehículo. El mismo requisito enumera laboratorios, ECG, medicamentos, tratamiento del disbarismo y medios de atención autónoma. El EIMO ConOps de NASA describe un sistema de sistemas que combine bases de referencia, wearables, point-of-care diagnostics y datos ambientales para ayudar al Crew Medical Officer cuando el apoyo terrestre esté retrasado o no disponible. citeturn19search0turn19search2

Eso **no demuestra que los criterios terrestres hayan sido validados automáticamente para astronautas**. NASA documenta, por ejemplo, que la intolerancia ortostática es particularmente relevante al volver a un entorno gravitatorio después de microgravedad y la relaciona con disminución del volumen plasmático y alteraciones del control simpático. NASA también documenta cambios de fluidos durante el vuelo. Por tanto, el test terrestre de ponerse de pie no es técnicamente equivalente durante microgravedad libre. citeturn24search3turn24search4

La situación renal merece una cautela similar. Investigación publicada en *Nature Communications* utilizando datos y muestras de vuelos espaciales encontró remodelación renal y alteraciones funcionales asociadas con microgravedad y exposición simulada a radiación de espacio profundo; NASA, por su parte, identifica deshidratación relativa, cambios en bioquímica urinaria, dinámica de fluidos y metabolismo óseo como factores relevantes para la salud urinaria espacial. Esto justifica conservar los criterios KDIGO terrestres como referencia explícita, pero etiquetarlos `REQUIRES_SPACE_SPECIFIC_VALIDATION`, no modificar sus umbrales sin evidencia. citeturn25search0turn25search5

**Fuentes de producción verificadas para esta iteración**

| ID | Fuente | Uso |
|---|---|---|
| `SRC-NASA-STD3001-V1-2023` | NASA-STD-3001 Vol. 1, §3.5 `[V1 3004]` | Gobernanza y autonomía |
| `SRC-NASA-EIMO-2025` | EIMO Concept of Operations | Arquitectura de autonomía |
| `SRC-ADA-DX-2026` | ADA Standards 2026 §2, DOI `10.2337/dc26-S002` | Diabetes |
| `SRC-DKA-2024` | Hyperglycemic Crises Consensus, DOI `10.2337/dci24-0032` | DKA |
| `SRC-AHA-OH-2024` | AHA Scientific Statement, DOI `10.1161/HYP.0000000000000236` | Hipotensión ortostática |
| `SRC-HRS-POTS-2015` | HRS Consensus, DOI `10.1016/j.hrthm.2015.03.029` | POTS |
| `SRC-NIH-POTS-2021` | NIH expert consensus, DOI `10.1016/j.autneu.2021.102828` | POTS y exclusiones |
| `SRC-KDIGO-AKI-2012` | KDIGO §2.1, DOI `10.1038/kisup.2011.32` | AKI |
| `SRC-WAO-ANAPH-2020` | WAO Guidance, DOI `10.1016/j.waojou.2020.100472` | Anafilaxia |

Los criterios de diabetes están particularmente bien especificados. ADA 2026 acepta A1C ≥6,5 %, FPG ≥126 mg/dL tras al menos ocho horas sin aporte calórico, glucosa plasmática a las dos horas ≥200 mg/dL tras OGTT de 75 g o glucosa plasmática aleatoria ≥200 mg/dL acompañada de síntomas clásicos o crisis hiperglucémica. Salvo hiperglucemia inequívoca, son necesarios dos resultados anormales; ADA también declara insuficiente la evidencia para usar CGM como prueba diagnóstica de diabetes. citeturn18search0turn21search1

Para DKA, el consenso 2024 exige **los tres componentes**: diabetes conocida o glucosa ≥200 mg/dL; cetosis con β-hidroxibutirato ≥3,0 mmol/L o cetonuria ≥2+; y acidosis con pH <7,3 y/o bicarbonato <18 mmol/L. El nuevo criterio permite reconocer DKA euglucémica cuando existe diabetes conocida y se cumplen cetosis y acidosis. citeturn21search3turn21search6

AHA define hipotensión ortostática como una reducción sostenida de PAS de al menos 20 mmHg o PAD de al menos 10 mmHg dentro de los tres minutos posteriores a ponerse de pie. POTS, en cambio, requiere incremento sostenido de frecuencia cardíaca ≥30 lpm en adultos —≥40 lpm entre 12 y 19 años— durante los primeros diez minutos de postura erguida, ausencia de hipotensión ortostática, síntomas ortostáticos que mejoren al volver al decúbito, persistencia durante al menos tres meses y ausencia de causas alternativas como deshidratación, anemia, fiebre, infección, dolor, hipertiroidismo, medicamentos o desacondicionamiento severo. citeturn17search0turn18search3turn18search5

KDIGO define AKI mediante cualquiera de tres vías: aumento de creatinina sérica ≥0,3 mg/dL en 48 horas; creatinina ≥1,5 veces el baseline conocida o presumiblemente ocurrida en los siete días previos; o diuresis <0,5 mL/kg/h durante seis horas. La estratificación KDIGO utiliza el peor criterio de creatinina o diuresis. citeturn22view0turn23view0turn23view1turn27search3

WAO considera altamente probable anafilaxia mediante dos vías: inicio agudo con afectación cutáneo-mucosa más compromiso respiratorio, disminución de presión/disfunción de órgano diana o síntomas gastrointestinales graves; o hipotensión, broncoespasmo o compromiso laríngeo después de un alérgeno conocido o muy probable, incluso sin manifestaciones cutáneas. En adultos, hipotensión incluye PAS <90 mmHg o una reducción >30 % respecto del baseline. citeturn21search0turn21search5

## Criterios computables por ruta clínica

**Diabetes e hiperglucemia**

VIGILE debe diferenciar cuatro clases de dato: glucosa plasmática en ayunas, glucosa plasmática aleatoria, glucosa plasmática a las dos horas de OGTT y A1C. Una lectura CGM/intersticial puede activar una necesidad de confirmación, pero no debe satisfacer directamente el criterio ADA 2026. A1C requiere método apropiado; si existe discordancia sustancial con glucosa o una situación que altera la relación A1C-glucemia, ADA recomienda investigar interferencias y utilizar criterios de glucosa plasmática en los contextos descritos. citeturn18search0turn21search1

```text
DM_DIAGNOSTIC_EVALUATION

if random_plasma_glucose >= 200 mg/dL
   and (classic_hyperglycemia_symptoms or hyperglycemic_crisis):
       diagnostic_status = CRITERIA_MET
       confirmation_status = NOT_REQUIRED

else:
    qualifying_results =
        A1C >= 6.5% with valid method
        OR FPG >= 126 mg/dL with fasting >= 8 h
        OR 2h_PG >= 200 mg/dL after valid 75-g OGTT

    if two qualifying abnormal results:
        diagnostic_status = CRITERIA_MET
        confirmation_status = SATISFIED
    elif one qualifying result:
        diagnostic_status = SUSPECTED
        confirmation_status = REQUIRED
    elif required measurement quality invalid:
        diagnostic_status = INSUFFICIENT_DATA
    else:
        diagnostic_status = CRITERIA_NOT_MET
```

La regla de confirmación no obliga a que sean dos pruebas distintas: ADA permite dos pruebas anormales diferentes en la misma ocasión o la misma prueba en dos momentos; ante resultados discordantes, debe repetirse la prueba que queda por encima de su punto diagnóstico. citeturn18search0

**Cetoacidosis diabética**

```text
D = prior_diabetes OR plasma_glucose >= 200 mg/dL
K = beta_hydroxybutyrate >= 3.0 mmol/L OR urine_ketones >= 2+
A = venous_pH < 7.3 OR bicarbonate < 18 mmol/L

DKA = D AND K AND A
```

El β-hidroxibutirato sanguíneo es preferible cuando está disponible. El consenso señala que ≥3 mmol/L tiene una relación fuerte con el cuadro ácido-base y que la medición point-of-care puede utilizarse si existen salvaguardas de entrenamiento y rendimiento del instrumento. El anion gap puede ser informativo, pero no debe convertirse en requisito primario de diagnóstico o resolución. citeturn21search3turn24search0

La ruta terapéutica debe ser una máquina de estados. El consenso recomienda glucosa cada 1–2 horas y electrolitos, creatinina, fosfato, β-hidroxibutirato y pH venoso cada cuatro horas durante tratamiento; insulina IV de acción corta suele iniciarse a 0,1 U/kg/h; cuando la glucosa baja de 250 mg/dL se añade 5–10 % de dextrosa y se reduce a 0,05 U/kg/h. Si K <3,5 mmol/L, se inicia reposición de potasio y se retrasa la insulina hasta K >3,5 mmol/L. Estos son regímenes terrestres del consenso, no regímenes espacialmente validados. citeturn24search0

```text
DKA_CRITERIA_MET
   ↓
mission protocol authorized?
   NO → PROTOCOL_NOT_AUTHORIZED
   YES
   ↓
required monitoring resources present?
   NO → BLOCKED_RESOURCE
   YES
   ↓
serum potassium known?
   NO → BLOCKED_MISSING_SAFETY_DATA
   YES
   ↓
K < 3.5 mmol/L?
   YES → HOLD_INSULIN / potassium pathway
   NO  → insulin pathway
```

**Hipotensión ortostática y POTS**

```text
CLASSIC_OH =
    standing_window <= 3 min
AND
    (
       delta_SBP <= -20 mmHg
       OR delta_DBP <= -10 mmHg
    )
```

Este resultado reconoce **hipotensión ortostática presente**, pero no su etiología. La AHA recomienda caracterizar patrones, desencadenantes y causa, además de revisar factores agravantes y medicamentos. citeturn17search0turn26search2

Para POTS:

```text
POTS =
    adult
AND sustained_delta_HR >= 30 bpm within 10 min upright
AND NOT classic_OH
AND frequent_orthostatic_symptoms
AND symptoms_improve_supine
AND duration >= 3 months
AND no_alternative_explanation
```

El consenso HRS reconoce el umbral de ≥30 lpm en adultos y ≥40 lpm entre 12 y 19 años; el consenso NIH añade explícitamente duración mínima de tres meses y exclusión de causas alternativas. citeturn17search2turn17search7turn18search3

En VIGILE, `dehydration`, `recent_blood_loss`, `anemia`, `fever_or_infection`, `pain`, `hyperthyroidism`, determinados medicamentos y `severe_deconditioning` deben funcionar como **bloqueadores de la etiqueta POTS**, no como simples notas. citeturn18search3turn18search5

Durante microgravedad libre, VIGILE no debe ejecutar literalmente un test terrestre basado en «standing». Esto se clasifica `NOT_APPLICABLE` para esa fase; tras retorno a gravedad o en una superficie con gravedad, el test puede volver a ser conceptualmente aplicable, pero con `APPLICABLE_WITH_LIMITATIONS`. Esta clasificación es una inferencia de ingeniería clínica basada en el carácter gravitatorio de la prueba y en la fisiología espacial documentada por NASA, no un nuevo criterio NASA para POTS. citeturn24search3turn24search4

**Lesión renal aguda**

```text
AKI =
    SCr_increase >= 0.3 mg/dL within 48 h
OR
    SCr_current >= 1.5 * baseline within prior 7 days
OR
    urine_output < 0.5 mL/kg/h for >= 6 h
```

Estadificación adulta:

```text
Stage 1:
  creatinine = 1.5–1.9 × baseline OR increase >= 0.3 mg/dL
  OR urine_output <0.5 mL/kg/h for 6–12 h

Stage 2:
  creatinine = 2.0–2.9 × baseline
  OR urine_output <0.5 mL/kg/h for >=12 h

Stage 3:
  creatinine = >=3.0 × baseline
  OR creatinine >=4.0 mg/dL
  OR renal_replacement_therapy_started
  OR urine_output <0.3 mL/kg/h for >=24 h
  OR anuria >=12 h
```

Estos criterios corresponden a KDIGO 2012, que sigue siendo la base final verificable mientras el documento 2026 permanece en proceso de actualización. citeturn23view0turn23view1turn17search6

VIGILE debe calcular AKI tanto por creatinina como por diuresis y conservar el criterio más grave. Un baseline inexistente no puede transformarse en un valor «normal» inventado. Si no existe suficiente historial para la vía de creatinina y tampoco existe diuresis válida, la salida correcta es `INSUFFICIENT_DATA`. KDIGO además recomienda determinar la causa siempre que sea posible y monitorizar creatinina y diuresis. citeturn22view0turn27search3

**Anafilaxia**

```text
PATH_A =
    acute_onset_minutes_to_hours
AND skin_or_mucosal_involvement
AND (
       respiratory_compromise
       OR reduced_BP_or_end_organ_dysfunction
       OR severe_GI_symptoms
    )

PATH_B =
    acute_onset_minutes_to_hours
AND known_or_highly_probable_allergen
AND (
       hypotension
       OR bronchospasm
       OR laryngeal_involvement
    )

ANAPHYLAXIS = PATH_A OR PATH_B
```

Para un adulto:

```text
hypotension =
    SBP < 90 mmHg
OR
    SBP_drop_from_baseline > 30%
```

La vía B es particularmente importante porque permite reconocer anafilaxia sin urticaria. citeturn21search0turn21search5

En este caso, diagnóstico y respuesta de emergencia deben procesarse en paralelo. La epinefrina IM es primera línea; WAO indica 0,01 mg/kg hasta un máximo de 0,5 mg y repetición cada 5–15 minutos si los síntomas son refractarios. WAO señala además que no existe una contraindicación absoluta para epinefrina IM en el tratamiento de anafilaxia, mientras que el bolo IV no es la vía inicial recomendada por su mayor riesgo y exige monitorización y personal experimentado si se emplean infusiones IV en casos refractarios. citeturn17search3turn17search4turn24search1

**Motor mareo/taquicardia**

Esta quinta ruta no debe fingir que «mareo + taquicardia» es una enfermedad. Es un **orquestador de hipótesis**.

```text
1. Buscar amenaza inmediata.
2. Evaluar reglas clínicas completas disponibles.
3. Detectar imitadores/exclusiones.
4. Determinar datos que faltan.
5. Seleccionar pruebas que discriminan varias hipótesis.
6. Ordenar las hipótesis por categorías transparentes,
   no por probabilidades inventadas.
```

Un orden determinista adecuado para esta primera versión es:

```text
TIME_CRITICAL_CRITERIA_MET
TIME_CRITICAL_SUSPECTED
CRITERIA_MET
HIGH_PRIORITY_UNRESOLVED
COMPATIBLE
WEAK_SUPPORT
CONTRADICTED
NOT_EVALUABLE
```

Así, un astronauta con mareo, taquicardia y caída de PAS de 25 mmHg durante una prueba ortostática válida debe priorizar la ruta de hipotensión ortostática y marcar POTS como contradictorio; un astronauta con aumento de FC de 35 lpm pero deshidratación aguda no debe recibir la etiqueta POTS; y un astronauta con taquicardia, broncoespasmo y exposición reciente a un alérgeno debe activar primero la ruta de anafilaxia. Estas son aplicaciones deterministas de los criterios anteriores, no probabilidades clínicas nuevas. citeturn17search0turn18search3turn21search0

## Diferenciales, pruebas y protocolos

La siguiente matriz es deliberadamente conservadora: VIGILE solo resuelve automáticamente las rutas cuyos criterios han sido incluidos en esta investigación. Enfermedades potencialmente graves ajenas al alcance, como embolia pulmonar o determinadas arritmias, pueden aparecer como `EXTERNAL_PATHWAY_REQUIRED`, pero Codex no debe inventar sus criterios para completar el diferencial.

| Presentación | Primero evaluar | Hipótesis dentro de esta versión | Prueba/dato discriminante |
|---|---|---|---|
| Mareo + taquicardia | Inestabilidad/anaphylaxis | OH, POTS, hipovolemia, DKA | BP/HR ortostáticos, exposición, glucosa, cetonas, pH/bicarbonato |
| Hipotensión + debilidad | Anafilaxia/inestabilidad | OH, hipovolemia, DKA | Relación postural, alérgeno, glucosa/cetonas, historia de pérdidas |
| Hiperglucemia + náuseas | DKA | Diabetes, DKA, hiperglucemia no confirmada | β-OHB, pH venoso, bicarbonato |
| Taquicardia + disnea | Anafilaxia primero si exposición | POTS solo si claramente postural/crónico; causas externas | BP, SpO₂, exposición, ECG como ruta externa |
| Oliguria + creatinina alterada | AKI | Prerrenal/renal/posrenal como etiologías | Serie SCr, UO, volumen, fármacos, evaluación de obstrucción |
| Alérgeno + síntomas respiratorios | Anafilaxia | Reacción alérgica no anafiláctica / ruta respiratoria externa | BP, piel/mucosa, broncoespasmo, laringe |

KDIGO considera AKI un síndrome de múltiples etiologías, incluyendo causas prerrenales, intrínsecas y posrenales, y recomienda buscar causas reversibles. Por tanto, que VIGILE satisfaga el criterio AKI no debe cerrar el razonamiento etiológico. citeturn27search3turn22view0

De modo equivalente, la hipotensión ortostática es un hallazgo/síndrome hemodinámico que requiere caracterizar causas y factores agravantes; POTS exige excluir estados que producen taquicardia sinusal ortostática secundaria. citeturn26search2turn18search3

**Protocolos de esta primera iteración**

Para diabetes sin crisis, el protocolo implementado debe ser primordialmente de **confirmación**, no de prescripción farmacológica. Un resultado aislado que supera un umbral en una persona sin síntomas debe llevar a repetición apropiada; un CGM elevado debe conducir a una medición diagnóstica válida, no a `CRITERIA_MET`. citeturn18search0turn21search1

Para DKA, ya existe suficiente especificación terrestre para modelar diagnóstico, monitorización y varios guardarraíles terapéuticos, pero el protocolo espacial debe comenzar `MISSION_APPROVED=false`. El consenso de 2024 exige monitorización intensiva y advierte especialmente sobre potasio e hipoglucemia durante insulinoterapia. citeturn24search0

Para OH/POTS, HRS favorece comenzar con medidas no farmacológicas, revisión de medicamentos, volumen/hidratación, compresión y ejercicio; la evidencia farmacológica es más limitada y varias recomendaciones tienen clases de evidencia modestas. En VIGILE v1 clínica, conviene representar esas intervenciones como opciones respaldadas pero dejar la farmacoterapia específica fuera del protocolo ejecutable hasta disponer de una política médica de misión. citeturn26search0turn26search3

Para AKI, KDIGO recomienda evaluación pronta de la causa, atención especial a causas reversibles, monitorización de creatinina y diuresis y manejo acorde con etapa y causa. KDIGO favorece cristaloides isotónicos sobre coloides para expansión intravascular en pacientes con AKI o riesgo de AKI en ausencia de shock hemorrágico, y desaconseja utilizar diuréticos para prevenir AKI o tratarla salvo en manejo de sobrecarga de volumen. citeturn22view0

Para anafilaxia, la epinefrina IM es el caso más claro de protocolo de emergencia. WAO también contempla oxígeno de alto flujo ante dificultad respiratoria o dosis adicionales de epinefrina y cristaloides IV en inestabilidad cardiovascular. Sin embargo, VIGILE debe comprobar concentración, vía, inventario y autorización de misión antes de presentar un protocolo como operativo. citeturn24search1

**Aplicabilidad espacial**

| Ruta | Clasificación | Motivo |
|---|---|---|
| Diabetes | `REQUIRES_SPACE_SPECIFIC_VALIDATION` | Criterios terrestres bien establecidos; no se verificó validación diagnóstica específica en microgravedad |
| DKA | `REQUIRES_SPACE_SPECIFIC_VALIDATION` | Diagnóstico y tratamiento terrestre verificables; monitorización intensiva y PK/PD/recursos de misión requieren validación |
| OH | `NOT_APPLICABLE` en microgravedad libre; `APPLICABLE_WITH_LIMITATIONS` en gravedad | La prueba depende de transición a posición erguida/gravedad |
| POTS | `NOT_APPLICABLE` para test de pie en microgravedad libre; `REQUIRES_SPACE_SPECIFIC_VALIDATION` después | Desacondicionamiento espacial puede imitar componentes del síndrome |
| AKI | `REQUIRES_SPACE_SPECIFIC_VALIDATION` | Criterio terrestre válido como referencia, pero fisiología renal espacial cambia |
| Anafilaxia | `APPLICABLE_WITH_LIMITATIONS` | Síndrome agudo clínico general; logística, posición, administración y recursos cambian |

Las clasificaciones espaciales anteriores son **decisiones de ingeniería clínica inferidas de la evidencia**, no categorías oficiales emitidas por NASA. NASA sí documenta cambios cardiovasculares/volémicos, intolerancia ortostática tras microgravedad, riesgos urinarios y la necesidad de atención autónoma contextualizada por los recursos de cada misión. citeturn19search2turn24search3turn25search0turn25search5

## Arquitectura clínica y algoritmos

VIGILE debe abandonar la idea de un único enum clínico. El objeto resultante debe separar cinco dimensiones:

```text
diagnostic_status
    NOT_EVALUATED
    INSUFFICIENT_DATA
    SUSPECTED
    CRITERIA_MET
    CRITERIA_NOT_MET
    CONFLICTING_EVIDENCE
    NOT_APPLICABLE

urgency
    ROUTINE
    PROMPT
    URGENT
    EMERGENCY

confirmation_status
    NOT_APPLICABLE
    NOT_REQUIRED
    REQUIRED
    PENDING
    SATISFIED
    UNAVAILABLE

protocol_status
    NOT_EVALUATED
    NOT_INDICATED
    ELIGIBLE
    BLOCKED_MISSING_DATA
    BLOCKED_CONTRAINDICATION
    BLOCKED_RESOURCE
    BLOCKED_AUTHORIZATION
    READY_FOR_CREW

treatment_status
    NOT_STARTED
    STARTED
    MONITORING
    HELD
    FAILED
    COMPLETED
```

Esto evita transiciones conceptualmente falsas como:

```text
SCREENING_POSITIVE → DIAGNOSIS_CONFIRMED
```

y permite en su lugar:

```text
SUSPECTED
  ↓
REQUIRED confirmation
  ↓
SATISFIED
  ↓
CRITERIA_MET

mientras, independientemente:

EMERGENCY
  ↓
ELIGIBLE
  ↓
READY_FOR_CREW
```

**Evaluación diagnóstica**

```python
def evaluate_diagnostic_criterion(criterion, patient, context):
    assert criterion.source_status == "CURRENT"

    if not criterion.applies_to(context):
        return result(diagnostic_status="NOT_APPLICABLE")

    quality = validate_required_measurements(
        patient=patient,
        requirements=criterion.measurement_quality,
    )

    if quality.invalid_required:
        return result(
            diagnostic_status="INSUFFICIENT_DATA",
            missing=quality.missing,
            invalid=quality.invalid,
        )

    tree_result = evaluate_boolean_tree(
        criterion.logic,
        patient=patient,
        context=context,
        missing_policy="UNKNOWN_NEVER_FALSE_OR_NORMAL",
    )

    if tree_result.conflicting:
        diagnostic_status = "CONFLICTING_EVIDENCE"
    elif tree_result.true:
        diagnostic_status = "CRITERIA_MET"
    elif tree_result.missing_required:
        diagnostic_status = "INSUFFICIENT_DATA"
    elif tree_result.partial_support:
        diagnostic_status = "SUSPECTED"
    else:
        diagnostic_status = "CRITERIA_NOT_MET"

    confirmation = evaluate_confirmation_rule(
        criterion.confirmation,
        patient,
        diagnostic_status,
    )

    return build_traceable_result(
        diagnostic_status=diagnostic_status,
        confirmation_status=confirmation,
        evaluated_nodes=tree_result.trace,
    )
```

**Diferencial determinista no probabilístico**

```python
def rank_differential(presentation, patient, candidate_pathways):
    results = []

    for hypothesis in candidate_pathways:
        result = evaluate_hypothesis(hypothesis, patient)

        if result.time_critical and result.criteria_met:
            tier = "TIME_CRITICAL_CRITERIA_MET"
        elif result.time_critical and result.supported:
            tier = "TIME_CRITICAL_SUSPECTED"
        elif result.criteria_met:
            tier = "CRITERIA_MET"
        elif result.required_data_missing and result.supported:
            tier = "HIGH_PRIORITY_UNRESOLVED"
        elif result.supported:
            tier = "COMPATIBLE"
        elif result.contradicted:
            tier = "CONTRADICTED"
        else:
            tier = "NOT_EVALUABLE"

        results.append((hypothesis.id, tier, result.trace))

    return deterministic_sort(results)
```

No se genera un «73 % de probabilidad de POTS» porque este proyecto no dispone de una calibración probabilística validada para astronautas.

**Selección de pruebas**

```python
def choose_next_tests(active_hypotheses, resources):
    candidates = collect_missing_tests(active_hypotheses)

    for test in candidates:
        test.priority = lexicographic_rank(
            time_critical_exclusion=test.rules_out_time_critical,
            required_for_diagnosis=test.required_for_criterion,
            discriminates_hypotheses=test.discrimination_count,
            available=resources.contains(test.resource_id),
            patient_risk=test.risk_class,
            resource_cost=test.resource_cost,
        )

    return sorted(candidates, key=lambda t: t.priority)
```

La selección es lexicográfica y explicable; no pretende ser una utilidad clínica probabilística validada.

**Elegibilidad de protocolo**

```python
def evaluate_protocol(protocol, clinical_result, patient, mission):
    if clinical_result.diagnostic_status not in protocol.allowed_states:
        return "NOT_INDICATED"

    if protocol.required_safety_data_missing(patient):
        return "BLOCKED_MISSING_DATA"

    if protocol.has_contraindication(patient):
        return "BLOCKED_CONTRAINDICATION"

    if not mission.resources.satisfy(protocol.required_resources):
        return "BLOCKED_RESOURCE"

    if not mission.authorization.allows(protocol.id):
        return "BLOCKED_AUTHORIZATION"

    return "READY_FOR_CREW"
```

**Reevaluación longitudinal**

```python
def reevaluate(previous, new_observations, knowledge_version):
    merged = append_immutable(previous.input_history, new_observations)

    current = run_full_evaluation(
        observations=merged,
        knowledge_version=knowledge_version,
    )

    delta = compare(
        old=previous,
        new=current,
        dimensions=[
            "diagnostic_status",
            "urgency",
            "confirmation_status",
            "protocol_status",
            "treatment_status",
        ],
    )

    if delta.clinical_deterioration:
        current.flags.add("DETERIORATION")

    persist_replayable_trace(previous, current, delta)
    return current
```

El enfoque encaja con el concepto NASA de un CDSS que integre datos contextuales y ayude a la tripulación a observar, evaluar, decidir y actuar, pero la especificación concreta de algoritmos anterior es diseño de VIGILE, no software NASA. citeturn19search4turn19search5

## Artefactos JSON embebidos

Los siguientes bloques constituyen los artefactos que Codex debe materializar en archivos. Los identificadores entre ellos son consistentes. Las reglas clínicas se vinculan a las fuentes verificadas descritas arriba. citeturn18search0turn21search3turn17search0turn18search3turn27search3turn21search0

**`sources_verified.json`**

```json
{
  "schema_version": "1.0.0",
  "as_of_date": "2026-10-16",
  "sources": [
    {
      "source_id": "SRC-NASA-STD3001-V1-2023",
      "organization": "NASA",
      "title": "NASA Spaceflight Human-System Standard Volume 1 — Crew Health",
      "year": 2023,
      "section": "3.5 In-Mission Medical Care; V1 3004",
      "doi": null,
      "url": "https://www.nasa.gov/reference/3-0-health-and-medical-care/",
      "type": "OFFICIAL_STANDARD",
      "verification": "VERIFIED",
      "use": ["governance", "autonomous_medical_care"]
    },
    {
      "source_id": "SRC-NASA-EIMO-2025",
      "organization": "NASA",
      "title": "Earth-Independent Medical Operations (EIMO) Concept of Operations",
      "year": 2025,
      "section": "Concept of Operations / system overview",
      "doi": null,
      "url": "https://ntrs.nasa.gov/citations/20250000009",
      "type": "NASA_TECHNICAL_REPORT",
      "verification": "VERIFIED",
      "use": ["autonomy", "clinical_decision_support"]
    },
    {
      "source_id": "SRC-NASA-CDSS-2023",
      "organization": "NASA / npj Microgravity",
      "title": "The Value of a Spaceflight Clinical Decision Support System for Earth-Independent Medical Operations",
      "year": 2023,
      "section": "Full article",
      "doi": "10.1038/s41526-023-00284-1",
      "url": "https://ntrs.nasa.gov/citations/20220007443",
      "type": "PEER_REVIEWED_PRIMARY",
      "verification": "VERIFIED",
      "use": ["autonomy", "CDSS"]
    },
    {
      "source_id": "SRC-ADA-DX-2026",
      "organization": "American Diabetes Association",
      "title": "2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes—2026",
      "year": 2026,
      "section": "Table 2.1; Recommendations 2.1a–2.4; Confirming the Diagnosis",
      "doi": "10.2337/dc26-S002",
      "url": "https://doi.org/10.2337/dc26-S002",
      "type": "CLINICAL_STANDARD",
      "verification": "VERIFIED",
      "use": ["diabetes_diagnosis"]
    },
    {
      "source_id": "SRC-DKA-2024",
      "organization": "ADA/EASD/AACE/JBDS/DTS expert panel",
      "title": "Hyperglycemic Crises in Adults With Diabetes: A Consensus Report",
      "year": 2024,
      "section": "Section 3, Figure 2A, Table 2; Section 4",
      "doi": "10.2337/dci24-0032",
      "url": "https://doi.org/10.2337/dci24-0032",
      "type": "MULTISOCIETY_CONSENSUS_REPORT",
      "verification": "VERIFIED",
      "use": ["DKA_diagnosis", "DKA_monitoring", "DKA_treatment"]
    },
    {
      "source_id": "SRC-AHA-OH-2024",
      "organization": "American Heart Association",
      "title": "Orthostatic Hypotension in Adults With Hypertension: A Scientific Statement From the American Heart Association",
      "year": 2024,
      "section": "Definition and diagnostic/management discussion",
      "doi": "10.1161/HYP.0000000000000236",
      "url": "https://doi.org/10.1161/HYP.0000000000000236",
      "type": "SCIENTIFIC_STATEMENT",
      "verification": "VERIFIED",
      "use": ["orthostatic_hypotension"]
    },
    {
      "source_id": "SRC-HRS-POTS-2015",
      "organization": "Heart Rhythm Society and collaborating societies",
      "title": "2015 Heart Rhythm Society Expert Consensus Statement on POTS, Inappropriate Sinus Tachycardia, and Vasovagal Syncope",
      "year": 2015,
      "section": "Section 1 — POTS definition and treatment recommendations",
      "doi": "10.1016/j.hrthm.2015.03.029",
      "url": "https://www.hrsonline.org/resource/2015-heart-rhythm-society-expert-consensus-statement-diagnosis-and-treatment-postural-tachycardia/",
      "type": "EXPERT_CONSENSUS",
      "verification": "VERIFIED",
      "use": ["POTS_definition", "POTS_management"]
    },
    {
      "source_id": "SRC-NIH-POTS-2021",
      "organization": "NIH expert consensus meeting participants",
      "title": "Postural orthostatic tachycardia syndrome: State of the science and clinical care from a 2019 NIH Expert Consensus Meeting — Part 1",
      "year": 2021,
      "section": "Section 2 — Clinical description",
      "doi": "10.1016/j.autneu.2021.102828",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8455420/",
      "type": "EXPERT_CONSENSUS_REPORT",
      "verification": "VERIFIED",
      "use": ["POTS_duration", "POTS_exclusions"]
    },
    {
      "source_id": "SRC-KDIGO-AKI-2012",
      "organization": "KDIGO",
      "title": "KDIGO Clinical Practice Guideline for Acute Kidney Injury — Section 2: AKI Definition",
      "year": 2012,
      "section": "Chapter 2.1; Table 2",
      "doi": "10.1038/kisup.2011.32",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4089595/",
      "type": "CLINICAL_GUIDELINE",
      "verification": "VERIFIED",
      "use": ["AKI_definition", "AKI_staging"]
    },
    {
      "source_id": "SRC-KDIGO-AKI-DRAFT-2026",
      "organization": "KDIGO",
      "title": "KDIGO 2026 Clinical Practice Guideline for AKI and AKD — Public Review Draft",
      "year": 2026,
      "section": "Draft status only",
      "doi": null,
      "url": "https://kdigo.org/kdigo-2026-aki-akd-guideline-draft-available-for-public-review/",
      "type": "DRAFT_GUIDELINE",
      "verification": "DRAFT_NOT_FOR_PRODUCTION",
      "use": ["version_monitoring"]
    },
    {
      "source_id": "SRC-WAO-ANAPH-2020",
      "organization": "World Allergy Organization",
      "title": "World Allergy Organization Anaphylaxis Guidance 2020",
      "year": 2020,
      "section": "Figure 1 diagnostic criteria; Management; Table 6",
      "doi": "10.1016/j.waojou.2020.100472",
      "url": "https://doi.org/10.1016/j.waojou.2020.100472",
      "type": "GUIDANCE",
      "verification": "VERIFIED_CURRENT_DOCUMENT",
      "use": ["anaphylaxis_diagnosis", "anaphylaxis_treatment"]
    },
    {
      "source_id": "SRC-NASA-OI",
      "organization": "NASA",
      "title": "Fundamentals of Human Health — Orthostatic Intolerance",
      "year": null,
      "section": "Orthostatic Intolerance",
      "doi": null,
      "url": "https://www.nasa.gov/reference/fundamentals-of-human-health/",
      "type": "NASA_OFFICIAL_REFERENCE",
      "verification": "VERIFIED",
      "use": ["space_orthostatic_context"]
    },
    {
      "source_id": "SRC-SPACE-KIDNEY-2024",
      "organization": "Nature Communications",
      "title": "Cosmic kidney disease: an integrated pan-omic, physiological and morphological study into spaceflight-induced renal dysfunction",
      "year": 2024,
      "section": "Full article",
      "doi": "10.1038/s41467-024-49212-1",
      "url": "https://doi.org/10.1038/s41467-024-49212-1",
      "type": "PRIMARY_RESEARCH",
      "verification": "VERIFIED",
      "use": ["space_renal_context"]
    }
  ]
}
```

Las versiones, DOI y estados del registro corresponden a las fuentes primarias u oficiales verificadas; en particular, KDIGO 2026 permanece identificado como borrador y no como sustituto del documento final 2012. citeturn19search2turn18search0turn21search3turn27search0turn27search1turn27search3turn27search4turn17search5turn25search0

**`diagnostic_criteria.json`**

```json
{
  "schema_version": "1.0.0",
  "criteria": [
    {
      "criterion_id": "CRIT-DM-ADA-2026",
      "condition_id": "DM",
      "version": "2026.1",
      "population": "NONPREGNANT_ADULT",
      "source_ids": ["SRC-ADA-DX-2026"],
      "inputs": [
        "a1c_percent",
        "fasting_plasma_glucose_mg_dl",
        "fasting_hours",
        "ogtt_2h_plasma_glucose_mg_dl",
        "ogtt_glucose_load_g",
        "random_plasma_glucose_mg_dl",
        "classic_hyperglycemia_symptoms",
        "hyperglycemic_crisis",
        "assay_quality"
      ],
      "logic": {
        "qualifying_paths": [
          {
            "id": "A1C",
            "all_of": [
              {"field": "a1c_percent", "op": ">=", "value": 6.5},
              {"field": "assay_quality.a1c_valid", "op": "==", "value": true}
            ]
          },
          {
            "id": "FPG",
            "all_of": [
              {"field": "fasting_plasma_glucose_mg_dl", "op": ">=", "value": 126},
              {"field": "fasting_hours", "op": ">=", "value": 8}
            ]
          },
          {
            "id": "OGTT",
            "all_of": [
              {"field": "ogtt_2h_plasma_glucose_mg_dl", "op": ">=", "value": 200},
              {"field": "ogtt_glucose_load_g", "op": "==", "value": 75}
            ]
          },
          {
            "id": "RANDOM_SYMPTOMATIC",
            "all_of": [
              {"field": "random_plasma_glucose_mg_dl", "op": ">=", "value": 200},
              {
                "any_of": [
                  {"field": "classic_hyperglycemia_symptoms", "op": "==", "value": true},
                  {"field": "hyperglycemic_crisis", "op": "==", "value": true}
                ]
              }
            ]
          }
        ]
      },
      "confirmation": {
        "RANDOM_SYMPTOMATIC": "NOT_REQUIRED",
        "other_paths": "TWO_ABNORMAL_RESULTS_REQUIRED_IF_NO_UNEQUIVOCAL_HYPERGLYCEMIA",
        "discordant_tests": "REPEAT_TEST_ABOVE_DIAGNOSTIC_CUTPOINT"
      },
      "measurement_quality": {
        "glucose_sample": "VENOUS_PLASMA_FOR_DIAGNOSTIC_THRESHOLDS",
        "a1c": "NGSP_CERTIFIED_DCCT_STANDARDIZED_OR_VALID_DIAGNOSTIC_METHOD",
        "cgm": "NOT_DIAGNOSTIC"
      },
      "space_applicability": "REQUIRES_SPACE_SPECIFIC_VALIDATION"
    },
    {
      "criterion_id": "CRIT-DKA-2024",
      "condition_id": "DKA",
      "version": "2024.1",
      "population": "ADULT",
      "source_ids": ["SRC-DKA-2024"],
      "logic": {
        "all_of": [
          {
            "any_of": [
              {"field": "known_diabetes", "op": "==", "value": true},
              {"field": "plasma_glucose_mg_dl", "op": ">=", "value": 200}
            ]
          },
          {
            "any_of": [
              {"field": "beta_hydroxybutyrate_mmol_l", "op": ">=", "value": 3.0},
              {"field": "urine_ketones_plus", "op": ">=", "value": 2}
            ]
          },
          {
            "any_of": [
              {"field": "venous_pH", "op": "<", "value": 7.3},
              {"field": "bicarbonate_mmol_l", "op": "<", "value": 18}
            ]
          }
        ]
      },
      "required_components": ["DIABETES_OR_HYPERGLYCEMIA", "KETOSIS", "ACIDOSIS"],
      "preferred_ketone_test": "BETA_HYDROXYBUTYRATE",
      "anion_gap_primary_diagnostic_criterion": false,
      "resolution": {
        "all_of": [
          {"field": "beta_hydroxybutyrate_mmol_l", "op": "<", "value": 0.6},
          {
            "any_of": [
              {"field": "venous_pH", "op": ">=", "value": 7.3},
              {"field": "bicarbonate_mmol_l", "op": ">=", "value": 18}
            ]
          }
        ]
      },
      "space_applicability": "REQUIRES_SPACE_SPECIFIC_VALIDATION"
    },
    {
      "criterion_id": "CRIT-OH-AHA-2024",
      "condition_id": "ORTHOSTATIC_HYPOTENSION",
      "version": "2024.1",
      "population": "ADULT",
      "source_ids": ["SRC-AHA-OH-2024"],
      "context": {
        "requires_gravity_supporting_upright_transition": true,
        "standing_window_minutes": 3
      },
      "logic": {
        "any_of": [
          {"derived_field": "delta_sbp_mm_hg", "op": "<=", "value": -20},
          {"derived_field": "delta_dbp_mm_hg", "op": "<=", "value": -10}
        ]
      },
      "measurement_quality": {
        "baseline_and_upright_bp_required": true,
        "time_since_upright_required": true,
        "sustained_reduction_required": true
      },
      "etiology_confirmed_by_criterion": false,
      "space_applicability": "CONTEXT_DEPENDENT"
    },
    {
      "criterion_id": "CRIT-POTS-HRS-NIH",
      "condition_id": "POTS",
      "version": "2015-2021.1",
      "population": "ADULT",
      "source_ids": ["SRC-HRS-POTS-2015", "SRC-NIH-POTS-2021"],
      "logic": {
        "all_of": [
          {"derived_field": "sustained_delta_hr_bpm", "op": ">=", "value": 30},
          {"field": "upright_window_minutes", "op": "<=", "value": 10},
          {"field": "orthostatic_hypotension_present", "op": "==", "value": false},
          {"field": "orthostatic_symptoms_frequent", "op": "==", "value": true},
          {"field": "symptoms_improve_supine", "op": "==", "value": true},
          {"field": "symptom_duration_months", "op": ">=", "value": 3},
          {"field": "alternative_cause_present", "op": "==", "value": false}
        ]
      },
      "alternative_causes": [
        "DEHYDRATION",
        "RECENT_BLOOD_LOSS",
        "ANEMIA",
        "FEVER",
        "INFECTION",
        "PAIN",
        "HYPERTHYROIDISM",
        "PHEOCHROMOCYTOMA",
        "CARDIOACTIVE_OR_SYMPATHOMIMETIC_DRUG",
        "SEVERE_DECONDITIONING"
      ],
      "space_applicability": "REQUIRES_SPACE_SPECIFIC_VALIDATION"
    },
    {
      "criterion_id": "CRIT-AKI-KDIGO-2012",
      "condition_id": "AKI",
      "version": "2012.final",
      "population": "ADULT",
      "source_ids": ["SRC-KDIGO-AKI-2012"],
      "logic": {
        "any_of": [
          {
            "derived_field": "serum_creatinine_delta_mg_dl_48h",
            "op": ">=",
            "value": 0.3
          },
          {
            "derived_field": "serum_creatinine_ratio_to_baseline_7d",
            "op": ">=",
            "value": 1.5
          },
          {
            "all_of": [
              {"field": "urine_output_ml_kg_h", "op": "<", "value": 0.5},
              {"field": "urine_output_duration_h", "op": ">=", "value": 6}
            ]
          }
        ]
      },
      "staging": [
        {
          "stage": 1,
          "creatinine": "1.5-1.9x baseline OR increase >=0.3 mg/dL",
          "urine_output": "<0.5 mL/kg/h for 6-12 h"
        },
        {
          "stage": 2,
          "creatinine": "2.0-2.9x baseline",
          "urine_output": "<0.5 mL/kg/h for >=12 h"
        },
        {
          "stage": 3,
          "creatinine": ">=3.0x baseline OR >=4.0 mg/dL OR RRT initiated",
          "urine_output": "<0.3 mL/kg/h for >=24 h OR anuria >=12 h"
        }
      ],
      "missing_baseline_policy": "DO_NOT_INVENT_BASELINE",
      "space_applicability": "REQUIRES_SPACE_SPECIFIC_VALIDATION"
    },
    {
      "criterion_id": "CRIT-ANAPH-WAO-2020",
      "condition_id": "ANAPHYLAXIS",
      "version": "2020.1",
      "population": "ADULT",
      "source_ids": ["SRC-WAO-ANAPH-2020"],
      "logic": {
        "any_of": [
          {
            "id": "WAO_PATH_1",
            "all_of": [
              {"field": "acute_onset_minutes_to_hours", "op": "==", "value": true},
              {"field": "skin_or_mucosal_involvement", "op": "==", "value": true},
              {
                "any_of": [
                  {"field": "respiratory_compromise", "op": "==", "value": true},
                  {"field": "reduced_bp_or_end_organ_symptoms", "op": "==", "value": true},
                  {"field": "severe_gi_symptoms", "op": "==", "value": true}
                ]
              }
            ]
          },
          {
            "id": "WAO_PATH_2",
            "all_of": [
              {"field": "acute_onset_minutes_to_hours", "op": "==", "value": true},
              {"field": "known_or_highly_probable_allergen", "op": "==", "value": true},
              {
                "any_of": [
                  {"field": "adult_sbp_mm_hg", "op": "<", "value": 90},
                  {"derived_field": "sbp_drop_percent", "op": ">", "value": 30},
                  {"field": "bronchospasm", "op": "==", "value": true},
                  {"field": "laryngeal_involvement", "op": "==", "value": true}
                ]
              }
            ]
          }
        ]
      },
      "confirmation": "NO_LAB_CONFIRMATION_REQUIRED_BEFORE_EMERGENCY_MANAGEMENT",
      "space_applicability": "APPLICABLE_WITH_LIMITATIONS"
    }
  ]
}
```

Los umbrales y condiciones de este archivo proceden de ADA 2026, el consenso DKA 2024, AHA 2024, HRS/NIH, KDIGO y WAO; ningún umbral espacial alternativo ha sido inventado. citeturn18search0turn21search3turn17search0turn18search3turn27search3turn21search0

**`differential_rules.json`**

```json
{
  "schema_version": "1.0.0",
  "ranking": [
    "TIME_CRITICAL_CRITERIA_MET",
    "TIME_CRITICAL_SUSPECTED",
    "CRITERIA_MET",
    "HIGH_PRIORITY_UNRESOLVED",
    "COMPATIBLE",
    "WEAK_SUPPORT",
    "CONTRADICTED",
    "NOT_EVALUABLE"
  ],
  "presentations": [
    {
      "presentation_id": "PRES-DIZZINESS-TACHYCARDIA",
      "triggers": ["DIZZINESS", "TACHYCARDIA"],
      "hypotheses": [
        {
          "id": "ANAPHYLAXIS",
          "support": ["ALLERGEN_EXPOSURE", "BRONCHOSPASM", "LARYNGEAL", "HYPOTENSION", "SKIN_MUCOSAL"],
          "test_ids": ["TEST-BP", "TEST-ANAPH-CLINICAL"],
          "time_critical": true
        },
        {
          "id": "ORTHOSTATIC_HYPOTENSION",
          "support": ["POSTURAL_TRIGGER", "BP_DROP"],
          "test_ids": ["TEST-ORTHOSTATIC-BP-HR"],
          "time_critical": false
        },
        {
          "id": "POTS",
          "support": ["POSTURAL_TRIGGER", "CHRONIC_ORTHOSTATIC_SYMPTOMS", "HR_RISE"],
          "contradictions": ["ORTHOSTATIC_HYPOTENSION", "DEHYDRATION", "ANEMIA", "INFECTION", "SEVERE_DECONDITIONING"],
          "test_ids": ["TEST-ORTHOSTATIC-BP-HR", "TEST-POTS-EXCLUSIONS"],
          "time_critical": false
        },
        {
          "id": "DKA",
          "support": ["HYPERGLYCEMIA_OR_DIABETES", "NAUSEA", "DEHYDRATION"],
          "test_ids": ["TEST-PLASMA-GLUCOSE", "TEST-BETA-OHB", "TEST-VENOUS-PH-BICARB"],
          "time_critical": true
        },
        {
          "id": "EXTERNAL_ARRHYTHMIA_PATHWAY",
          "support": ["NON_POSTURAL_TACHYCARDIA", "IRREGULAR_PULSE", "PALPITATIONS"],
          "test_ids": ["TEST-ECG"],
          "time_critical": true,
          "criteria_implemented_here": false
        }
      ]
    },
    {
      "presentation_id": "PRES-HYPOTENSION-WEAKNESS",
      "triggers": ["HYPOTENSION", "WEAKNESS"],
      "hypotheses": [
        {"id": "ANAPHYLAXIS", "time_critical": true},
        {"id": "ORTHOSTATIC_HYPOTENSION", "time_critical": false},
        {"id": "HYPOVOLEMIA", "time_critical": true},
        {"id": "DKA", "time_critical": true},
        {"id": "EXTERNAL_BLEEDING_PATHWAY", "time_critical": true, "criteria_implemented_here": false}
      ]
    },
    {
      "presentation_id": "PRES-HYPERGLYCEMIA-NAUSEA",
      "triggers": ["HYPERGLYCEMIA", "NAUSEA"],
      "hypotheses": [
        {"id": "DKA", "time_critical": true, "test_ids": ["TEST-BETA-OHB", "TEST-VENOUS-PH-BICARB"]},
        {"id": "DIABETES", "time_critical": false, "test_ids": ["TEST-PLASMA-GLUCOSE"]},
        {"id": "STRESS_HYPERGLYCEMIA_OR_OTHER", "time_critical": false, "criteria_implemented_here": false}
      ]
    },
    {
      "presentation_id": "PRES-TACHYCARDIA-DYSPNEA",
      "triggers": ["TACHYCARDIA", "DYSPNEA"],
      "hypotheses": [
        {"id": "ANAPHYLAXIS", "time_critical": true},
        {"id": "DKA", "time_critical": true},
        {"id": "POTS", "time_critical": false},
        {"id": "EXTERNAL_ARRHYTHMIA_PATHWAY", "time_critical": true, "criteria_implemented_here": false},
        {"id": "EXTERNAL_PULMONARY_PATHWAY", "time_critical": true, "criteria_implemented_here": false}
      ]
    },
    {
      "presentation_id": "PRES-OLIGURIA-CREATININE",
      "triggers": ["OLIGURIA_OR_ANURIA", "CREATININE_CHANGE"],
      "hypotheses": [
        {"id": "AKI", "time_critical": true, "test_ids": ["TEST-SERUM-CREATININE", "TEST-URINE-OUTPUT"]},
        {"id": "HYPOVOLEMIC_PRERENAL_STATE", "time_critical": true},
        {"id": "EXTERNAL_POSTRENAL_OBSTRUCTION", "time_critical": true, "criteria_implemented_here": false},
        {"id": "EXTERNAL_INTRINSIC_RENAL_PATHWAY", "time_critical": true, "criteria_implemented_here": false}
      ]
    },
    {
      "presentation_id": "PRES-ALLERGEN-RESPIRATORY",
      "triggers": ["ALLERGEN_EXPOSURE", "RESPIRATORY_SYMPTOMS"],
      "hypotheses": [
        {"id": "ANAPHYLAXIS", "time_critical": true, "test_ids": ["TEST-ANAPH-CLINICAL", "TEST-BP"]},
        {"id": "NON_ANAPHYLACTIC_ALLERGIC_REACTION", "time_critical": false, "criteria_implemented_here": false},
        {"id": "EXTERNAL_RESPIRATORY_PATHWAY", "time_critical": true, "criteria_implemented_here": false}
      ]
    }
  ]
}
```

La parte que ordena estas hipótesis es una **heurística de software explícita**, no una escala clínica validada. Las condiciones internas utilizan los criterios verificados; las rutas externas deben permanecer sin implementar hasta que sus propias especificaciones hayan sido verificadas. citeturn18search3turn21search0turn27search3

**`diagnostic_tests.json`**

```json
{
  "schema_version": "1.0.0",
  "tests": [
    {
      "test_id": "TEST-PLASMA-GLUCOSE",
      "measure": "plasma_glucose",
      "canonical_unit": "mg/dL",
      "alternatives": ["mmol/L"],
      "conversion": "mmol/L * 18 ≈ mg/dL",
      "diagnostic_use": ["DM", "DKA"],
      "quality": ["sample_type_recorded", "fasting_status_when_required"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-A1C",
      "measure": "A1C",
      "canonical_unit": "%",
      "diagnostic_use": ["DM"],
      "quality": ["validated_diagnostic_method", "assay_interference_assessed_when_discordant"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-OGTT-75G",
      "measure": "2h_plasma_glucose",
      "canonical_unit": "mg/dL",
      "diagnostic_use": ["DM"],
      "quality": ["75_g_glucose_load", "2h_timing_valid"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-BETA-OHB",
      "measure": "beta_hydroxybutyrate",
      "canonical_unit": "mmol/L",
      "diagnostic_use": ["DKA"],
      "quality": ["device_or_lab_valid", "operator_training"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-VENOUS-PH-BICARB",
      "measure": ["venous_pH", "bicarbonate"],
      "canonical_unit": ["pH", "mmol/L"],
      "diagnostic_use": ["DKA"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-ORTHOSTATIC-BP-HR",
      "measure": ["blood_pressure", "heart_rate"],
      "diagnostic_use": ["ORTHOSTATIC_HYPOTENSION", "POTS"],
      "quality": [
        "gravity_context_recorded",
        "baseline_position_recorded",
        "upright_time_recorded",
        "valid_BP_device",
        "valid_HR_device"
      ],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-POTS-EXCLUSIONS",
      "measure": "clinical_exclusion_set",
      "diagnostic_use": ["POTS"],
      "required_review": [
        "dehydration",
        "recent_blood_loss",
        "anemia",
        "fever",
        "infection",
        "pain",
        "hyperthyroidism",
        "medications",
        "severe_deconditioning"
      ],
      "missing_behavior": "UNRESOLVED_EXCLUSION"
    },
    {
      "test_id": "TEST-SERUM-CREATININE",
      "measure": "serum_creatinine",
      "canonical_unit": "mg/dL",
      "alternatives": ["micromol/L"],
      "diagnostic_use": ["AKI"],
      "quality": ["timestamp", "comparable_assay_context"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-URINE-OUTPUT",
      "measure": "urine_output",
      "canonical_unit": "mL/kg/h",
      "diagnostic_use": ["AKI"],
      "quality": ["body_mass_known", "collection_window_known", "collection_reliable"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-ANAPH-CLINICAL",
      "measure": [
        "skin_mucosal",
        "respiratory",
        "laryngeal",
        "GI",
        "allergen_context"
      ],
      "diagnostic_use": ["ANAPHYLAXIS"],
      "missing_behavior": "PARTIAL_CLINICAL_INFORMATION"
    },
    {
      "test_id": "TEST-BP",
      "measure": "blood_pressure",
      "canonical_unit": "mmHg",
      "diagnostic_use": ["ANAPHYLAXIS", "ORTHOSTATIC_HYPOTENSION"],
      "quality": ["device_valid", "timestamp", "position"],
      "missing_behavior": "UNKNOWN"
    },
    {
      "test_id": "TEST-ECG",
      "measure": "electrocardiogram",
      "diagnostic_use": ["EXTERNAL_ARRHYTHMIA_PATHWAY"],
      "quality": ["signal_quality"],
      "criteria_implemented_in_this_release": false,
      "missing_behavior": "EXTERNAL_PATHWAY_UNRESOLVED"
    }
  ]
}
```

ADA especifica plasma y A1C apropiadamente validados para diagnóstico y no acepta CGM como sustituto diagnóstico; el consenso DKA respalda β-hidroxibutirato y pH/bicarbonato; KDIGO exige temporalidad para creatinina y diuresis; y las rutas ortostáticas dependen de contexto postural/gravitatorio. citeturn18search0turn21search1turn24search0turn27search3turn17search0

**`treatment_protocols.json`**

```json
{
  "schema_version": "1.0.0",
  "default_policy": {
    "mission_approved": false,
    "automatic_execution": false
  },
  "protocols": [
    {
      "protocol_id": "PROT-DM-CONFIRMATION",
      "condition_id": "DM",
      "source_ids": ["SRC-ADA-DX-2026"],
      "trigger": ["SUSPECTED", "CRITERIA_MET"],
      "steps": [
        "VERIFY_DIAGNOSTIC_SAMPLE_AND_METHOD",
        "APPLY_CONFIRMATION_RULE_IF_REQUIRED",
        "INVESTIGATE_MAJOR_A1C_GLUCOSE_DISCORDANCE",
        "PERSIST_RESULT_AND_SOURCE_VERSION"
      ],
      "medication_actions": [],
      "mission_approved": false,
      "execution": "DECISION_SUPPORT_ONLY"
    },
    {
      "protocol_id": "PROT-DKA-ADULT-2024",
      "condition_id": "DKA",
      "source_ids": ["SRC-DKA-2024"],
      "trigger": ["CRITERIA_MET"],
      "urgency": "EMERGENCY",
      "required_resources": [
        "validated_glucose_measurement",
        "potassium_measurement",
        "electrolytes",
        "beta_hydroxybutyrate",
        "venous_pH_or_bicarbonate",
        "IV_access_capability",
        "IV_fluid_capability",
        "insulin_inventory",
        "continuous_or_frequent_monitoring"
      ],
      "safety_gates": [
        {
          "if": "potassium_mmol_l < 3.5",
          "action": "HOLD_INSULIN_UNTIL_POTASSIUM_ABOVE_3_5"
        }
      ],
      "therapy": [
        {
          "action": "IV_SHORT_ACTING_INSULIN",
          "rate": "0.1 U/kg/h",
          "requires_mission_authorization": true
        },
        {
          "if": "glucose_mg_dl < 250",
          "action": "ADD_5_TO_10_PERCENT_DEXTROSE_AND_REDUCE_INSULIN",
          "new_rate": "0.05 U/kg/h",
          "requires_mission_authorization": true
        }
      ],
      "monitoring": [
        "glucose_every_1_to_2_h",
        "electrolytes_creatinine_phosphate_beta_OHB_pH_every_4_h",
        "potassium_2_h_after_insulin_then_every_4_h"
      ],
      "resolution": "beta_OHB <0.6 AND (pH >=7.3 OR bicarbonate >=18)",
      "mission_approved": false,
      "automatic_execution": false
    },
    {
      "protocol_id": "PROT-OH-POTS-INITIAL",
      "condition_id": "ORTHOSTATIC_SYNDROME",
      "source_ids": ["SRC-AHA-OH-2024", "SRC-HRS-POTS-2015", "SRC-NIH-POTS-2021"],
      "steps": [
        "CHARACTERIZE_TRIGGER_AND_PATTERN",
        "REVIEW_AGGRAVATING_MEDICATIONS",
        "ASSESS_DEHYDRATION_AND_VOLUME_STATUS",
        "ASSESS_ALTERNATIVE_CAUSES",
        "CONSIDER_NONPHARMACOLOGIC_COUNTERMEASURES",
        "REASSESS"
      ],
      "pharmacologic_automation": false,
      "mission_approved": false
    },
    {
      "protocol_id": "PROT-AKI-INITIAL",
      "condition_id": "AKI",
      "source_ids": ["SRC-KDIGO-AKI-2012"],
      "trigger": ["CRITERIA_MET"],
      "steps": [
        "DETERMINE_CAUSE_WHEN_POSSIBLE",
        "LOOK_FOR_REVERSIBLE_CAUSES",
        "REVIEW_NEPHROTOXIC_EXPOSURES",
        "MONITOR_SERUM_CREATININE",
        "MONITOR_URINE_OUTPUT",
        "STAGE_AKI",
        "MANAGE_ACCORDING_TO_CAUSE_AND_STAGE"
      ],
      "rules": [
        "ISOTONIC_CRYSTALLOIDS_PREFERRED_TO_COLLOIDS_FOR_INTRAVASCULAR_EXPANSION_WHEN_APPROPRIATE_AND_NO_HEMORRHAGIC_SHOCK",
        "DO_NOT_USE_DIURETICS_TO_PREVENT_AKI",
        "DO_NOT_USE_DIURETICS_TO_TREAT_AKI_EXCEPT_VOLUME_OVERLOAD"
      ],
      "mission_approved": false,
      "automatic_execution": false
    },
    {
      "protocol_id": "PROT-ANAPH-IM-EPI",
      "condition_id": "ANAPHYLAXIS",
      "source_ids": ["SRC-WAO-ANAPH-2020"],
      "trigger": ["CRITERIA_MET", "TIME_CRITICAL_SUSPECTED"],
      "urgency": "EMERGENCY",
      "therapy": [
        {
          "action": "EPINEPHRINE_IM",
          "dose": "0.01 mg/kg",
          "maximum_dose": "0.5 mg",
          "repeat_if_refractory": "every 5-15 min",
          "preferred_adult_site": "intramuscular",
          "requires_mission_authorization": true
        }
      ],
      "additional_actions": [
        "POSITION_ACCORDING_TO_CLINICAL_STATE",
        "OXYGEN_IF_RESPIRATORY_DISTRESS_OR_FURTHER_EPINEPHRINE_REQUIRED",
        "IV_CRYSTALLOIDS_IF_CARDIOVASCULAR_INSTABILITY"
      ],
      "initial_IV_epinephrine_bolus": "NOT_RECOMMENDED",
      "mission_approved": false,
      "automatic_execution": false
    },
    {
      "protocol_id": "PROT-DIZZINESS-TACHY-TRIAGE",
      "condition_id": "DIZZINESS_TACHYCARDIA_PRESENTATION",
      "source_ids": [
        "SRC-AHA-OH-2024",
        "SRC-HRS-POTS-2015",
        "SRC-DKA-2024",
        "SRC-WAO-ANAPH-2020"
      ],
      "steps": [
        "ASSESS_IMMEDIATE_INSTABILITY",
        "ASSESS_ANAPHYLAXIS",
        "ASSESS_DKA_IF_METABOLIC_FEATURES",
        "ASSESS_ORTHOSTATIC_RELATION_IF_CONTEXT_APPLICABLE",
        "ASSESS_POTS_EXCLUSIONS",
        "REQUEST_ECG_FOR_NONPOSTURAL_OR_IRREGULAR_TACHYCARDIA",
        "ROUTE_EXTERNAL_TIME_CRITICAL_CONDITIONS_TO_SEPARATE_PATHWAYS"
      ],
      "medication_actions": [],
      "automatic_execution": false
    }
  ]
}
```

Los regímenes de DKA y anafilaxia aquí representados reproducen datos explícitos de las fuentes terrestres y permanecen bloqueados por defecto para misión. La epinefrina IM y la insulinoterapia DKA tienen requisitos de monitorización muy distintos, por lo que nunca deben reducirse a una simple tabla «fármaco–dosis». citeturn24search0turn24search1

**`contraindications.json`**

```json
{
  "schema_version": "1.0.0",
  "rules": [
    {
      "rule_id": "BLOCK-DKA-INSULIN-LOW-K",
      "protocol_id": "PROT-DKA-ADULT-2024",
      "source_ids": ["SRC-DKA-2024"],
      "condition": "potassium_mmol_l < 3.5",
      "effect": "HOLD_INSULIN",
      "reason": "risk_of_worsening_hypokalemia"
    },
    {
      "rule_id": "BLOCK-DKA-MISSING-K",
      "protocol_id": "PROT-DKA-ADULT-2024",
      "condition": "potassium_unknown",
      "effect": "BLOCKED_MISSING_SAFETY_DATA",
      "reason": "potassium_required_for_safe_protocol_state_machine"
    },
    {
      "rule_id": "BLOCK-DKA-NO-MONITOR",
      "protocol_id": "PROT-DKA-ADULT-2024",
      "condition": "required_monitoring_unavailable",
      "effect": "BLOCKED_RESOURCE"
    },
    {
      "rule_id": "ANAPH-IM-EPI-NO-ABSOLUTE-CLINICAL-CONTRAINDICATION",
      "protocol_id": "PROT-ANAPH-IM-EPI",
      "source_ids": ["SRC-WAO-ANAPH-2020"],
      "condition": "anaphylaxis_emergency",
      "effect": "DO_NOT_CREATE_HARD_CLINICAL_CONTRAINDICATION_TO_IM_EPINEPHRINE_FROM_UNSOURCED_RULES"
    },
    {
      "rule_id": "BLOCK-ANAPH-WRONG-ROUTE",
      "protocol_id": "PROT-ANAPH-IM-EPI",
      "source_ids": ["SRC-WAO-ANAPH-2020"],
      "condition": "initial_epinephrine_route == IV_BOLUS",
      "effect": "BLOCK"
    },
    {
      "rule_id": "BLOCK-ANAPH-NO-VERIFIED-DRUG",
      "protocol_id": "PROT-ANAPH-IM-EPI",
      "condition": "epinephrine_inventory_or_concentration_unverified",
      "effect": "BLOCKED_RESOURCE"
    },
    {
      "rule_id": "BLOCK-POTS-DEHYDRATION",
      "criterion_id": "CRIT-POTS-HRS-NIH",
      "source_ids": ["SRC-NIH-POTS-2021"],
      "condition": "dehydration_present",
      "effect": "POTS_CRITERIA_NOT_MET"
    },
    {
      "rule_id": "BLOCK-POTS-OH",
      "criterion_id": "CRIT-POTS-HRS-NIH",
      "source_ids": ["SRC-HRS-POTS-2015"],
      "condition": "orthostatic_hypotension_present",
      "effect": "POTS_CRITERIA_NOT_MET"
    },
    {
      "rule_id": "BLOCK-OH-FREE-MICROGRAVITY",
      "criterion_id": "CRIT-OH-AHA-2024",
      "condition": "gravity_context == FREE_MICROGRAVITY",
      "effect": "NOT_APPLICABLE"
    },
    {
      "rule_id": "BLOCK-MISSION-NOT-AUTHORIZED",
      "protocol_id": "*",
      "condition": "mission_authorization != AUTHORIZED",
      "effect": "BLOCKED_AUTHORIZATION"
    }
  ]
}
```

WAO especifica que no existe una contraindicación absoluta para epinefrina IM en anafilaxia, mientras que el consenso DKA exige retrasar la insulina cuando el potasio es <3,5 mmol/L. Las restantes barreras relativas a autorización, inventario y microgravedad son controles de VIGILE. citeturn17search4turn24search0

**`space_applicability.json`**

```json
{
  "schema_version": "1.0.0",
  "classifications": [
    {
      "condition_id": "DM",
      "classification": "REQUIRES_SPACE_SPECIFIC_VALIDATION",
      "terrestrial_rule_preserved": true,
      "threshold_adjustment": "NONE",
      "reason": "No verified space-specific diagnostic thresholds identified."
    },
    {
      "condition_id": "DKA",
      "classification": "REQUIRES_SPACE_SPECIFIC_VALIDATION",
      "terrestrial_rule_preserved": true,
      "threshold_adjustment": "NONE",
      "reason": "Diagnostic and treatment criteria are terrestrial; mission resources and physiology require validation."
    },
    {
      "condition_id": "ORTHOSTATIC_HYPOTENSION",
      "classification": "CONTEXT_DEPENDENT",
      "contexts": {
        "FREE_MICROGRAVITY": "NOT_APPLICABLE",
        "EARTH_GRAVITY": "DIRECTLY_APPLICABLE_WITH_STANDARD_CLINICAL_LIMITATIONS",
        "POST_SPACEFLIGHT_GRAVITY_TRANSITION": "APPLICABLE_WITH_LIMITATIONS",
        "PARTIAL_GRAVITY": "REQUIRES_SPACE_SPECIFIC_VALIDATION"
      },
      "threshold_adjustment": "NONE"
    },
    {
      "condition_id": "POTS",
      "classification": "REQUIRES_SPACE_SPECIFIC_VALIDATION",
      "contexts": {
        "FREE_MICROGRAVITY": "NOT_APPLICABLE_FOR_STANDARD_STANDING_TEST",
        "POST_SPACEFLIGHT": "APPLICABLE_WITH_LIMITATIONS"
      },
      "special_confounder": "SPACEFLIGHT_DECONDITIONING",
      "threshold_adjustment": "NONE"
    },
    {
      "condition_id": "AKI",
      "classification": "REQUIRES_SPACE_SPECIFIC_VALIDATION",
      "terrestrial_rule_preserved": true,
      "threshold_adjustment": "NONE",
      "reason": "Spaceflight alters renal physiology, fluids and body composition; no replacement KDIGO thresholds verified."
    },
    {
      "condition_id": "ANAPHYLAXIS",
      "classification": "APPLICABLE_WITH_LIMITATIONS",
      "terrestrial_rule_preserved": true,
      "threshold_adjustment": "NONE",
      "limitations": [
        "positioning_in_microgravity",
        "drug_inventory",
        "route_execution",
        "monitoring_resources"
      ]
    },
    {
      "condition_id": "DIZZINESS_TACHYCARDIA_PRESENTATION",
      "classification": "CONTEXT_DEPENDENT",
      "reason": "Orthostatic branches depend on gravity; metabolic/allergic branches do not use standing criteria."
    }
  ]
}
```

No se ha introducido ningún «umbral espacial» nuevo. La evidencia disponible justifica registrar incertidumbre y contexto, no alterar arbitrariamente ADA, KDIGO, AHA, HRS o WAO. citeturn24search3turn25search0turn19search0

**`synthetic_cases.json`**

Los 30 casos siguientes son **casos de conformidad del software**, no pacientes ni evidencia de validación clínica.

```json
{
  "schema_version": "1.0.0",
  "cases": [
    {
      "id": "DM-01",
      "route": "DM_DKA",
      "inputs": {
        "fpg": [
          {"value": 132, "unit": "mg/dL", "fasting_h": 9, "valid": true},
          {"value": 130, "unit": "mg/dL", "fasting_h": 10, "valid": true}
        ],
        "classic_symptoms": false
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "ROUTINE",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": [],
      "source_ids": ["SRC-ADA-DX-2026"]
    },
    {
      "id": "DM-02",
      "route": "DM_DKA",
      "inputs": {
        "fpg": [{"value": 130, "unit": "mg/dL", "fasting_h": 8, "valid": true}],
        "classic_symptoms": false
      },
      "expected": {
        "diagnostic_status": "SUSPECTED",
        "urgency": "ROUTINE",
        "confirmation_status": "REQUIRED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["REPEAT_VALID_DIAGNOSTIC_TEST"],
      "source_ids": ["SRC-ADA-DX-2026"]
    },
    {
      "id": "DM-03",
      "route": "DM_DKA",
      "inputs": {
        "random_plasma_glucose": {"value": 220, "unit": "mg/dL", "valid": true},
        "classic_symptoms": true
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "PROMPT",
        "confirmation_status": "NOT_REQUIRED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["ASSESS_HYPERGLYCEMIC_CRISIS_IF_INDICATED"],
      "source_ids": ["SRC-ADA-DX-2026"]
    },
    {
      "id": "DM-04",
      "route": "DM_DKA",
      "inputs": {
        "cgm_interstitial_glucose": {"value": 245, "unit": "mg/dL"},
        "diagnostic_plasma_glucose": null
      },
      "expected": {
        "diagnostic_status": "INSUFFICIENT_DATA",
        "urgency": "PROMPT",
        "confirmation_status": "REQUIRED",
        "protocol_status": "BLOCKED_MISSING_DATA",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["TEST-PLASMA-GLUCOSE"],
      "source_ids": ["SRC-ADA-DX-2026"]
    },
    {
      "id": "DM-05",
      "route": "DM_DKA",
      "inputs": {
        "known_diabetes": true,
        "plasma_glucose_mg_dl": 180,
        "beta_hydroxybutyrate_mmol_l": 4.2,
        "venous_pH": 7.22
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "EMERGENCY",
        "confirmation_status": "SATISFIED",
        "protocol_status": "BLOCKED_AUTHORIZATION",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["POTASSIUM", "ELECTROLYTES", "CREATININE"],
      "source_ids": ["SRC-DKA-2024"]
    },
    {
      "id": "DM-06",
      "route": "DM_DKA",
      "inputs": {
        "plasma_glucose_mg_dl": 310,
        "beta_hydroxybutyrate_mmol_l": 4.0,
        "venous_pH": null,
        "bicarbonate_mmol_l": null
      },
      "expected": {
        "diagnostic_status": "SUSPECTED",
        "urgency": "URGENT",
        "confirmation_status": "REQUIRED",
        "protocol_status": "BLOCKED_MISSING_DATA",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["TEST-VENOUS-PH-BICARB"],
      "source_ids": ["SRC-DKA-2024"]
    },

    {
      "id": "ORTHO-01",
      "route": "OH_POTS",
      "inputs": {
        "gravity": "EARTH",
        "baseline_bp": "125/80",
        "bp_at_2min": "100/68"
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "PROMPT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "expected_condition": "ORTHOSTATIC_HYPOTENSION",
      "source_ids": ["SRC-AHA-OH-2024"]
    },
    {
      "id": "ORTHO-02",
      "route": "OH_POTS",
      "inputs": {
        "gravity": "EARTH",
        "baseline_sbp": 120,
        "standing_sbp": 100,
        "standing_time_min": 3
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "PROMPT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "boundary_test": true,
      "source_ids": ["SRC-AHA-OH-2024"]
    },
    {
      "id": "ORTHO-03",
      "route": "OH_POTS",
      "inputs": {
        "baseline_bp": null,
        "standing_bp": "90/60",
        "standing_time_min": 2
      },
      "expected": {
        "diagnostic_status": "INSUFFICIENT_DATA",
        "urgency": "PROMPT",
        "confirmation_status": "REQUIRED",
        "protocol_status": "BLOCKED_MISSING_DATA",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["VALID_BASELINE_AND_UPRIGHT_BP"],
      "source_ids": ["SRC-AHA-OH-2024"]
    },
    {
      "id": "ORTHO-04",
      "route": "OH_POTS",
      "inputs": {
        "adult": true,
        "delta_hr_bpm": 35,
        "within_10_min": true,
        "orthostatic_hypotension": false,
        "orthostatic_symptoms": true,
        "improve_supine": true,
        "duration_months": 5,
        "alternative_cause": false
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "ROUTINE",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "expected_condition": "POTS",
      "source_ids": ["SRC-HRS-POTS-2015", "SRC-NIH-POTS-2021"]
    },
    {
      "id": "ORTHO-05",
      "route": "OH_POTS",
      "inputs": {
        "delta_hr_bpm": 40,
        "orthostatic_hypotension": false,
        "orthostatic_symptoms": true,
        "duration_months": 4,
        "dehydration": true
      },
      "expected": {
        "diagnostic_status": "CRITERIA_NOT_MET",
        "urgency": "PROMPT",
        "confirmation_status": "NOT_APPLICABLE",
        "protocol_status": "NOT_INDICATED",
        "treatment_status": "NOT_STARTED"
      },
      "expected_condition": "POTS",
      "differential": ["DEHYDRATION_OR_HYPOVOLEMIA"],
      "source_ids": ["SRC-NIH-POTS-2021"]
    },
    {
      "id": "ORTHO-06",
      "route": "OH_POTS",
      "inputs": {
        "gravity": "FREE_MICROGRAVITY",
        "requested_test": "STANDARD_STANDING_ORTHOSTATIC_TEST"
      },
      "expected": {
        "diagnostic_status": "NOT_APPLICABLE",
        "urgency": "ROUTINE",
        "confirmation_status": "NOT_APPLICABLE",
        "protocol_status": "NOT_INDICATED",
        "treatment_status": "NOT_STARTED"
      },
      "source_ids": ["SRC-NASA-OI"]
    },

    {
      "id": "AKI-01",
      "route": "AKI",
      "inputs": {
        "creatinine_baseline_mg_dl": 0.9,
        "creatinine_current_mg_dl": 1.3,
        "elapsed_h": 40
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "URGENT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "stage": 1,
      "source_ids": ["SRC-KDIGO-AKI-2012"]
    },
    {
      "id": "AKI-02",
      "route": "AKI",
      "inputs": {
        "creatinine_baseline_mg_dl": 1.0,
        "creatinine_current_mg_dl": 1.6,
        "elapsed_days": 5
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "URGENT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "stage": 1,
      "source_ids": ["SRC-KDIGO-AKI-2012"]
    },
    {
      "id": "AKI-03",
      "route": "AKI",
      "inputs": {
        "urine_output_ml_kg_h": 0.4,
        "duration_h": 7
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "URGENT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "stage": 1,
      "source_ids": ["SRC-KDIGO-AKI-2012"]
    },
    {
      "id": "AKI-04",
      "route": "AKI",
      "inputs": {
        "creatinine_baseline_mg_dl": 0.8,
        "creatinine_current_mg_dl": 1.84,
        "elapsed_days": 3
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "URGENT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "stage": 2,
      "source_ids": ["SRC-KDIGO-AKI-2012"]
    },
    {
      "id": "AKI-05",
      "route": "AKI",
      "inputs": {
        "creatinine_current_mg_dl": 1.3,
        "baseline": null,
        "prior_creatinines": [],
        "urine_output": null
      },
      "expected": {
        "diagnostic_status": "INSUFFICIENT_DATA",
        "urgency": "PROMPT",
        "confirmation_status": "REQUIRED",
        "protocol_status": "BLOCKED_MISSING_DATA",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["SERIAL_CREATININE", "URINE_OUTPUT"],
      "source_ids": ["SRC-KDIGO-AKI-2012"]
    },
    {
      "id": "AKI-06",
      "route": "AKI",
      "inputs": {
        "gravity": "MICROGRAVITY",
        "creatinine_baseline_mg_dl": 0.7,
        "creatinine_current_mg_dl": 1.05,
        "elapsed_days": 5
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "URGENT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "space_warning": "REQUIRES_SPACE_SPECIFIC_VALIDATION",
      "source_ids": ["SRC-KDIGO-AKI-2012", "SRC-SPACE-KIDNEY-2024"]
    },

    {
      "id": "ANAPH-01",
      "route": "ANAPHYLAXIS",
      "inputs": {
        "acute": true,
        "skin_mucosal": true,
        "bronchospasm": true
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "EMERGENCY",
        "confirmation_status": "NOT_REQUIRED",
        "protocol_status": "BLOCKED_AUTHORIZATION",
        "treatment_status": "NOT_STARTED"
      },
      "source_ids": ["SRC-WAO-ANAPH-2020"]
    },
    {
      "id": "ANAPH-02",
      "route": "ANAPHYLAXIS",
      "inputs": {
        "acute": true,
        "known_allergen": true,
        "skin_mucosal": false,
        "adult_sbp": 82
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "EMERGENCY",
        "confirmation_status": "NOT_REQUIRED",
        "protocol_status": "BLOCKED_AUTHORIZATION",
        "treatment_status": "NOT_STARTED"
      },
      "source_ids": ["SRC-WAO-ANAPH-2020"]
    },
    {
      "id": "ANAPH-03",
      "route": "ANAPHYLAXIS",
      "inputs": {
        "acute": true,
        "probable_allergen": true,
        "repetitive_vomiting": true,
        "skin_mucosal": false,
        "respiratory": false,
        "hypotension": false
      },
      "expected": {
        "diagnostic_status": "SUSPECTED",
        "urgency": "PROMPT",
        "confirmation_status": "PENDING",
        "protocol_status": "NOT_INDICATED",
        "treatment_status": "NOT_STARTED"
      },
      "next_tests": ["REASSESS_SKIN_RESPIRATORY_BP_LARYNGEAL"],
      "source_ids": ["SRC-WAO-ANAPH-2020"]
    },
    {
      "id": "ANAPH-04",
      "route": "ANAPHYLAXIS",
      "inputs": {
        "acute": true,
        "skin_mucosal": true,
        "respiratory": false,
        "hypotension": false,
        "severe_gi": false
      },
      "expected": {
        "diagnostic_status": "CRITERIA_NOT_MET",
        "urgency": "PROMPT",
        "confirmation_status": "NOT_APPLICABLE",
        "protocol_status": "NOT_INDICATED",
        "treatment_status": "NOT_STARTED"
      },
      "differential": ["NON_ANAPHYLACTIC_ALLERGIC_REACTION"],
      "source_ids": ["SRC-WAO-ANAPH-2020"]
    },
    {
      "id": "ANAPH-05",
      "route": "ANAPHYLAXIS",
      "inputs": {
        "acute": true,
        "known_allergen": true,
        "laryngeal_involvement": true,
        "skin_mucosal": false
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "EMERGENCY",
        "confirmation_status": "NOT_REQUIRED",
        "protocol_status": "BLOCKED_AUTHORIZATION",
        "treatment_status": "NOT_STARTED"
      },
      "source_ids": ["SRC-WAO-ANAPH-2020"]
    },
    {
      "id": "ANAPH-06",
      "route": "ANAPHYLAXIS",
      "inputs": {
        "acute": true,
        "known_allergen": true,
        "bronchospasm": true,
        "epinephrine_inventory_verified": false
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "EMERGENCY",
        "confirmation_status": "NOT_REQUIRED",
        "protocol_status": "BLOCKED_RESOURCE",
        "treatment_status": "NOT_STARTED"
      },
      "source_ids": ["SRC-WAO-ANAPH-2020"]
    },

    {
      "id": "DIFF-01",
      "route": "DIZZINESS_TACHYCARDIA",
      "inputs": {
        "dizziness": true,
        "tachycardia": true,
        "postural": true,
        "delta_sbp": -25,
        "standing_time_min": 2
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "PROMPT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "top_hypothesis": "ORTHOSTATIC_HYPOTENSION",
      "contradicted": ["POTS"],
      "source_ids": ["SRC-AHA-OH-2024", "SRC-HRS-POTS-2015"]
    },
    {
      "id": "DIFF-02",
      "route": "DIZZINESS_TACHYCARDIA",
      "inputs": {
        "dizziness": true,
        "postural_delta_hr": 36,
        "orthostatic_hypotension": false,
        "vomiting_last_24h": true,
        "dehydration": true,
        "symptom_duration_days": 1
      },
      "expected": {
        "diagnostic_status": "SUSPECTED",
        "urgency": "PROMPT",
        "confirmation_status": "PENDING",
        "protocol_status": "NOT_EVALUATED",
        "treatment_status": "NOT_STARTED"
      },
      "top_hypothesis": "HYPOVOLEMIA",
      "contradicted": ["POTS"],
      "source_ids": ["SRC-NIH-POTS-2021"]
    },
    {
      "id": "DIFF-03",
      "route": "DIZZINESS_TACHYCARDIA",
      "inputs": {
        "tachycardia": true,
        "dyspnea": true,
        "known_allergen": true,
        "bronchospasm": true
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "EMERGENCY",
        "confirmation_status": "NOT_REQUIRED",
        "protocol_status": "BLOCKED_AUTHORIZATION",
        "treatment_status": "NOT_STARTED"
      },
      "top_hypothesis": "ANAPHYLAXIS",
      "source_ids": ["SRC-WAO-ANAPH-2020"]
    },
    {
      "id": "DIFF-04",
      "route": "DIZZINESS_TACHYCARDIA",
      "inputs": {
        "tachycardia": true,
        "nausea": true,
        "plasma_glucose_mg_dl": 280,
        "beta_hydroxybutyrate": null,
        "pH": null,
        "bicarbonate": null
      },
      "expected": {
        "diagnostic_status": "SUSPECTED",
        "urgency": "URGENT",
        "confirmation_status": "REQUIRED",
        "protocol_status": "BLOCKED_MISSING_DATA",
        "treatment_status": "NOT_STARTED"
      },
      "top_hypothesis": "DKA",
      "next_tests": ["TEST-BETA-OHB", "TEST-VENOUS-PH-BICARB"],
      "source_ids": ["SRC-DKA-2024"]
    },
    {
      "id": "DIFF-05",
      "route": "DIZZINESS_TACHYCARDIA",
      "inputs": {
        "dizziness": true,
        "tachycardia": true,
        "urine_output_ml_kg_h": 0.3,
        "urine_output_duration_h": 8,
        "creatinine_delta_48h_mg_dl": 0.4
      },
      "expected": {
        "diagnostic_status": "CRITERIA_MET",
        "urgency": "URGENT",
        "confirmation_status": "SATISFIED",
        "protocol_status": "ELIGIBLE",
        "treatment_status": "NOT_STARTED"
      },
      "top_hypothesis": "AKI",
      "secondary_hypothesis": "HYPOVOLEMIA",
      "source_ids": ["SRC-KDIGO-AKI-2012"]
    },
    {
      "id": "DIFF-06",
      "route": "DIZZINESS_TACHYCARDIA",
      "inputs": {
        "dizziness": true,
        "persistent_tachycardia": true,
        "postural_relation": false,
        "irregular_pulse": true
      },
      "expected": {
        "diagnostic_status": "INSUFFICIENT_DATA",
        "urgency": "URGENT",
        "confirmation_status": "REQUIRED",
        "protocol_status": "NOT_EVALUATED",
        "treatment_status": "NOT_STARTED"
      },
      "top_hypothesis": "EXTERNAL_ARRHYTHMIA_PATHWAY",
      "next_tests": ["TEST-ECG"],
      "must_not_output": ["POTS_DIAGNOSIS"],
      "source_ids": ["SRC-HRS-POTS-2015"]
    }
  ]
}
```

Los primeros 24 casos reproducen límites o reglas de las fuentes correspondientes; los seis casos diferenciales prueban la lógica de orquestación y están deliberadamente construidos para evitar que el motor confunda una presentación inespecífica con un diagnóstico. citeturn18search0turn21search3turn17search0turn18search3turn27search3turn21search0

## CODEX_IMPLEMENTATION_SPEC.md y validación

El repositorio previamente especificado para VIGILE es:

```text
C:\Users\Gianni\Desktop\Vigile
```

Codex debe **ampliar el motor existente, no reconstruirlo**, conservando almacenamiento, auditoría, baselines, API, simulación, permisos y pruebas ya implementados. Esta continuidad está establecida en la especificación previa del proyecto. fileciteturn0file1

La nueva capa propuesta es:

```text
engine/
└── vigile/
    ├── clinical/
    │   ├── models.py
    │   ├── evaluator.py
    │   ├── boolean_logic.py
    │   ├── quality.py
    │   ├── differential.py
    │   ├── test_selection.py
    │   ├── protocols.py
    │   ├── authorization.py
    │   ├── resources.py
    │   ├── reassessment.py
    │   └── trace.py
    │
    └── clinical_knowledge/
        ├── sources_verified.json
        ├── diagnostic_criteria.json
        ├── differential_rules.json
        ├── diagnostic_tests.json
        ├── treatment_protocols.json
        ├── contraindications.json
        ├── space_applicability.json
        └── synthetic_cases.json
```

**Modelos Pydantic**

```python
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class DiagnosticStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SUSPECTED = "SUSPECTED"
    CRITERIA_MET = "CRITERIA_MET"
    CRITERIA_NOT_MET = "CRITERIA_NOT_MET"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ClinicalUrgency(str, Enum):
    ROUTINE = "ROUTINE"
    PROMPT = "PROMPT"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class ConfirmationStatus(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    PENDING = "PENDING"
    SATISFIED = "SATISFIED"
    UNAVAILABLE = "UNAVAILABLE"


class ProtocolStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    NOT_INDICATED = "NOT_INDICATED"
    ELIGIBLE = "ELIGIBLE"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"
    BLOCKED_CONTRAINDICATION = "BLOCKED_CONTRAINDICATION"
    BLOCKED_RESOURCE = "BLOCKED_RESOURCE"
    BLOCKED_AUTHORIZATION = "BLOCKED_AUTHORIZATION"
    READY_FOR_CREW = "READY_FOR_CREW"


class TreatmentStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    MONITORING = "MONITORING"
    HELD = "HELD"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class SpaceApplicability(str, Enum):
    DIRECTLY_APPLICABLE = "DIRECTLY_APPLICABLE"
    APPLICABLE_WITH_LIMITATIONS = "APPLICABLE_WITH_LIMITATIONS"
    REQUIRES_SPACE_SPECIFIC_VALIDATION = "REQUIRES_SPACE_SPECIFIC_VALIDATION"
    NOT_ESTABLISHED_FOR_SPACEFLIGHT = "NOT_ESTABLISHED_FOR_SPACEFLIGHT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"


class MeasurementQuality(BaseModel):
    valid: bool
    device_id: str | None = None
    method: str | None = None
    reason_invalid: str | None = None
    calibration_status: str | None = None


class ClinicalObservation(BaseModel):
    observation_id: str
    concept: str
    value: float | int | bool | str | None
    unit: str | None = None
    observed_at: datetime
    body_position: str | None = None
    gravity_context: str | None = None
    quality: MeasurementQuality


class SymptomAssessment(BaseModel):
    symptom: str
    present: bool
    onset_at: datetime | None = None
    duration_seconds: int | None = None
    severity: str | None = None
    relation_to_posture: str | None = None


class ClinicalHistory(BaseModel):
    known_conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    recent_exposures: list[str] = Field(default_factory=list)


class MissionContext(BaseModel):
    mission_phase: str
    gravity_context: str
    earth_contact_state: Literal[
        "EARTH_CONNECTED",
        "DELAYED_COMMUNICATION",
        "EARTH_UNAVAILABLE",
    ]
    resource_inventory_version: str
    authorization_policy_version: str


class CriterionTraceNode(BaseModel):
    node_id: str
    result: Literal["TRUE", "FALSE", "UNKNOWN", "INVALID"]
    inputs_used: list[str] = Field(default_factory=list)
    explanation: str


class DifferentialHypothesisResult(BaseModel):
    hypothesis_id: str
    tier: str
    supporting_findings: list[str] = Field(default_factory=list)
    contradictory_findings: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    next_test_ids: list[str] = Field(default_factory=list)


class ClinicalEvaluationResult(BaseModel):
    evaluation_id: str
    patient_or_crew_id: str
    condition_id: str | None = None

    diagnostic_status: DiagnosticStatus
    urgency: ClinicalUrgency
    confirmation_status: ConfirmationStatus
    protocol_status: ProtocolStatus
    treatment_status: TreatmentStatus

    criteria_met: list[str] = Field(default_factory=list)
    criteria_not_met: list[str] = Field(default_factory=list)
    criteria_unknown: list[str] = Field(default_factory=list)
    invalid_inputs: list[str] = Field(default_factory=list)

    differentials: list[DifferentialHypothesisResult] = Field(
        default_factory=list
    )
    recommended_test_ids: list[str] = Field(default_factory=list)

    protocol_id: str | None = None
    space_applicability: SpaceApplicability

    source_ids: list[str]
    criterion_version: str | None = None
    knowledge_bundle_hash: str
    input_snapshot_hash: str

    trace: list[CriterionTraceNode] = Field(default_factory=list)

    evaluated_at: datetime
```

El modelo debe ser multi-dimensional porque diagnóstico, urgencia y tratamiento no forman una única secuencia lineal. Esta es una decisión de diseño de VIGILE sustentada por la necesidad de actuar frente a cuadros como anafilaxia mientras se continúa la evaluación. citeturn21search0turn24search1

**Contrato de entrada**

```json
{
  "crew_id": "ASTRONAUT_01",
  "presentation": ["dizziness", "tachycardia"],
  "observations": [],
  "symptoms": [],
  "history": {},
  "mission_context": {
    "mission_phase": "MARS_TRANSIT",
    "gravity_context": "FREE_MICROGRAVITY",
    "earth_contact_state": "DELAYED_COMMUNICATION",
    "resource_inventory_version": "inv-2026-10",
    "authorization_policy_version": "auth-001"
  },
  "requested_mode": "DIAGNOSTIC_AND_DIFFERENTIAL"
}
```

**Contrato de salida**

```json
{
  "diagnostic_status": "INSUFFICIENT_DATA",
  "urgency": "PROMPT",
  "confirmation_status": "REQUIRED",
  "protocol_status": "NOT_EVALUATED",
  "treatment_status": "NOT_STARTED",
  "criteria_met": [],
  "criteria_unknown": ["orthostatic_response"],
  "differentials": [],
  "recommended_test_ids": [],
  "space_applicability": "CONTEXT_DEPENDENT",
  "source_ids": [],
  "trace": []
}
```

**API**

```text
POST /clinical/evaluations
GET  /clinical/evaluations/{evaluation_id}

POST /clinical/presentations/evaluate
GET  /clinical/evaluations/{evaluation_id}/differential
GET  /clinical/evaluations/{evaluation_id}/next-tests

GET  /clinical/conditions/{condition_id}
GET  /clinical/conditions/{condition_id}/criteria
GET  /clinical/criteria/{criterion_id}

GET  /clinical/protocols/{protocol_id}
POST /clinical/protocols/{protocol_id}/eligibility

POST /clinical/evaluations/{evaluation_id}/reassess

GET  /clinical/sources/{source_id}
GET  /clinical/knowledge/version
```

El endpoint `protocol-eligibility` **no ejecuta un tratamiento**. Devuelve una evaluación estructurada:

```json
{
  "protocol_id": "PROT-ANAPH-IM-EPI",
  "evidence_supported": true,
  "mission_approved": false,
  "resource_available": true,
  "contraindications_cleared": true,
  "protocol_status": "BLOCKED_AUTHORIZATION",
  "reasons": ["MISSION_POLICY_NOT_AUTHORIZED"]
}
```

Solo un módulo operacional separado, con permisos explícitos, podría registrar:

```text
treatment_status = STARTED
```

**Semántica obligatoria de valores ausentes**

```python
def compare(value, operator, threshold):
    if value is None:
        return "UNKNOWN"

    if not value.quality.valid:
        return "INVALID"

    return apply_operator(value, operator, threshold)
```

Prohibido:

```python
# NO HACER
if value is None:
    value = 0
```

También prohibido:

```python
# NO HACER
if not criterion_met:
    condition_excluded = True
```

Debe ser:

```python
if criterion_has_missing_required_inputs:
    diagnostic_status = DiagnosticStatus.INSUFFICIENT_DATA
elif criterion_evaluates_false:
    diagnostic_status = DiagnosticStatus.CRITERIA_NOT_MET
```

**Evaluación de árboles JSON**

Codex debe admitir:

```text
all_of
any_of
none_of
at_least_n_of
comparison
temporal_window
change_from_baseline
ratio_to_baseline
repeat_confirmation
symptom_presence
exposure_presence
context_requirement
quality_requirement
exclusion_present
```

Los árboles deben producir un trace completo:

```json
{
  "node_id": "DKA-KETOSIS",
  "result": "TRUE",
  "inputs_used": ["beta_hydroxybutyrate=4.2 mmol/L"],
  "source_id": "SRC-DKA-2024",
  "rule": "beta_hydroxybutyrate >= 3.0 mmol/L"
}
```

**Pruebas unitarias mínimas**

```python
def test_single_fpg_requires_confirmation():
    case = load_case("DM-02")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.SUSPECTED
    assert result.confirmation_status == ConfirmationStatus.REQUIRED


def test_cgm_is_not_direct_diabetes_diagnosis():
    case = load_case("DM-04")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.INSUFFICIENT_DATA
    assert "TEST-PLASMA-GLUCOSE" in result.recommended_test_ids


def test_euglycemic_dka_allowed_with_known_diabetes():
    case = load_case("DM-05")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.CRITERIA_MET
    assert result.urgency == ClinicalUrgency.EMERGENCY


def test_missing_acid_base_data_does_not_confirm_dka():
    case = load_case("DM-06")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.SUSPECTED
    assert result.confirmation_status == ConfirmationStatus.REQUIRED


def test_pots_blocked_by_dehydration():
    case = load_case("ORTHO-05")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.CRITERIA_NOT_MET


def test_orthostatic_test_not_applicable_in_free_microgravity():
    case = load_case("ORTHO-06")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.NOT_APPLICABLE


def test_aki_delta_creatinine():
    case = load_case("AKI-01")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.CRITERIA_MET
    assert result.metadata["aki_stage"] == 1


def test_missing_aki_baseline_not_assumed_normal():
    case = load_case("AKI-05")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.INSUFFICIENT_DATA


def test_anaphylaxis_without_skin_can_meet_WAO_path_two():
    case = load_case("ANAPH-02")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.CRITERIA_MET
    assert result.urgency == ClinicalUrgency.EMERGENCY


def test_anaphylaxis_protocol_can_be_blocked_even_when_diagnosis_met():
    case = load_case("ANAPH-06")
    result = evaluate(case)

    assert result.diagnostic_status == DiagnosticStatus.CRITERIA_MET
    assert result.protocol_status == ProtocolStatus.BLOCKED_RESOURCE


def test_oh_contradicts_pots_path():
    case = load_case("DIFF-01")
    result = evaluate(case)

    assert result.differentials[0].hypothesis_id == "ORTHOSTATIC_HYPOTENSION"
    assert hypothesis(result, "POTS").tier == "CONTRADICTED"


def test_nonpostural_irregular_tachycardia_does_not_become_pots():
    case = load_case("DIFF-06")
    result = evaluate(case)

    assert result.recommended_test_ids == ["TEST-ECG"]
    assert result.condition_id != "POTS"
```

**Pruebas negativas obligatorias**

Codex debe añadir, además de los 30 casos clínicos:

```text
glucose wrong unit
creatinine wrong unit
unconvertible unit
timestamp missing
measurement outside temporal window
invalid assay
invalid fasting duration
A1C-glucose discordance
CGM supplied instead of plasma glucose
DKA missing ketones
DKA missing acid-base data
DKA potassium missing before treatment eligibility
DKA potassium <3.5
OH measurement >3 min when evaluating classic criterion
OH missing baseline
POTS symptoms <3 months
POTS dehydration
POTS infection
POTS orthostatic hypotension present
orthostatic test in free microgravity
AKI missing baseline and missing urine output
AKI invalid urine collection window
anaphylaxis without sufficient clinical combination
anaphylaxis without skin but valid WAO pathway 2
epinephrine inventory unavailable
mission authorization absent
knowledge source superseded
criterion source marked DRAFT
LLM attempts to modify criterion
LLM attempts to authorize protocol
LLM attempts to change a dose
replay with same input and knowledge hash
```

**LLM/RAG boundary**

```text
LLM MAY READ
✓ observations
✓ evaluated clinical states
✓ criteria satisfied
✓ missing evidence
✓ differential hypotheses
✓ recommended tests
✓ approved source text
✓ protocol eligibility
✓ authorization status

LLM MAY EXPLAIN
✓ why a criterion was met
✓ why a diagnosis remains unresolved
✓ why another test is required
✓ why a protocol is blocked

LLM MAY NOT WRITE
✗ threshold
✗ diagnostic state
✗ source version
✗ medication dose
✗ mission authorization
✗ protocol eligibility
✗ treatment execution
```

NASA está investigando CDSS precisamente como apoyo cognitivo y procedimental para una tripulación cada vez más autónoma; nada en esas publicaciones obliga a que las conclusiones clínicas procedan de un LLM generativo, por lo que mantener la generación de lenguaje separada del motor determinista es coherente con el objetivo de auditabilidad de VIGILE. citeturn19search1turn19search4turn19search5

**Criterios de aceptación de Codex**

La iteración solo debe considerarse terminada cuando se cumplan todos estos puntos:

```text
[ ] Los 30 casos sintéticos pasan.

[ ] Diabetes:
    un FPG aislado >=126 mg/dL en persona asintomática
    NO produce confirmación automática.

[ ] Diabetes:
    dos resultados anormales válidos pueden satisfacer
    la regla de confirmación ADA.

[ ] CGM/interstitial glucose nunca satisface directamente
    el criterio diagnóstico ADA 2026.

[ ] Random plasma glucose >=200 mg/dL solo usa la vía
    diagnóstica inmediata cuando existe el contexto clínico
    requerido por ADA.

[ ] DKA exige simultáneamente:
    diabetes/hiperglucemia + cetosis + acidosis.

[ ] DKA euglucémica no queda excluida solo porque
    glucose <200 mg/dL cuando existe diabetes conocida.

[ ] DKA con K <3.5 mmol/L bloquea la fase de insulina
    del protocolo representado.

[ ] Una prueba ausente nunca se convierte en normal.

[ ] OH reconoce exactamente >=20 mmHg sistólica
    o >=10 mmHg diastólica dentro del contexto temporal.

[ ] OH positivo impide diagnosticar POTS mediante
    la ruta POTS definida.

[ ] POTS exige duración >=3 meses y revisión
    de explicaciones alternativas.

[ ] El test ortostático estándar queda NOT_APPLICABLE
    en microgravedad libre.

[ ] AKI reconoce las tres vías KDIGO.

[ ] AKI usa el peor estadio cumplido.

[ ] Un baseline de creatinina desconocido nunca se inventa.

[ ] El borrador KDIGO 2026 nunca se carga como
    fuente CURRENT de producción.

[ ] Anafilaxia puede cumplir criterios sin afectación cutánea
    a través de la segunda vía WAO.

[ ] Cumplir criterios de anafilaxia y tener un protocolo
    bloqueado son estados simultáneamente representables.

[ ] Ningún protocolo pasa a READY_FOR_CREW
    sin autorización + recursos + datos de seguridad.

[ ] El motor diferencial nunca genera probabilidades
    numéricas no calibradas.

[ ] Las rutas no investigadas permanecen
    EXTERNAL_PATHWAY_REQUIRED.

[ ] El LLM no puede modificar reglas ni resultados.

[ ] Cada decisión conserva:
    source_id
    criterion_version
    knowledge_bundle_hash
    input_snapshot_hash
    trace

[ ] Replay con los mismos datos y conocimiento
    produce el mismo resultado.
```

Las pruebas de conformidad no equivalen a validación clínica. La secuencia necesaria sigue siendo:

```text
regla verificada contra fuente
        ↓
unit test
        ↓
caso sintético
        ↓
revisión clínica independiente
        ↓
validación retrospectiva
        ↓
validación prospectiva
        ↓
validación en análogo espacial
        ↓
validación operacional específica de misión
        ↓
autorización
```

Esto es especialmente importante porque EIMO sigue siendo una dirección de desarrollo e investigación de NASA destinada a aumentar gradualmente la autonomía, no una certificación genérica de cualquier CDSS autónomo. citeturn19search0turn19search1turn19search6

La implementación resultante debe producir un salto claramente observable respecto de VIGILE actual:

```text
ANTES

sensor
  ↓
valor
  ↓
umbral
  ↓
alerta
```

```text
DESPUÉS

sensor + síntomas + historia + contexto
                ↓
       calidad de los datos
                ↓
          urgencia paralela
                ↓
        criterios clínicos
                ↓
       confirmación necesaria
                ↓
       diferencial estructurado
                ↓
         siguiente prueba
                ↓
       protocolo candidato
                ↓
 autorización + recursos + seguridad
                ↓
        actuación de tripulación
                ↓
           reevaluación
```

Esta arquitectura cumple el objetivo más importante de la especificación original: **VIGILE deja de limitarse a avisar que un dato es extraño y empieza a determinar, mediante reglas trazables, qué condición clínica está respaldada, qué alternativas siguen abiertas, qué datos faltan y qué protocolo preautorizado puede aplicarse sin depender de una respuesta generativa ni de comunicación inmediata con Tierra.** fileciteturn0file0 La idea de aumentar progresivamente esa autonomía está alineada con EIMO y con la exigencia de NASA-STD-3001 de diseñar las capacidades médicas según riesgo, necesidades de la tripulación, guías clínicas y restricciones de la misión. citeturn19search0turn19search2