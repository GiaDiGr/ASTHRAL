# VIGILE — Base biomédica integral y computable para el Health Intelligence Engine

## Resumen ejecutivo

He cerrado esta iteración como la **investigación biomédica general de referencia para VIGILE**, siguiendo la especificación integral que proporcionaste: especialidades médicas + ciclo completo de atención + evidencia primaria + reglas computables + algoritmos + sensores + datasets + trazabilidad + handoff para Codex. fileciteturn0file0

**Paquete principal:**

[Descargar VIGILE_FINAL_BIOMEDICAL_KNOWLEDGE.zip](ARCHIVO_ORIGINAL_NO_RECUPERADO)

También puedes abrir directamente los artefactos principales:

- [Handoff biomédico para Codex](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Registro maestro de fuentes](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Extracciones de evidencia primaria](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Catálogo integral de condiciones](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Clinical Pathways](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Reglas computables JSON](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Biblioteca de algoritmos](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Matriz de cobertura clínica](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Casos de prueba sintéticos](ARCHIVO_ORIGINAL_NO_RECUPERADO)
- [Limitaciones y validación](ARCHIVO_ORIGINAL_NO_RECUPERADO)

El paquete contiene **53 registros de fuentes**, **49 extracciones de evidencia localizadas**, **34 condiciones/riesgos clínicos**, **13 reglas computables de primera implementación**, **11 algoritmos formalizados**, un inventario de sensores y biomarcadores, relaciones multisistema, datasets, matriz condición × etapa clínica, gaps, 16 casos sintéticos y una especificación técnica para Codex. Es deliberadamente más conservador que “rellenar” todos los protocolos: cuando la literatura pública no permite justificar diagnóstico, tratamiento o triaje autónomo, se conserva `REQUIRES_VALIDATION`, `REQUIRES_MISSION_AUTHORIZATION`, `RESEARCH_ONLY` o `NOT_PUBLICLY_AVAILABLE`.

La conclusión más importante es que **VIGILE sí puede ser integral sin fingir que todas las especialidades tienen el mismo nivel de automatización**. Los componentes más maduros para determinismo inmediato son cumplimiento ambiental, capacidad aeróbica, fuerza muscular, BMD, contabilidad radiológica, adquisición longitudinal, trazabilidad y una parte de la vigilancia SANS; sueño, cognición, inmunidad, salud conductual, sensorimotor, renal y otras áreas pueden tener monitorización y evaluación estructurada bastante amplias, pero determinadas etapas clínicas necesitan autorización humana o protocolos operativos que no están públicamente disponibles. Esa separación coincide con el enfoque de autonomía progresiva y apoyo a decisiones que NASA ExMC plantea para operaciones médicas independientes de la Tierra. citeturn25search1turn25search11turn25search2

La arquitectura biomédica final que emerge es:

```text
PREVENCIÓN
   ↓
MONITORIZACIÓN
   ↓
CONTROL DE CALIDAD
   ↓
BASELINE PERSONAL + CONTEXTO DE MISIÓN
   ↓
DETECCIÓN
   ↓
EVALUACIÓN GUIADA + DIAGNÓSTICO DIFERENCIAL
   ↓
TRIAJE / ESCALAMIENTO
   ↓
¿PROTOCOLO AUTORIZADO?
   ├── Sí → INTERVENCIÓN SUPPORT
   └── No → REQUIRES_VALIDATION / HUMAN AUTHORITY
   ↓
RECUPERACIÓN
   ↓
SEGUIMIENTO
   ↓
REEVALUACIÓN LONGITUDINAL
```

Y, crucialmente:

> **medición anómala ≠ incumplimiento NASA ≠ hallazgo clínico ≠ diagnóstico ≠ autorización terapéutica.**

Esas cinco entidades quedan separadas en el modelo.

## Auditoría documental y fuentes fundamentales

