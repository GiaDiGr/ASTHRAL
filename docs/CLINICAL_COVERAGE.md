# Cobertura clínica real

Las 44 condiciones y sus 11 estados de evidencia se importan exactamente. ES no significa que VIGILE haya implementado o validado esa etapa clínica.

Software común disponible: registro/monitorización, calidad, baselines y tendencias; hallazgos y observaciones humanas separados de hipótesis; solicitud de evaluación; episodios; registro humano de recuperación/seguimiento. Diagnóstico, triaje automatizado, tratamiento y pronóstico individual están bloqueados. No hay protocolo terapéutico autorizado.

| Condición | Descripción | Comparadores de simulación asociados |
|---|---|---|
| C001 | Capacidad aeróbica reducida / fisiología cardiovascular | VIGILE-AER-001, VIGILE-AER-002, VIGILE-AER-003 |
| C002 | Pérdida de tamaño/fuerza/resistencia muscular / muscular | VIGILE-MUS-001, VIGILE-MUS-002 |
| C003 | Pérdida ósea y riesgo de fractura / óseo | VIGILE-BONE-001 |
| C004 | Desacondicionamiento cardiovascular / cardiovascular | Sin regla numérica activada |
| C005 | Intolerancia ortostática / cardiovascular-autonómica | Sin regla numérica activada |
| C006 | Tromboembolismo venoso / cardiovascular-hematológico | Sin regla numérica activada |
| C007 | Arritmia/evento cardiovascular agudo / cardiovascular-emergencias | Sin regla numérica activada |
| C008 | Redistribución de fluidos/hipovolemia relativa / cardiovascular | Sin regla numérica activada |
| C009 | SANS / neuro-oftalmología | Sin regla numérica activada |
| C010 | Space Motion Sickness / neurovestibular | Sin regla numérica activada |
| C011 | Deterioro sensorimotor/postural/locomotor / sensorimotor | Sin regla numérica activada |
| C012 | Pérdida de sueño / medicina del sueño | Sin regla numérica activada |
| C013 | Desincronización circadiana / sueño | Sin regla numérica activada |
| C014 | Fatiga y sobrecarga de trabajo / factores humanos | Sin regla numérica activada |
| C015 | Deterioro cognitivo funcional / neurocognición | Sin regla numérica activada |
| C016 | Cambios conductuales/psiquiátricos / salud conductual | Sin regla numérica activada |
| C017 | Deterioro de trabajo en equipo/adaptación psicosocial / factores humanos | Sin regla numérica activada |
| C018 | Alteración de respuesta inmunitaria / inmunología | Sin regla numérica activada |
| C019 | Reactivación viral latente / infeccioso-inmunológico | Sin regla numérica activada |
| C020 | Infección/host–microorganism interaction / infeccioso | Sin regla numérica activada |
| C021 | Formación de cálculos renales / nefro-urología | Sin regla numérica activada |
| C022 | Retención urinaria / urología | Sin regla numérica activada |
| C023 | Nutrición/energía inadecuadas / nutrición-metabolismo | VIGILE-NUT-001 |
| C024 | Deshidratación/desequilibrio hidroelectrolítico / nutrición-renal | Sin regla numérica activada |
| C025 | Enfermedad gastrointestinal aguda / gastroenterología | Sin regla numérica activada |
| C026 | Hipoxia / respiratorio-ambiental | VIGILE-ENV-001, VIGILE-ENV-003 |
| C027 | Exposición nominal/crónica a CO₂ / ambiental-respiratorio-neurológico | VIGILE-ENV-002 |
| C028 | Exposición a sustancias tóxicas / toxicología | Sin regla numérica activada |
| C029 | Exposición a polvo celestial/lunar / ocupacional-respiratorio | Sin regla numérica activada |
| C030 | Enfermedad por descompresión / aeroespacial | VIGILE-ENV-003 |
| C031 | Barotrauma/ear-sinus block / ORL | VIGILE-ENV-004 |
| C032 | Exposición acumulada a radiación ionizante/carcinogénesis / radiobiología | VIGILE-RAD-001, VIGILE-RAD-002, VIGILE-RAD-003, VIGILE-RAD-004 |
| C033 | Síndrome/efectos agudos de radiación / emergencias-radiobiología | Sin regla numérica activada |
| C034 | Radiación no ionizante / ambiental | Sin regla numérica activada |
| C035 | Pérdida auditiva/exposición acústica / audiología | Sin regla numérica activada |
| C036 | Lesión por cargas dinámicas / trauma | Sin regla numérica activada |
| C037 | Lesión/rendimiento comprometido durante EVA / medicina EVA | Sin regla numérica activada |
| C038 | Trauma, heridas y fractura aguda / emergencias | Sin regla numérica activada |
| C039 | Patología/emergencia dental / odontología | Sin regla numérica activada |
| C040 | Medicamento ineficaz o tóxico / farmacología | Sin regla numérica activada |
| C041 | Infección respiratoria/inhalación de humo / respiratorio-emergencias | Sin regla numérica activada |
| C042 | Choque eléctrico / emergencias | Sin regla numérica activada |
| C043 | Incapacidad de egress/tarea tras transición de gravedad / rendimiento | Sin regla numérica activada |
| C044 | Alteración dermatológica/infección cutánea / dermatología-inmunología | Sin regla numérica activada |

Etapas originales: prevention, monitoring, data_quality, detection, assessment, differential_diagnosis, triage, intervention_authorized, recovery, follow_up, prognosis. Ver matriz original; se mantiene NA, NPA, RV, RO, ES y RMA sin convertirlos en permisos.

Las doce relaciones multisistema se conservan; la asociación requiere selección explícita, coincidencia de sujeto/misión y ventana configurada. Los grupos Cxxx son candidatos de ingeniería y las salidas RESEARCH_ONLY no infieren causalidad. MSI05 no incluye un detector de adherencia a ejercicio; MSI10 no incluye gestión farmacológica real.