La revisión anterior era útil, pero estaba mucho más cerca de un inventario bibliográfico con algunos localizadores que de una especificación clínica integral. En esta investigación mantuve los hallazgos que podían sostenerse y amplié particularmente las normas NASA actuales, SANS, inmunología, renal, arquitectura de medicina autónoma, datasets e interoperabilidad.

### NASA-STD-3001 como columna vertebral normativa

Para el software, **NASA-STD-3001 Volume 1 Rev. C** y **Volume 2 Rev. F** son las dos fuentes normativas centrales. La primera establece requisitos de salud de la tripulación; la segunda cubre factores humanos, habitabilidad y salud ambiental. La Rev. F del Volume 2 es la revisión vigente de 2026 identificada durante la investigación. citeturn0search1turn0search2turn0search3

Los requisitos que ya pueden convertirse en checks determinísticos son especialmente valiosos:

| Source locator | Evidencia extraída | Traducción correcta a VIGILE |
|---|---|---|
| V1 4001, p. 32 | VO₂max ≥ **32.9 mL/min/kg** en el contexto aplicable de EVA en microgravedad | Requirement check contextual |
| V1 4002, p. 33 | VO₂max ≥ **36.5 mL/min/kg** para EVA en superficie extraterrestre | Requirement check contextual |
| V1 4003, p. 33 | Capacidad aeróbica durante misión ≥ **80%** del valor preflight comparable | Ratio contra baseline |
| V1 4024, p. 38 | Fuerza muscular durante misión ≥ **80%** del baseline preflight comparable | Ratio por mismo grupo/test |
| V1 4027, p. 39 | BMD hip/columna ≥ **95%**, cuello femoral ≥ **90%** del preflight | Comparación por sitio anatómico |
| V1 4030, p. 40 | Dosis efectiva profesional acumulada debida a vuelo espacial < **600 mSv** | Radiation career ledger |
| V2 6002, p. 49 | Al menos **30% de gas diluyente** en el contexto de cabina especificado | Environmental rule |
| V2 6003, pp. 49–51 | Bandas de exposición de presión parcial inspirada de O₂ | PIO₂ exposure classifier |
| V2 6004, p. 51 | Promedio de una hora de ppCO₂ ≤ **3 mmHg** | Rolling time-weighted average |
| V2 6006, p. 52 | Para exposición indefinida: **34.5 kPa < P ≤ 103 kPa** | Pressure-envelope rule |
| V2 6020, p. 58 | Registro automático por compartimento de presión, humedad, temperatura, ppO₂ y ppCO₂ | Mandatory telemetry coverage |

Los tres requisitos de VO₂ están directamente contenidos en V1 4001–4003; es importante que el software seleccione el requisito en función del tipo de misión/EVA y no trate un incumplimiento como diagnóstico cardiovascular. citeturn4view0turn4view1turn5view0turn5view1

La fuerza tiene la misma lógica. NASA exige conservar al menos el 80% de la fuerza preflight, pero la comparación tiene sentido únicamente entre mediciones verdaderamente comparables; el estándar también proporciona una tabla de requisitos preflight de fuerza que varían por tareas/escenario. citeturn5view2turn8view2

Para hueso, NASA diferencia explícitamente el sitio anatómico: total hip y columna tienen un objetivo de conservación ≥95% y femoral neck ≥90%. VIGILE, por tanto, no puede almacenar simplemente una variable genérica `bone_density`: debe conservar región anatómica, método, dispositivo/protocolo y baseline comparable. Tampoco debe transformar por sí solo una pérdida de BMD en una probabilidad individual de fractura. citeturn8view3turn14view3

La radiación exige todavía más disciplina de tipos. NASA utiliza distintas magnitudes según el requisito; el límite de dosis efectiva profesional acumulada es 600 mSv, mientras que la tabla de órganos emplea mGy-Eq o mGy según el tejido. La tabla incluye, entre otros, lens 1000/2000/4000 mGy-Eq para 30 días/1 año/carrera, skin 1500/3000/6000, blood-forming organs 250/500 para 30 días/1 año y circulatory system 250/500/1000. **VIGILE tiene que impedir por tipo que se sumen silenciosamente mSv, mGy y mGy-Eq.** citeturn4view4turn5view4turn5view5

### Salud ambiental

V2 es una fuente excepcionalmente buena para la parte autónoma porque muchas disposiciones sí poseen semántica determinística. NASA especifica una atmósfera con al menos 30% de diluyente en el contexto aplicable, una tabla de presión parcial inspirada de oxígeno, un promedio horario de ppCO₂ no superior a 3 mmHg y un intervalo de presión para exposición indefinida de más de 34.5 hasta 103 kPa. citeturn21view0turn21view1turn21view2

La tabla de O₂ permite además derivar computacionalmente PIO₂ según el contexto del estándar. En el paquete se conserva la relación:

```text
PIO2 = (PB - 47 mmHg) × FIO2
```

junto con las condiciones de uso; no se trata como una fórmula diagnóstica de enfermedad, sino como cálculo ambiental de exposición. La tabla identifica un objetivo normóxico de aproximadamente 145–155 mmHg y condiciones inferiores/superiores dependientes de duración. citeturn23view2turn5view8

V2 también es explícito sobre telemetría: cada compartimento habitable aislable debe registrar automáticamente presión, humedad, temperatura, ppO₂ y ppCO₂, y esos datos deben poder mostrarse en tiempo real y disparar alertas ante límites seguros. NASA además contempla monitorización de VOC y productos de combustión, pero muchos límites tóxicos son sustancia y misión específicos; por ello el motor queda diseñado para cargar perfiles SMAC/mission-authorized y no inventarlos. citeturn23view0turn23view1

Una consecuencia de ingeniería especialmente importante es que VIGILE **no debe declarar “NORMAL” cuando faltan datos críticos**. La ausencia de telemetría atmosférica se trata como `INCONCLUSIVE` o `DATA_COVERAGE_FAILURE`.

### Medicina autónoma e interoperabilidad

NASA ExMC lleva años trabajando explícitamente en arquitecturas de Clinical Decision Support para exploración, donde comunicación retardada, limitaciones de masa/potencia/volumen, disponibilidad limitada de expertos y falta de evacuación inmediata aumentan la necesidad de autonomía local. El EIMO ConOps de 2025 formula precisamente una transición progresiva de responsabilidades desde sistemas dependientes de Tierra hacia operaciones médicas independientes de Tierra. citeturn25search1turn25search2

CHP-IDSP, por su parte, desarrolla una plataforma de datos integrada con modelos/APIs comunes entre información ambiental, médica, ejercicio, sueño y rendimiento, lo cual respalda la decisión arquitectónica de que VIGILE no construya veinte motores incomunicados, sino una capa común de eventos, contexto, evidencia y tiempo. citeturn25search0

Esta es una de las conclusiones más fuertes de la investigación: **la salud integral no debe implementarse como una lista de especialidades; debe implementarse como un grafo longitudinal de eventos fisiológicos, ambientales, funcionales y clínicos.**

## Evidencia clínica, condiciones y pathways

El catálogo estructurado contiene 34 condiciones/riesgos iniciales. No son las únicas condiciones médicas imaginables, sino el conjunto amplio que puede justificarse ahora mediante el corpus público revisado sin convertir VIGILE en un catálogo de enfermedades terrestres irrelevantes para operaciones espaciales.

### Cobertura integral

| Dominio | Capacidad más sólida actual | Principal limitación |
|---|---|---|
| Cardiovascular | VO₂, tendencias, contexto ortostático, VTE structured assessment | Diagnóstico/tratamiento autónomo |
| Muscular | Fuerza, baseline, retención, recuperación | Prescripción personalizada requiere autorización |
| Óseo | BMD por sitio, tendencias, recovery | BMD no basta para probabilidad individual de fractura |
| SANS | OCT, fundoscopy, vigilancia longitudinal | Tratamiento/countermeasure definitivo no establecido |
| Sueño/circadiano | Actigrafía, horario, luz, tendencias | Monitorización no equivale a diagnóstico de trastorno |
| Cognición | Batería cognitiva, speed/accuracy, z longitudinal | No hay cutpoint clínico universal |
| Behavioral health | Escalas, tendencias, contexto, escalamiento humano | Crisis/terapia deben permanecer human-controlled |
| Inmune/infeccioso | Baseline, tendencias, viral reactivation | Umbrales clínicos espaciales incompletos |
| Renal | Riesgo, urine chemistry, ultrasound, proposed ConOps | Disponibilidad/autorización de tratamientos |
| Radiación | Ledger de dosis y límites normativos | Predicción individual de efectos clínicos |
| Nutrición | Requirements/provision/intake tracking | Ecuaciones y prescripción individual deben versionarse |
| Respiratorio | Integración SpO₂/respiración/ambiente | Protocolos espaciales públicos incompletos |
| Sensorimotor | Función alrededor de transiciones gravitacionales | Criterios clínicos específicos dependen de tarea/misión |
| Farmacología | Stock, storage, shelf life, expiry | PK/PD espacial y dosificación |
| Emergencias | Detección/red flags/escalamiento/capability check | Protocolos operativos detallados no completamente públicos |
| Ambiental | O₂, CO₂, presión, VOC, combustión | Límites específicos de compuestos/eventos |

### SANS como ejemplo de evidencia realmente computable

El Evidence Report de NASA sobre SANS proporciona uno de los mejores ejemplos de cómo VIGILE debe transformar literatura en código. El informe utiliza OCT y define una medida de grosor retinal alrededor de la apertura de Bruch; un incremento de **más de 19.4 µm** respecto al baseline en la región BMO–250 µm funciona como señal temprana de optic-disc edema que justifica mayor monitorización. El mismo informe explica que el Frisén grade ≥1 representa edema clínicamente significativo, pero su evaluación es subjetiva y menos sensible para cambios tempranos. citeturn15view0turn16view0

De ahí sale una regla mucho mejor que “si visión mala → SANS”:

```json
{
  "RuleID": "R-SANS-OCT",
  "ConditionID": "C-SANS",
  "inputs": [
    {"name": "current_trt_bmo250", "unit": "um"},
    {"name": "baseline_trt_bmo250", "unit": "um"}
  ],
  "derived": [
    "delta = current_trt_bmo250 - baseline_trt_bmo250"
  ],
  "logic": "delta > 19.4",
  "output": "EARLY_OPTIC_DISC_EDEMA_SIGNAL_INCREASE_MONITORING",
  "authorization": "ASSESSMENT_SUPPORT",
  "validation": "NOT_DEFINITIVE_SANS_DIAGNOSIS"
}
```

Eso muestra exactamente la filosofía que queremos: **usar toda la evidencia computable sin exagerar lo que esa evidencia demuestra**.

### Inmunidad: integral, pero deliberadamente no sobreactuada

NASA documenta cambios de inmunidad durante y después del vuelo, incluyendo alteraciones de función celular y reactivación de virus latentes. Sin embargo, el Evidence Report también reconoce que las cohortes son pequeñas y que no existe evidencia suficiente para transformar de forma general estos cambios en riesgo clínico cuantificado para misiones de exploración prolongadas. Las mediciones se prestan mejor a comparaciones preflight–inflight–postflight y seguimiento hacia baseline. citeturn18view0turn19view0

Por ello la regla inmune del paquete hace:

```text
assay → QC → comparación con baseline → trend → contextualización
```

y **no**:

```text
cytokine X subió 25% → enfermedad Y
```

La segunda lógica sería precisamente una invención clínica.

### Sueño, cognición y behavioral health

NASA Standard Measures combina longitudinalmente sueño/vigilia, cognición, inmunidad, bioquímica, microbioma, cardiovascular, sensorimotor y procesos de equipo, proporcionando un precedente directo para la arquitectura multisistema de VIGILE. citeturn25search3

En cognición, un estudio de astronautas de ISS con 25 participantes analizó velocidad y exactitud a través de cinco fases de misión y utilizó resultados corregidos por efectos de práctica y z-scores respecto al rendimiento preflight. Eso sí puede inspirar el algoritmo longitudinal, pero **el estudio no convierte un z-score concreto en un diagnóstico universal de deterioro cognitivo**. citeturn25search18

NASA también mantiene un Evidence Report reciente para riesgo cognitivo/conductual/psiquiátrico; esto justifica que VIGILE integre esa área, pero la transición desde cuestionario o variación de rendimiento hasta diagnóstico psiquiátrico o intervención terapéutica debe permanecer bajo evaluación humana. citeturn2view4

### Renal y otras áreas clínicas

El Evidence Report de NASA de 2024 sobre renal stones es particularmente útil porque incluye además un **proposed expanded Concept of Operations for Mars missions**. Esa distinción se conserva en el package: “propuesto” no se transforma automáticamente en “flight authorized”. citeturn14view2

Lo mismo se aplica a VTE, emergencias, heridas, gastrointestinal, dental, ENT, respiratory y otras condiciones: VIGILE puede conocer recursos disponibles, recoger síntomas, dirigir preguntas y pruebas, detectar red flags, mostrar un differential y escalar; no debería fabricar un tratamiento NASA inexistente públicamente.

## Reglas, algoritmos, sensores e interacciones multisistema

El paquete incluye actualmente 13 reglas JSON-ready que cubren la primera capa de mayor certeza. Son **ejemplos directamente implementables**, no un techo arquitectónico.

Entre ellas:

```text
R-AERO-MICRO-EVA
R-AERO-SURFACE-EVA
R-AERO-RETENTION
R-MUSCLE-RETENTION
R-BONE-HIP-SPINE
R-BONE-FEMORAL-NECK
R-RAD-CAREER
R-CO2-1H
R-CABIN-PRESSURE
R-SANS-OCT
R-NUTRITION-PROVISION
R-IMMUNE-TREND
R-EVA-CLEARANCE
```

La regla de nutrición se basa en el requisito de NASA de proporcionar el 100% de los requerimientos calculados de nutrientes y energía, pero el propio diseño distingue **provision** de **actual intake** y exige que la ecuación utilizada para calcular necesidades tenga su propia procedencia/versionado. citeturn8view2

El paquete también formaliza algoritmos transversales:

```text
Retention = current / comparable_baseline

Percent retention = 100 × current / baseline

TWA = Σ(value_i × Δt_i) / ΣΔt_i

PIO2 = (PB - 47 mmHg) × FIO2

ΔTRT = TRT_current - TRT_preflight

z = (score - corrected_baseline_mean) / baseline_SD
```

Para anomalías longitudinales se incluyen median/MAD, EWMA y CUSUM **solamente como `ENGINEERING_CHOICE / REQUIRES_VALIDATION`**. Esto es importante: son técnicas matemáticas razonables para detectar cambio, pero NASA no convierte automáticamente un robust-z o un CUSUM en enfermedad.

### Arquitectura multisistema

Algunas relaciones incluidas son:

```text
sueño ↔ cognición
sueño ↔ salud conductual
estrés/circadiano ↔ inmunidad
bone loss ↔ renal stone
hidratación ↔ respuesta hemodinámica
ejercicio ↔ cardiovascular ↔ muscular ↔ hueso
CO₂ ↔ síntomas neurológicos/cognitivos
SANS ↔ fluid shift
radiación ↔ múltiples sistemas
nutrición ↔ músculo/hueso/inmunidad
medicación ↔ sueño/cognición/hemodinámica
ambiente ↔ síntomas respiratorios
```

Estas relaciones no se codifican como causalidad automática. Por ejemplo, el Evidence Report inmune considera estrés, sueño/circadiano y otros estresores como componentes relevantes, pero no permite afirmar que cualquier alteración simultánea determine causalidad individual. citeturn19view0

El comportamiento esperado de una regla compuesta es por tanto:

```python
sleep_deterioration
+ persistent_cognitive_change
+ valid_measurements
→ increase_assessment_priority
```

y no:

```python
sleep_deterioration
+ cognitive_change
→ diagnose_neurological_disease
```

### Sensor layer

NASA y las agencias asociadas respaldan la viabilidad operacional o experimental de una combinación bastante amplia de sensores y pruebas. JAXA describe gestión médica preflight/inflight/postflight y uso de equipos como ECG, presión arterial y ultrasound; CSA ha trabajado con Bio-Monitor para medidas wearables como frecuencia cardiaca, respiración y SpO₂. citeturn24search20turn24search10

El registry diferencia explícitamente:

- continuously sensed;
- wearable;
- periodically measured;
- functional test;
- imaging;
- laboratory;
- questionnaire;
- manually entered;
- environmental;
- derived.

Esto evita el error de tratar un DXA, una cytokine panel y la frecuencia cardiaca como tres streams continuos equivalentes.

## Datasets, biblioteca offline y cobertura de validación

NASA OSDR es la principal fuente pública identificada para datos de space biology y analogs. La documentación oficial señala que el repositorio contiene, según el estudio, datos ómicos, fenotípicos, fisiológicos, conductuales e imágenes; buena parte de los datos abiertos pueden consultarse/descargarse sin autenticación, mientras que determinados datos derivados de astronautas —en particular secuencias— pueden tener acceso controlado. citeturn20search3turn20search4

El package conserva además datasets/estudios candidatos como los analogs de bed rest NASA ya identificados en la fase previa, pero no los etiqueta como “validación clínica espacial”: bed rest es un modelo terrestre útil para cambios fisiológicos asociados al unloading y para ensayar countermeasures, no un sustituto perfecto de un vuelo a Marte.

ESA aporta HREDA, que agrupa décadas de investigaciones humanas espaciales y análogas; a diferencia de buena parte del OSDR abierto, HREDA exige autenticación para descargar datos, incluso cuando el producto científico sea público. Algunos productos con DOI indican licencias como CC BY-NC 3.0 IGO, pero la licencia debe verificarse a nivel de dataset. citeturn20search0turn20search2turn20search10turn20search11

DLR continúa utilizando bed rest como modelo central para estudiar efectos relacionados con weightlessness y evaluar contramedidas, lo que hace esos datasets especialmente útiles para el desarrollo de algoritmos longitudinales de cardiovascular, músculo, hueso y sensorimotor. citeturn24search18

### Development Library frente a Operational Library

El paquete separa dos conceptos:

**Development Library** puede contener Evidence Reports, papers, datasets, standards y documentación utilizada para construir/validar VIGILE.

**Operational RAG Library** debería contener únicamente documentación legalmente almacenada y apropiada para operación, con versión, hash, licencia y estado de autorización.

No se ha supuesto que “PDF accesible públicamente” signifique “redistribución libre”. En el registro RAG hay una política por documento: `store`, `link/hash`, `rights review`, etc.

Esto también influye en el RAG: el corpus operacional no debería ser simplemente una carpeta de cientos de papers. Debe privilegiar:

```text
protocolos autorizados
→ normas vigentes
→ procedimientos de misión
→ referencias clínicas aprobadas
→ evidence reports pertinentes
→ literatura de apoyo
```

## Especificación final para Codex

El handoff preparado para Codex ya no le pide que “investigue medicina espacial y vea qué implementa”. Le dice qué entidades separar, qué localizadores consultar, qué reglas programar primero, qué resultados devolver y qué funciones deben permanecer bloqueadas.

El orden de implementación recomendado es:

### Núcleo biomédico común

```text
EvidenceRegistry
SourceVersionRegistry
AstronautProfile
MissionContext
TypedMeasurementStore
DataQualityEngine
PersonalBaselineEngine
TrendEngine
AuthorizationEngine
AuditTrail
RuleEngine
ClinicalEpisodeEngine
FollowUpEngine
```

Todos los datos deberían llevar, como mínimo:

```text
subject
timestamp
measurement type
value
unit
method/device
anatomical site if applicable
mission phase
gravity context
environmental context
quality
provenance
```

### Primera capa de alta confianza

Implementar completamente:

```text
EnvironmentalHealthEngine
AerobicRequirementEngine
MuscleRequirementEngine
BoneRequirementEngine
RadiationLedger
SANSOCTMonitoring
```

Estos son los mejores dominios para demostrar determinismo + trazabilidad.

### Segunda capa integral

Después:

```text
SleepCircadianEngine
CognitivePerformanceEngine
BehavioralHealthMonitoring
ImmuneMonitoring
RenalAssessment
SensorimotorAssessment
NutritionHydrationEngine
RespiratoryAssessment
MedicationIntegrityEngine
MultisystemCorrelationEngine
```

### Clinical Protocol Engine

Finalmente, en vez de hardcodear tratamientos:

```text
Protocol
 ├── protocol_id
 ├── version
 ├── issuing_authority
 ├── applicable_mission
 ├── indications
 ├── contraindications
 ├── required_resources
 ├── steps
 ├── stop_conditions
 ├── follow_up
 ├── evidence
 ├── authorization_signature
 └── validity_period
```

Ese diseño es particularmente coherente con EIMO: en exploración profunda habrá más autonomía local, pero la autonomía requiere sistemas, referencias, sensores, entrenamiento y autoridad operativa bien definidos; no significa entregar la medicina al LLM. citeturn25search2turn25search11

### LLM

El LLM debería tener permiso para:

```text
GET findings
GET evidence
GET protocol
GET trends
START guided assessment
EXPLAIN result
SEARCH RAG
```

pero no:

```text
PATCH rule threshold
PATCH protocol
AUTHORIZE treatment
CHANGE severity
DELETE audit log
OVERRIDE mission authority
```

Ese boundary es fundamental.

### Modelo de estados

Recomiendo conservar:

```text
NORMAL
WATCH
CAUTION
CRITICAL
INCONCLUSIVE
REQUIRES_VALIDATION
```

pero **en dimensiones separadas**.

Ejemplo:

```json
{
  "data_quality": "VALID",
  "normative_compliance": "NON_COMPLIANT",
  "clinical_finding": "AEROBIC_CAPACITY_BELOW_REQUIREMENT",
  "diagnosis": null,
  "severity": "CAUTION",
  "evidence_confidence": "HIGH_FOR_NASA_REQUIREMENT",
  "authorization": "HUMAN_REVIEW_REQUIRED"
}
```

Esto es muy superior a guardar solamente:

```json
{"status": "CRITICAL"}
```

porque permite explicar exactamente qué sabemos y qué no sabemos.

## Validación, vacíos restantes y significado de “integral”

Esta investigación reduce mucho el trabajo documental pendiente, pero **ninguna búsqueda pública puede convertir VIGILE en un sistema médico de vuelo completamente validado**, porque hay tres límites objetivos.

Primero, parte de la medicina operacional depende de requisitos, recursos y procedimientos específicos de misión. NASA-STD-3001 exige que las capacidades médicas se adapten al riesgo, condiciones de misión, recursos, necesidades individuales y juicio médico; por tanto, una única biblioteca pública no puede conocer de antemano la configuración médica final de cada vehículo. citeturn8view5

Segundo, la autonomía aumenta en deep space precisamente porque la comunicación y evacuación empeoran, pero EIMO sigue siendo un Concept of Operations y una arquitectura de autonomía, no una publicación de todas las órdenes clínicas, dosificaciones y procedimientos operativos de futuras misiones. citeturn25search2

Tercero, en varios dominios la propia ciencia aún tiene incertidumbre. En inmunidad, por ejemplo, NASA documenta alteraciones biológicas pero también reconoce limitaciones al inferir riesgo clínico de exploración; en SANS se dispone de indicadores excelentes de monitorización, pero continúan preguntas sobre mecanismos y countermeasures; en cognición, cambios de rendimiento pueden cuantificarse longitudinalmente sin que exista un único cutpoint diagnóstico universal. citeturn19view0turn15view0turn25search18

Por eso el objetivo correcto de **“VIGILE integral”** no es:

> diagnostica y trata autónomamente todas las enfermedades.

Es:

> **representa de forma integral el estado de salud y contexto del astronauta; previene, monitoriza, detecta, integra señales multisistema, conduce evaluaciones, reconoce urgencia, recupera evidencia y ejecuta únicamente las decisiones clínicas que estén suficientemente documentadas y autorizadas.**

Eso permite abarcar cardiovascular, muscular, óseo, neuro-ocular, sensorimotor, sueño, cognición, behavioral health, inmunidad, infecciones, renal, nutrición, respiratorio, farmacología, radiación, ambiente, emergencias y demás dominios sin perder rigor.

El principal cuello de botella a partir de ahora **ya no debería ser otro Deep Research general**. Los vacíos futuros deberían surgir de manera concreta durante el desarrollo, por ejemplo:

```text
Codex: “Para C-RENAL-STONE me falta un criterio autorizado de X”
→ búsqueda puntual de X

Codex: “Necesito definir el QC mínimo del sensor Y”
→ documentación del dispositivo Y

Codex: “El protocol engine necesita saber quién puede autorizar Z”
→ mission authority specification

Codex: “Quiero validar R-SANS-OCT con dataset real”
→ dataset/access request específico
```

Eso es exactamente el punto al que queríamos llegar: **pasar de “seguir buscando medicina espacial” a implementar, probar y cerrar gaps concretos.**

Las funciones deliberadamente bloqueadas en esta versión son principalmente dosificación farmacológica autónoma, anticoagulación autónoma, tratamiento psiquiátrico autónomo, selección autónoma de procedimientos invasivos, tratamiento médico autónomo de exposición radiológica aguda y cualquier intervención de alta consecuencia cuya autorización operacional no esté incorporada explícitamente. El Evidence Report farmacológico de NASA, por ejemplo, se centra principalmente en estabilidad y shelf life de medicamentos y no resuelve por sí solo las incertidumbres generales de PK/PD en vuelo espacial. citeturn14view4

Por último, la validación deberá progresar por etapas:

```text
source verification
        ↓
schema + unit tests
        ↓
boundary tests
        ↓
synthetic scenarios
        ↓
retrospective public/approved datasets
        ↓
medical expert review
        ↓
analog-environment tests
        ↓
human-factors testing
        ↓
mission-authorized protocol integration
        ↓
independent verification / safety case
        ↓
prospective operational validation
```

Hasta que esas etapas existan, VIGILE debe describirse honestamente como un **research-grade, evidence-traceable autonomous health decision-support prototype**, no como un sistema clínico NASA validado.

**Entregable principal:** [VIGILE_FINAL_BIOMEDICAL_KNOWLEDGE.zip](ARCHIVO_ORIGINAL_NO_RECUPERADO). El archivo que debe leer primero Codex después del README es [VIGILE_BIOMEDICAL_IMPLEMENTATION_HANDOFF_FOR_CODEX.md](ARCHIVO_ORIGINAL_NO_RECUPERADO).