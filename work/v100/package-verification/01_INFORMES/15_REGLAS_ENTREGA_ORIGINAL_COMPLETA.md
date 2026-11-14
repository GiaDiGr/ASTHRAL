# VIGILE — Deep Research, PARTE 1: catálogo de reglas computables

## Alcance, auditoría y versión de referencia

Esta entrega reconstruye **quince reglas computables de alta confianza directamente desde documentación primaria NASA actualmente vigente**, en vez de fingir que puedo recuperar exactamente el contenido del ZIP inaccesible. El encargo original exige precisamente eso: si un artefacto previo no existe o no puede recuperarse, debe reconstruirse desde evidencia verificada y no inventarse para mantener una cantidad prometida. fileciteturn0file0

La base normativa verificada para esta parte es **NASA-STD-3001 Volume 1, Revision C**, activa y fechada el 15 de septiembre de 2023, y **NASA-STD-3001 Volume 2, Revision F**, activa y fechada el 14 de julio de 2026. Por tanto, VIGILE debe fijar explícitamente estas revisiones en su registro de evidencia; no conviene mezclar valores extraídos de Technical Briefs antiguos con requisitos modificados posteriormente. citeturn16view0turn16view1

Hay además varias correcciones importantes respecto de información que había aparecido en iteraciones anteriores del proyecto:

| Tema | Resultado de la auditoría actual |
|---|---|
| Nutrición | **V1 4020 Rev. C exige proporcionar el 100 %**, no el 90 %, de los requerimientos calculados de nutrientes y energía. citeturn17view4turn21view2 |
| CO₂ | **V2 6004 Rev. F se refiere al promedio de una hora ≤3 mmHg**, no a cada lectura instantánea; los límites off-nominal se dejan a requisitos inferiores específicos de misión. citeturn17view6turn22view0 |
| Registro atmosférico | V2 6020 Rev. F dice **registro automático durante operaciones tripuladas** de presión, humedad, temperatura, ppO₂ y ppCO₂ por compartimento habitable aislable; no publica en esa cláusula una frecuencia fija de muestreo que podamos inventar. citeturn25view0turn25view1 |
| DCS | La Rev. F actual de V2 6008 utiliza **<4 % de probabilidad de DCS con 95 % de confianza para validación en cámara terrestre** y especifica que ese estándar de validación no es para uso directo en vuelo; esto sustituye referencias anteriores a otros porcentajes procedentes de versiones previas. citeturn22view2 |
| BMD | 95 %/90 % son objetivos normativos de mantenimiento de BMD, **no un algoritmo de diagnóstico individual de fractura**. El Evidence Report de NASA señala además que DXA no captura toda la pérdida y recuperación ósea de vuelos largos y que QCT aporta información complementaria. citeturn17view3turn18view0turn19view0 |
| Radiación | 600 mSv, 250 mSv, 20 mSv/año de misión y 1,3/0,9 mSv/día tienen **contextos de aplicación diferentes** y no deben colapsarse en una única alarma clínica. citeturn24view0turn24view1turn24view2turn24view3 |

Estas quince reglas no representan las únicas reglas que tendrá VIGILE. Son las que, en esta primera entrega, tienen suficiente definición pública para convertirse en comparadores determinísticos sin inventar parámetros. Por ejemplo, NASA exige monitorizar cognición, salud conductual, hematología e inmunología, pero no publica en NASA-STD-3001 un único conjunto universal de valores numéricos que pueda introducirse limpiamente en el motor como si fueran umbrales diagnósticos. Esa clase de reglas debe quedar parametrizada o bloqueada hasta la especificación de misión, en lugar de fabricar números. citeturn16view2

## Esquema común y semántica del motor

Para estas reglas, Codex debe separar **cinco conceptos que nunca deben fusionarse**:

`rule_result` indica si los datos cumplen un requisito concreto.

`data_quality_status` indica si los datos son utilizables.

`clinical_assessment_status` representa una evaluación médica posterior.

`evidence_status` expresa el nivel de respaldo de la regla.

`authorization_status` determina si el motor puede únicamente evaluar, o también iniciar una acción.

Por tanto, un `FAIL_REQUIREMENT` **no significa automáticamente** `CRITICAL`, enfermedad, diagnóstico, incapacidad para la misión ni necesidad de un tratamiento. La propia justificación de la tabla de fuerza de NASA reconoce que una persona por debajo del estándar podría realizar determinadas tareas, aunque potencialmente necesite más tiempo o recursos. citeturn17view1

El objeto común que debería utilizar Codex es:

```json
{
  "rule_schema_version": "1.0.0",
  "required_fields": [
    "rule_id",
    "rule_version",
    "title",
    "domain",
    "condition_id",
    "purpose",
    "rule_kind",
    "evidence_class",
    "evidence_status",
    "software_validation_status",
    "authorization",
    "applicability",
    "inputs",
    "derived_variables",
    "logic",
    "thresholds",
    "temporal_window",
    "confounders",
    "missing_data_policy",
    "data_quality_policy",
    "output",
    "severity_semantics",
    "follow_up",
    "source_locators",
    "test_cases"
  ],
  "rule_results": [
    "PASS",
    "FAIL_REQUIREMENT",
    "INCONCLUSIVE",
    "NOT_APPLICABLE",
    "REQUIRES_VALIDATION",
    "REQUIRES_MISSION_AUTHORIZATION"
  ],
  "data_quality_states": [
    "ACCEPTABLE",
    "DEGRADED",
    "INVALID",
    "UNKNOWN"
  ],
  "clinical_assessment_states": [
    "NOT_DETERMINED_BY_RULE",
    "ASSESSMENT_REQUIRED",
    "INCONCLUSIVE",
    "HUMAN_REVIEW_REQUIRED"
  ],
  "evidence_classes": [
    "NASA_STANDARD",
    "NASA_OPERATIONAL_PROCEDURE",
    "SPACEFLIGHT_PRIMARY_EVIDENCE",
    "SPACEFLIGHT_EVIDENCE_REPORT",
    "ANALOG_EVIDENCE",
    "TERRESTRIAL_CLINICAL_GUIDELINE",
    "ENGINEERING_CHOICE",
    "RESEARCH_HYPOTHESIS"
  ],
  "authorization_states": [
    "AUTO_EVALUATION_ALLOWED",
    "REQUIRES_MISSION_AUTHORIZATION",
    "REQUIRES_MEDICAL_AUTHORIZATION",
    "RESEARCH_ONLY"
  ],
  "global_guardrails": {
    "standard_failure_is_not_diagnosis": true,
    "clinical_severity_separate_from_rule_result": true,
    "missing_required_input_returns_inconclusive": true,
    "invalid_data_returns_inconclusive": true,
    "unvalidated_unit_conversion_forbidden": true,
    "llm_can_modify_rule": false,
    "llm_can_modify_threshold": false,
    "llm_can_authorize_treatment": false,
    "autonomous_drug_dosing_from_these_rules": false
  }
}
```

Esta separación también encaja con los requisitos de NASA sobre conservar los resultados de monitorización en formato permanente y recuperable para análisis de tendencias y proteger los registros médicos durante almacenamiento y transmisión. citeturn17view13turn17view14

## Reglas fisiológicas, musculoesqueléticas y nutricionales

Las primeras siete reglas proceden de las secciones de rendimiento humano de NASA-STD-3001 Volume 1 Rev. C. NASA fija 32,9 mL/min/kg para EVA en microgravedad, 36,5 mL/min/kg para EVA de superficie extraterrestre y ≥80 % del baseline preflight para capacidad aeróbica en misión. La norma también establece la tabla preflight de fuerza, ≥80 % del baseline para fuerza en vuelo, los objetivos 95/90 % de BMD y el suministro del 100 % del requerimiento nutricional y energético calculado. citeturn23view0turn17view0turn17view1turn17view2turn17view3turn17view4

```json
[
  {
    "rule_id": "VIGILE-AER-001",
    "rule_version": "1.0.0",
    "title": "Microgravity EVA in-mission VO2max requirement",
    "domain": "CARDIORESPIRATORY_FITNESS",
    "condition_id": "AEROBIC_CAPACITY_FOR_MICROGRAVITY_EVA",
    "purpose": "Evaluate compliance with the minimum in-mission VO2max required for missions involving microgravity EVA.",
    "rule_kind": "STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "clinical_interpretation": "REQUIRES_MEDICAL_AUTHORIZATION",
      "treatment": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "mission_phase": ["IN_MISSION"],
      "required_context": {
        "microgravity_eva_planned_or_required": true
      },
      "otherwise": "NOT_APPLICABLE"
    },
    "inputs": [
      {
        "name": "vo2max_relative",
        "type": "number",
        "canonical_unit": "mL/min/kg",
        "required": true
      },
      {
        "name": "microgravity_eva_planned_or_required",
        "type": "boolean",
        "required": true
      },
      {
        "name": "measurement_method",
        "type": "enum",
        "values": ["DIRECT", "INDIRECT"],
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "preconditions": [
        "microgravity_eva_planned_or_required == true",
        "data_quality_status == ACCEPTABLE",
        "vo2max_relative is not null"
      ],
      "decision": [
        {
          "when": "vo2max_relative >= 32.9",
          "result": "PASS"
        },
        {
          "when": "vo2max_relative < 32.9",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "vo2max_relative_minimum": {
        "value": 32.9,
        "unit": "mL/min/kg",
        "operator": ">="
      }
    },
    "temporal_window": {
      "type": "CURRENT_VALID_IN_MISSION_ASSESSMENT",
      "fixed_sampling_frequency_in_source": false
    },
    "confounders": [
      "measurement_method",
      "measurement_quality",
      "body_mass_used_for_relative_VO2",
      "temporary illness",
      "exercise-related acute effects"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Do not evaluate compliance from INVALID or UNKNOWN quality data.",
    "output": {
      "primary": "rule_result",
      "clinical_assessment_status": "NOT_DETERMINED_BY_RULE",
      "diagnosis": null
    },
    "severity_semantics": {
      "on_failure": "STANDARD_NONCOMPLIANCE",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Flag for mission/medical review.",
      "Evaluate together with VIGILE-AER-003 and operational task requirements.",
      "Do not autonomously diagnose cardiovascular disease or prescribe treatment."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4001",
        "section": "4.1.1",
        "printed_page": 32,
        "pdf_page_index_0based": 31,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "AER001-T01",
        "synthetic": true,
        "inputs": {
          "vo2max_relative": 33.0,
          "microgravity_eva_planned_or_required": true,
          "measurement_method": "DIRECT",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "AER001-T02",
        "synthetic": true,
        "inputs": {
          "vo2max_relative": 32.8,
          "microgravity_eva_planned_or_required": true,
          "measurement_method": "DIRECT",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "AER001-T03",
        "synthetic": true,
        "inputs": {
          "vo2max_relative": 30.0,
          "microgravity_eva_planned_or_required": false,
          "measurement_method": "INDIRECT",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "NOT_APPLICABLE"
      }
    ]
  },
  {
    "rule_id": "VIGILE-AER-002",
    "rule_version": "1.0.0",
    "title": "Extraterrestrial surface EVA in-mission VO2max requirement",
    "domain": "CARDIORESPIRATORY_FITNESS",
    "condition_id": "AEROBIC_CAPACITY_FOR_SURFACE_EVA",
    "purpose": "Evaluate compliance with the minimum in-mission VO2max required for extraterrestrial surface EVA.",
    "rule_kind": "STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "clinical_interpretation": "REQUIRES_MEDICAL_AUTHORIZATION",
      "treatment": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "mission_phase": ["IN_MISSION"],
      "required_context": {
        "extraterrestrial_surface_eva_planned_or_required": true
      },
      "otherwise": "NOT_APPLICABLE"
    },
    "inputs": [
      {
        "name": "vo2max_relative",
        "type": "number",
        "canonical_unit": "mL/min/kg",
        "required": true
      },
      {
        "name": "extraterrestrial_surface_eva_planned_or_required",
        "type": "boolean",
        "required": true
      },
      {
        "name": "measurement_method",
        "type": "enum",
        "values": ["DIRECT", "INDIRECT"],
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "decision": [
        {
          "when": "extraterrestrial_surface_eva_planned_or_required == false",
          "result": "NOT_APPLICABLE"
        },
        {
          "when": "data_quality_status != ACCEPTABLE OR vo2max_relative is null",
          "result": "INCONCLUSIVE"
        },
        {
          "when": "vo2max_relative >= 36.5",
          "result": "PASS"
        },
        {
          "when": "vo2max_relative < 36.5",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "vo2max_relative_minimum": {
        "value": 36.5,
        "unit": "mL/min/kg",
        "operator": ">="
      }
    },
    "temporal_window": {
      "type": "CURRENT_VALID_IN_MISSION_ASSESSMENT",
      "fixed_sampling_frequency_in_source": false
    },
    "confounders": [
      "measurement_method",
      "measurement_quality",
      "body_mass",
      "temporary illness",
      "acute exercise effects"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Reject INVALID or UNKNOWN quality measurements.",
    "output": {
      "primary": "rule_result",
      "clinical_assessment_status": "NOT_DETERMINED_BY_RULE",
      "diagnosis": null
    },
    "severity_semantics": {
      "on_failure": "STANDARD_NONCOMPLIANCE",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Mission/medical review.",
      "Evaluate VIGILE-AER-003.",
      "Do not infer disease from this threshold alone."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4002",
        "section": "4.1.2",
        "printed_page": 33,
        "pdf_page_index_0based": 32,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "AER002-T01",
        "synthetic": true,
        "inputs": {
          "vo2max_relative": 36.5,
          "extraterrestrial_surface_eva_planned_or_required": true,
          "measurement_method": "DIRECT",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "AER002-T02",
        "synthetic": true,
        "inputs": {
          "vo2max_relative": 36.4,
          "extraterrestrial_surface_eva_planned_or_required": true,
          "measurement_method": "INDIRECT",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      }
    ]
  },
  {
    "rule_id": "VIGILE-AER-003",
    "rule_version": "1.0.0",
    "title": "In-mission aerobic capacity retention",
    "domain": "CARDIORESPIRATORY_FITNESS",
    "condition_id": "AEROBIC_DECONDITIONING",
    "purpose": "Evaluate preservation of aerobic capacity relative to the individual's pre-mission baseline.",
    "rule_kind": "BASELINE_RELATIVE_STANDARD",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "clinical_interpretation": "REQUIRES_MEDICAL_AUTHORIZATION",
      "treatment": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "mission_phase": ["IN_MISSION"],
      "baseline_required": true
    },
    "inputs": [
      {
        "name": "premission_aerobic_capacity",
        "type": "number",
        "required": true
      },
      {
        "name": "current_aerobic_capacity",
        "type": "number",
        "required": true
      },
      {
        "name": "measurement_unit",
        "type": "string",
        "required": true
      },
      {
        "name": "measurement_comparability",
        "type": "enum",
        "values": ["COMPARABLE", "NOT_COMPARABLE", "UNKNOWN"],
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [
      {
        "name": "aerobic_capacity_retention_percent",
        "formula": "100 * current_aerobic_capacity / premission_aerobic_capacity",
        "unit": "%"
      }
    ],
    "logic": {
      "preconditions": [
        "premission_aerobic_capacity > 0",
        "measurement_comparability == COMPARABLE",
        "data_quality_status == ACCEPTABLE"
      ],
      "decision": [
        {
          "when": "aerobic_capacity_retention_percent >= 80",
          "result": "PASS"
        },
        {
          "when": "aerobic_capacity_retention_percent < 80",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "retention_percent_minimum": {
        "value": 80,
        "unit": "%",
        "operator": ">="
      }
    },
    "temporal_window": {
      "baseline": "PRE_MISSION",
      "comparison": "IN_MISSION",
      "fixed_reassessment_interval_in_source": false
    },
    "confounders": [
      "non-comparable measurement protocols",
      "changes in body-mass normalization",
      "temporary disease",
      "acute exercise effects",
      "sensor or ergometer differences"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Baseline and current measurements must be sufficiently comparable under a mission-approved measurement protocol.",
    "output": {
      "primary": "rule_result",
      "derived": "aerobic_capacity_retention_percent",
      "clinical_assessment_status": "NOT_DETERMINED_BY_RULE"
    },
    "severity_semantics": {
      "on_failure": "PERMISSIBLE_OUTCOME_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Review trend and task-specific requirements.",
      "Evaluate VIGILE-AER-001 or VIGILE-AER-002 when applicable.",
      "Clinical assessment if deterioration is unexpected or symptomatic."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4003",
        "section": "4.1.3",
        "printed_page": 33,
        "pdf_page_index_0based": 32,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "AER003-T01",
        "synthetic": true,
        "inputs": {
          "premission_aerobic_capacity": 45.0,
          "current_aerobic_capacity": 36.0,
          "measurement_unit": "mL/min/kg",
          "measurement_comparability": "COMPARABLE",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected_retention_percent": 80.0,
        "expected": "PASS"
      },
      {
        "id": "AER003-T02",
        "synthetic": true,
        "inputs": {
          "premission_aerobic_capacity": 45.0,
          "current_aerobic_capacity": 35.9,
          "measurement_unit": "mL/min/kg",
          "measurement_comparability": "COMPARABLE",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "AER003-T03",
        "synthetic": true,
        "inputs": {
          "premission_aerobic_capacity": null,
          "current_aerobic_capacity": 35.0,
          "measurement_unit": "mL/min/kg",
          "measurement_comparability": "UNKNOWN",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "INCONCLUSIVE"
      }
    ]
  },
  {
    "rule_id": "VIGILE-MUS-001",
    "rule_version": "1.0.0",
    "title": "Pre-mission muscle strength requirement",
    "domain": "MUSCULOSKELETAL",
    "condition_id": "PREMISSION_FUNCTIONAL_STRENGTH",
    "purpose": "Evaluate pre-mission deadlift and bench-press strength against NASA mission-context requirements.",
    "rule_kind": "STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE_WITH_APPROVED_TEST_PROTOCOL",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "measurement_protocol": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_interpretation": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "mission_phase": ["PRE_MISSION"],
      "mission_profiles": [
        "MINIMUM",
        "MICROGRAVITY_EVA",
        "EXTRATERRESTRIAL_SURFACE_EVA",
        "UNAIDED_TERRESTRIAL_EGRESS"
      ]
    },
    "inputs": [
      {
        "name": "body_weight",
        "type": "number",
        "canonical_unit": "kg_equivalent",
        "required": true
      },
      {
        "name": "deadlift_strength_value",
        "type": "number",
        "canonical_unit": "kg_equivalent",
        "required": true
      },
      {
        "name": "bench_press_strength_value",
        "type": "number",
        "canonical_unit": "kg_equivalent",
        "required": true
      },
      {
        "name": "applicable_mission_profiles",
        "type": "array",
        "required": true
      },
      {
        "name": "approved_strength_test_protocol",
        "type": "boolean",
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [
      {
        "name": "deadlift_body_weight_ratio",
        "formula": "deadlift_strength_value / body_weight"
      },
      {
        "name": "bench_press_body_weight_ratio",
        "formula": "bench_press_strength_value / body_weight"
      }
    ],
    "thresholds": {
      "MINIMUM": {
        "deadlift_body_weight_ratio": 1.0,
        "bench_press_body_weight_ratio": 0.7
      },
      "MICROGRAVITY_EVA": {
        "deadlift_body_weight_ratio": 1.3,
        "bench_press_body_weight_ratio": 0.8
      },
      "EXTRATERRESTRIAL_SURFACE_EVA": {
        "deadlift_body_weight_ratio": 1.6,
        "bench_press_body_weight_ratio": 1.0
      },
      "UNAIDED_TERRESTRIAL_EGRESS": {
        "deadlift_body_weight_ratio": 1.3,
        "bench_press_body_weight_ratio": 0.7
      }
    },
    "logic": {
      "preconditions": [
        "body_weight > 0",
        "approved_strength_test_protocol == true",
        "data_quality_status == ACCEPTABLE"
      ],
      "decision": [
        {
          "when": "all measured exercise ratios meet or exceed every applicable mission-profile threshold",
          "result": "PASS"
        },
        {
          "when": "one or more required ratios are below an applicable threshold",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "temporal_window": {
      "type": "PRE_MISSION_ASSESSMENT"
    },
    "confounders": [
      "test protocol",
      "technique",
      "injury",
      "pain",
      "equipment differences",
      "body-weight measurement error"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Do not infer that the table specifies a particular unmentioned testing protocol such as one-repetition maximum. Use a program-approved protocol.",
    "output": {
      "primary": "rule_result",
      "site_results": ["deadlift", "bench_press"],
      "clinical_assessment_status": "NOT_DETERMINED_BY_RULE"
    },
    "severity_semantics": {
      "on_failure": "FITNESS_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Review mission task demands and test validity.",
      "Do not classify a person as diseased solely because a threshold is not met."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4023",
        "section": "4.6.1",
        "table": "Table 4.6-1",
        "printed_page": 38,
        "pdf_page_index_0based": 37,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "MUS001-T01",
        "synthetic": true,
        "inputs": {
          "body_weight": 80,
          "deadlift_strength_value": 104,
          "bench_press_strength_value": 64,
          "applicable_mission_profiles": ["MINIMUM", "MICROGRAVITY_EVA"],
          "approved_strength_test_protocol": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "MUS001-T02",
        "synthetic": true,
        "inputs": {
          "body_weight": 80,
          "deadlift_strength_value": 127,
          "bench_press_strength_value": 80,
          "applicable_mission_profiles": ["EXTRATERRESTRIAL_SURFACE_EVA"],
          "approved_strength_test_protocol": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "MUS001-T03",
        "synthetic": true,
        "inputs": {
          "body_weight": 80,
          "deadlift_strength_value": 128,
          "bench_press_strength_value": 80,
          "applicable_mission_profiles": ["EXTRATERRESTRIAL_SURFACE_EVA"],
          "approved_strength_test_protocol": false,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "REQUIRES_MISSION_AUTHORIZATION"
      }
    ]
  },
  {
    "rule_id": "VIGILE-MUS-002",
    "rule_version": "1.0.0",
    "title": "In-mission skeletal muscle strength retention",
    "domain": "MUSCULOSKELETAL",
    "condition_id": "MUSCLE_STRENGTH_DECONDITIONING",
    "purpose": "Evaluate in-mission muscle-strength preservation relative to baseline.",
    "rule_kind": "BASELINE_RELATIVE_STANDARD",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "clinical_interpretation": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "mission_phase": ["IN_MISSION"],
      "baseline_required": true
    },
    "inputs": [
      {
        "name": "baseline_strength",
        "type": "number",
        "required": true
      },
      {
        "name": "current_strength",
        "type": "number",
        "required": true
      },
      {
        "name": "test_id",
        "type": "string",
        "required": true
      },
      {
        "name": "measurement_comparability",
        "type": "enum",
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [
      {
        "name": "strength_retention_percent",
        "formula": "100 * current_strength / baseline_strength",
        "unit": "%"
      }
    ],
    "logic": {
      "preconditions": [
        "baseline_strength > 0",
        "measurement_comparability == COMPARABLE",
        "data_quality_status == ACCEPTABLE"
      ],
      "decision": [
        {
          "when": "strength_retention_percent >= 80",
          "result": "PASS"
        },
        {
          "when": "strength_retention_percent < 80",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "retention_percent_minimum": 80
    },
    "temporal_window": {
      "baseline": "PRE_MISSION_OR_APPROVED_BASELINE",
      "comparison": "IN_MISSION",
      "fixed_reassessment_interval_in_source": false
    },
    "confounders": [
      "different muscle groups",
      "different exercises",
      "different equipment",
      "injury",
      "fatigue",
      "pain",
      "test-learning effects"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Never aggregate unlike tests into one retention ratio without a separately validated model.",
    "output": {
      "primary": "rule_result",
      "derived": "strength_retention_percent",
      "clinical_assessment_status": "NOT_DETERMINED_BY_RULE"
    },
    "severity_semantics": {
      "on_failure": "PERMISSIBLE_OUTCOME_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Review longitudinal strength trend.",
      "Review exercise-countermeasure adherence and measurement context.",
      "Medical evaluation if accompanied by injury, pain, focal weakness or unexpected deterioration."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4024",
        "section": "4.6.2",
        "printed_page": 38,
        "pdf_page_index_0based": 37,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "MUS002-T01",
        "synthetic": true,
        "inputs": {
          "baseline_strength": 100,
          "current_strength": 80,
          "test_id": "TEST_A",
          "measurement_comparability": "COMPARABLE",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected_retention_percent": 80,
        "expected": "PASS"
      },
      {
        "id": "MUS002-T02",
        "synthetic": true,
        "inputs": {
          "baseline_strength": 100,
          "current_strength": 79.9,
          "test_id": "TEST_A",
          "measurement_comparability": "COMPARABLE",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      }
    ]
  },
  {
    "rule_id": "VIGILE-BONE-001",
    "rule_version": "1.0.0",
    "title": "Bone mineral density retention requirement",
    "domain": "BONE",
    "condition_id": "SPACEFLIGHT_ASSOCIATED_BMD_LOSS",
    "purpose": "Evaluate BMD retention against NASA permissible outcome targets by anatomical site.",
    "rule_kind": "BASELINE_RELATIVE_STANDARD",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "fracture_diagnosis": "REQUIRES_MEDICAL_AUTHORIZATION",
      "pharmacologic_treatment": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "baseline_required": true,
      "anatomical_sites": [
        "TOTAL_HIP",
        "LUMBAR_SPINE_L1_L4",
        "FEMORAL_NECK"
      ]
    },
    "inputs": [
      {
        "name": "premission_bmd",
        "type": "map_anatomical_site_to_number",
        "canonical_unit": "g/cm2_or_validated_equivalent",
        "required": true
      },
      {
        "name": "current_bmd",
        "type": "map_anatomical_site_to_number",
        "canonical_unit": "same_as_baseline",
        "required": true
      },
      {
        "name": "measurement_comparability",
        "type": "enum",
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [
      {
        "name": "bmd_retention_percent_by_site",
        "formula": "100 * current_bmd[site] / premission_bmd[site]",
        "unit": "%"
      }
    ],
    "thresholds": {
      "TOTAL_HIP": {
        "minimum_retention_percent": 95
      },
      "LUMBAR_SPINE_L1_L4": {
        "minimum_retention_percent": 95
      },
      "FEMORAL_NECK": {
        "minimum_retention_percent": 90
      }
    },
    "logic": {
      "preconditions": [
        "valid baseline exists for anatomical site",
        "current and baseline measurements are comparable",
        "data_quality_status == ACCEPTABLE"
      ],
      "decision": [
        {
          "when": "all required available sites meet their site-specific thresholds",
          "result": "PASS"
        },
        {
          "when": "one or more valid required sites are below threshold",
          "result": "FAIL_REQUIREMENT"
        },
        {
          "when": "a required comparison cannot be made",
          "result": "INCONCLUSIVE"
        }
      ]
    },
    "temporal_window": {
      "baseline": "PRE_MISSION",
      "comparison": "WHEN_A_COMPARABLE_MEASUREMENT_IS_AVAILABLE",
      "continuous_inflight_measurement_assumed": false
    },
    "confounders": [
      "scanner differences",
      "cross-calibration",
      "positioning",
      "region-of-interest differences",
      "measurement artifacts",
      "DXA limitations for trabecular bone recovery"
    ],
    "missing_data_policy": "Return site-specific results where possible and overall INCONCLUSIVE if a required site cannot be evaluated.",
    "data_quality_policy": "Require comparable acquisition and analysis. Do not substitute unrelated imaging measures without validation.",
    "output": {
      "primary": "rule_result",
      "site_results": true,
      "derived": "bmd_retention_percent_by_site",
      "fracture_risk": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "BMD_COUNTERMEASURE_TARGET_NOT_MET",
      "fracture_probability": "NOT_DETERMINED"
    },
    "follow_up": [
      "Review longitudinal BMD and relevant skeletal data.",
      "Do not infer individual fracture probability from this ratio alone.",
      "Additional QCT or biomechanical interpretation requires a separate validated pathway."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4027",
        "section": "4.7.2",
        "printed_page": 39,
        "pdf_page_index_0based": 38,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      },
      {
        "source_id": "NASA-HRP-FRACTURE-EVIDENCE-REPORT-2024",
        "use": "LIMITATION_AND_CONTEXT",
        "document_id": "20240005190",
        "printed_page": 6,
        "pdf_page_index_0based": 5,
        "url": "https://ntrs.nasa.gov/citations/20240005190"
      }
    ],
    "test_cases": [
      {
        "id": "BONE001-T01",
        "synthetic": true,
        "inputs": {
          "premission_bmd": {
            "TOTAL_HIP": 1.0,
            "LUMBAR_SPINE_L1_L4": 1.0,
            "FEMORAL_NECK": 1.0
          },
          "current_bmd": {
            "TOTAL_HIP": 0.95,
            "LUMBAR_SPINE_L1_L4": 0.96,
            "FEMORAL_NECK": 0.90
          },
          "measurement_comparability": "COMPARABLE",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "BONE001-T02",
        "synthetic": true,
        "inputs": {
          "premission_bmd": {
            "TOTAL_HIP": 1.0,
            "LUMBAR_SPINE_L1_L4": 1.0,
            "FEMORAL_NECK": 1.0
          },
          "current_bmd": {
            "TOTAL_HIP": 0.95,
            "LUMBAR_SPINE_L1_L4": 0.95,
            "FEMORAL_NECK": 0.899
          },
          "measurement_comparability": "COMPARABLE",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      }
    ]
  },
  {
    "rule_id": "VIGILE-NUT-001",
    "rule_version": "1.0.0",
    "title": "In-mission nutrient and energy provision requirement",
    "domain": "NUTRITION",
    "condition_id": "NUTRITIONAL_PROVISION_ADEQUACY",
    "purpose": "Evaluate whether the program provides 100% of each calculated nutrient and energy requirement.",
    "rule_kind": "STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE_AFTER_REQUIREMENTS_ARE_CALCULATED",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "requirement_calculation_method": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_diagnosis": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "mission_phase": ["IN_MISSION"]
    },
    "inputs": [
      {
        "name": "calculated_requirements",
        "type": "map_component_to_quantity",
        "required": true,
        "note": "Requirements must be calculated using an approved method considering age, sex, body mass, height and appropriate activity factor."
      },
      {
        "name": "provided_amounts",
        "type": "map_component_to_quantity",
        "required": true
      },
      {
        "name": "requirement_period",
        "type": "mission_configured_time_period",
        "required": true
      },
      {
        "name": "requirement_calculation_method_approved",
        "type": "boolean",
        "required": true
      }
    ],
    "derived_variables": [
      {
        "name": "provision_percent_by_component",
        "formula": "100 * provided_amount[component] / calculated_requirement[component]",
        "unit": "%"
      }
    ],
    "thresholds": {
      "minimum_provision_percent": 100
    },
    "logic": {
      "preconditions": [
        "calculated requirement > 0 for each evaluated component",
        "units are compatible",
        "requirement_calculation_method_approved == true"
      ],
      "decision": [
        {
          "when": "every required component has provision_percent >= 100",
          "result": "PASS"
        },
        {
          "when": "one or more required components have provision_percent < 100",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "temporal_window": {
      "type": "MISSION_CONFIGURED",
      "fixed_period_in_V1_4020": false
    },
    "confounders": [
      "incorrect nutritional requirement calculation",
      "incorrect activity factor",
      "changes in body mass",
      "mission-specific food availability"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Requirement and provision quantities must use compatible units and the same accounting period.",
    "output": {
      "primary": "rule_result",
      "derived": "provision_percent_by_component",
      "actual_consumption_assessment": "NOT_DETERMINED_BY_THIS_RULE",
      "nutrient_deficiency_diagnosis": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "PROVISION_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Identify deficient provision components.",
      "Recalculate requirements if body mass, activity or other relevant variables changed.",
      "Assess actual intake and biomarkers using separate nutrition pathways."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4020",
        "section": "4.5.2",
        "printed_page": 37,
        "pdf_page_index_0based": 36,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "NUT001-T01",
        "synthetic": true,
        "inputs": {
          "calculated_requirements": {
            "energy_kcal": 2500
          },
          "provided_amounts": {
            "energy_kcal": 2500
          },
          "requirement_period": "MISSION_DEFINED_DAY",
          "requirement_calculation_method_approved": true
        },
        "expected": "PASS"
      },
      {
        "id": "NUT001-T02",
        "synthetic": true,
        "inputs": {
          "calculated_requirements": {
            "energy_kcal": 2500
          },
          "provided_amounts": {
            "energy_kcal": 2499
          },
          "requirement_period": "MISSION_DEFINED_DAY",
          "requirement_calculation_method_approved": true
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "NUT001-T03",
        "synthetic": true,
        "inputs": {
          "calculated_requirements": null,
          "provided_amounts": {
            "energy_kcal": 2500
          },
          "requirement_period": "MISSION_DEFINED_DAY",
          "requirement_calculation_method_approved": false
        },
        "expected": "INCONCLUSIVE"
      }
    ]
  }
]
```

El requisito de fuerza debe implementarse con especial cuidado: la tabla de NASA da relaciones respecto del peso corporal, pero no autoriza a VIGILE a inventar un protocolo de ensayo no descrito. Además, el estándar reconoce que el diseño del traje y las demandas de tarea pueden modificar la interpretación operacional. citeturn17view1turn21view4

En hueso, la separación entre **cumplimiento de V1 4027** y **predicción de fractura** es deliberada. El informe de riesgo de fractura de NASA de 2024 indica que el seguimiento DXA preflight/postflight no describe por completo determinados cambios y recuperación en vuelos largos; QCT y modelos biomecánicos aportan información adicional, mientras que el modelo PRA IMPACT seguía en desarrollo en ese informe. citeturn18view0turn18view1turn19view0

Y en nutrición, el código debe representar exactamente lo que dice la norma: **“proporcionar”** el 100 % del requerimiento calculado no equivale a demostrar que el astronauta ingirió, absorbió o metabolizó el 100 %. Una futura ruta nutricional deberá comparar provisión, consumo registrado, cambios de masa corporal, síntomas y biomarcadores como conceptos separados. citeturn17view4turn21view2

## Reglas de exposición radiológica

NASA-STD-3001 Rev. C distingue al menos cuatro comparaciones que VIGILE no debe confundir: el límite efectivo de carrera de 600 mSv; el evento solar de referencia por debajo de 250 mSv; la exposición debida a tecnologías nucleares por debajo de 20 mSv por año de misión prorrateado; y, para determinados sistemas de más de 60 días, tasas GCR inferiores a 1,3 mSv/día en espacio libre y 0,9 mSv/día en superficie planetaria. citeturn23view2turn24view1turn17view11turn24view3

```json
[
  {
    "rule_id": "VIGILE-RAD-001",
    "rule_version": "1.0.0",
    "title": "Career spaceflight effective radiation dose limit",
    "domain": "RADIATION",
    "condition_id": "CUMULATIVE_SPACEFLIGHT_RADIATION_EXPOSURE",
    "purpose": "Evaluate career NASA effective dose from spaceflight radiation against the career PEL.",
    "rule_kind": "SPACE_PERMISSIBLE_EXPOSURE_LIMIT",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE_WITH_NASA_EFFECTIVE_DOSE_INPUT",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "dosimetry_conversion": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_action": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "population": "CREWMEMBER",
      "exposure_type": "SPACEFLIGHT_RADIATION"
    },
    "inputs": [
      {
        "name": "past_spaceflight_effective_dose",
        "type": "number",
        "canonical_unit": "mSv",
        "required": true
      },
      {
        "name": "projected_upcoming_mission_effective_dose",
        "type": "number",
        "canonical_unit": "mSv",
        "required_for": "MISSION_PLANNING"
      },
      {
        "name": "evaluation_mode",
        "type": "enum",
        "values": ["CURRENT_CAREER_RECORD", "MISSION_PLANNING"],
        "required": true
      },
      {
        "name": "dose_methodology",
        "type": "string",
        "required": true
      }
    ],
    "derived_variables": [
      {
        "name": "evaluated_career_effective_dose",
        "formula": "CURRENT_CAREER_RECORD: past_spaceflight_effective_dose; MISSION_PLANNING: past_spaceflight_effective_dose + projected_upcoming_mission_effective_dose",
        "unit": "mSv"
      }
    ],
    "logic": {
      "preconditions": [
        "dose values represent NASA effective dose appropriate to V1 4030",
        "no incompatible absorbed-dose units have been silently summed"
      ],
      "decision": [
        {
          "when": "evaluated_career_effective_dose < 600",
          "result": "PASS"
        },
        {
          "when": "evaluated_career_effective_dose >= 600",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "career_effective_dose": {
        "value": 600,
        "unit": "mSv",
        "operator": "<"
      }
    },
    "temporal_window": {
      "type": "CAREER_CUMULATIVE"
    },
    "confounders": [
      "incorrect dose-equivalent conversion",
      "incorrect NASA quality-factor application",
      "missing prior mission exposure",
      "mixing effective dose with organ absorbed dose"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Do not convert or combine mSv, mGy and mGy-Eq without a validated dosimetric method.",
    "output": {
      "primary": "rule_result",
      "derived": "evaluated_career_effective_dose",
      "radiation_injury_diagnosis": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "PEL_NONCOMPLIANCE",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "ALARA review.",
      "Mission radiation-protection review.",
      "Medical interpretation under authorized radiation-health protocol."
    ],
    "special_handling": {
      "medical_and_biomedical_research_exposure": "TRACK_IN_EXPOSURE_HISTORY_BUT_EXCLUDE_FROM_V1_4030_LIMIT_COMPARISON"
    },
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4030",
        "section": "4.8.2",
        "printed_pages": [40, 41],
        "pdf_page_indices_0based": [39, 40],
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "RAD001-T01",
        "synthetic": true,
        "inputs": {
          "past_spaceflight_effective_dose": 599.9,
          "projected_upcoming_mission_effective_dose": 0,
          "evaluation_mode": "CURRENT_CAREER_RECORD",
          "dose_methodology": "NASA_APPROVED"
        },
        "expected": "PASS"
      },
      {
        "id": "RAD001-T02",
        "synthetic": true,
        "inputs": {
          "past_spaceflight_effective_dose": 600.0,
          "projected_upcoming_mission_effective_dose": 0,
          "evaluation_mode": "CURRENT_CAREER_RECORD",
          "dose_methodology": "NASA_APPROVED"
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "RAD001-T03",
        "synthetic": true,
        "inputs": {
          "past_spaceflight_effective_dose": 450,
          "projected_upcoming_mission_effective_dose": 160,
          "evaluation_mode": "MISSION_PLANNING",
          "dose_methodology": "NASA_APPROVED"
        },
        "expected": "FAIL_REQUIREMENT"
      }
    ]
  },
  {
    "rule_id": "VIGILE-RAD-002",
    "rule_version": "1.0.0",
    "title": "Design-reference Solar Particle Event effective-dose requirement",
    "domain": "RADIATION",
    "condition_id": "SOLAR_PARTICLE_EVENT_PROTECTION",
    "purpose": "Evaluate design protection against NASA's design-reference SPE environment.",
    "rule_kind": "DESIGN_EXPOSURE_REQUIREMENT",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE_WITH_APPROVED_MODEL",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "dosimetry_model": "REQUIRES_MISSION_AUTHORIZATION",
      "acute_event_triage": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "context": "DESIGN_REFERENCE_SOLAR_PARTICLE_EVENT",
      "reference_environment": "SUM_OF_OCTOBER_1989_EVENTS"
    },
    "inputs": [
      {
        "name": "modeled_design_reference_spe_effective_dose",
        "type": "number",
        "canonical_unit": "mSv",
        "required": true
      },
      {
        "name": "reference_environment_verified",
        "type": "boolean",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "decision": [
        {
          "when": "reference_environment_verified != true",
          "result": "INCONCLUSIVE"
        },
        {
          "when": "modeled_design_reference_spe_effective_dose < 250",
          "result": "PASS"
        },
        {
          "when": "modeled_design_reference_spe_effective_dose >= 250",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "effective_dose": {
        "value": 250,
        "unit": "mSv",
        "operator": "<"
      }
    },
    "temporal_window": {
      "type": "DESIGN_REFERENCE_EVENT"
    },
    "confounders": [
      "shielding model",
      "crew location",
      "reference spectrum",
      "geometry",
      "dose methodology"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Only evaluate using an approved model of the specified reference SPE environment.",
    "output": {
      "primary": "rule_result",
      "acute_radiation_syndrome_diagnosis": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "DESIGN_RADIATION_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Radiation-protection design review.",
      "Apply ALARA.",
      "Do not repurpose the 250 mSv design threshold as an autonomous in-flight clinical triage rule."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4031",
        "section": "4.8.3",
        "printed_page": 42,
        "pdf_page_index_0based": 41,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "RAD002-T01",
        "synthetic": true,
        "inputs": {
          "modeled_design_reference_spe_effective_dose": 249.9,
          "reference_environment_verified": true
        },
        "expected": "PASS"
      },
      {
        "id": "RAD002-T02",
        "synthetic": true,
        "inputs": {
          "modeled_design_reference_spe_effective_dose": 250.0,
          "reference_environment_verified": true
        },
        "expected": "FAIL_REQUIREMENT"
      }
    ]
  },
  {
    "rule_id": "VIGILE-RAD-003",
    "rule_version": "1.0.0",
    "title": "Nuclear-technology radiation exposure limit",
    "domain": "RADIATION",
    "condition_id": "NUCLEAR_TECHNOLOGY_IONIZING_EXPOSURE",
    "purpose": "Evaluate ionizing-radiation exposure attributable to onboard nuclear technologies against the mission-year limit.",
    "rule_kind": "SPACE_PERMISSIBLE_EXPOSURE_LIMIT",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE_AFTER_MISSION_PRORATION_DEFINITION",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "mission_year_proration_method": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_action": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "nuclear_technology_emitting_ionizing_radiation_present": true
    },
    "inputs": [
      {
        "name": "nuclear_technology_effective_dose",
        "type": "number",
        "canonical_unit": "mSv",
        "required": true
      },
      {
        "name": "mission_year_equivalent",
        "type": "number",
        "required": true,
        "note": "Must use the approved program convention for prorating/extrapolating mission duration."
      }
    ],
    "derived_variables": [
      {
        "name": "prorated_limit_mSv",
        "formula": "20 * mission_year_equivalent",
        "unit": "mSv"
      }
    ],
    "logic": {
      "preconditions": [
        "mission_year_equivalent > 0"
      ],
      "decision": [
        {
          "when": "nuclear_technology_effective_dose < prorated_limit_mSv",
          "result": "PASS"
        },
        {
          "when": "nuclear_technology_effective_dose >= prorated_limit_mSv",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "annualized_effective_dose": {
        "value": 20,
        "unit": "mSv/mission-year",
        "operator": "<"
      }
    },
    "temporal_window": {
      "type": "MISSION_DURATION_PRORATED"
    },
    "confounders": [
      "mission-year convention",
      "shielding",
      "time near source",
      "EVA fraction",
      "source geometry"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Do not silently assume 365 or 365.25 days as the mission-year convention unless the mission configuration explicitly defines it.",
    "output": {
      "primary": "rule_result",
      "derived": "prorated_limit_mSv",
      "clinical_assessment_status": "NOT_DETERMINED_BY_RULE"
    },
    "severity_semantics": {
      "on_failure": "NUCLEAR_TECHNOLOGY_RADIATION_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "ALARA and engineering review.",
      "Review source shielding and crew timeline.",
      "Medical evaluation under authorized radiation protocol if actual crew exposure is involved."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4032",
        "section": "4.8.4",
        "printed_pages": [43, 44],
        "pdf_page_indices_0based": [42, 43],
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "RAD003-T01",
        "synthetic": true,
        "inputs": {
          "nuclear_technology_effective_dose": 19.9,
          "mission_year_equivalent": 1.0
        },
        "expected": "PASS"
      },
      {
        "id": "RAD003-T02",
        "synthetic": true,
        "inputs": {
          "nuclear_technology_effective_dose": 20.0,
          "mission_year_equivalent": 1.0
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "RAD003-T03",
        "synthetic": true,
        "inputs": {
          "nuclear_technology_effective_dose": 10.0,
          "mission_year_equivalent": 0.5
        },
        "expected": "FAIL_REQUIREMENT",
        "reason": "The standard uses a strict less-than criterion."
      }
    ]
  },
  {
    "rule_id": "VIGILE-RAD-004",
    "rule_version": "1.0.0",
    "title": "Galactic Cosmic Radiation effective-dose-rate requirement",
    "domain": "RADIATION",
    "condition_id": "LONG_DURATION_GCR_EXPOSURE",
    "purpose": "Evaluate GCR protection for habitable systems designed to support crew for more than 60 days.",
    "rule_kind": "DESIGN_EXPOSURE_RATE_REQUIREMENT",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE_WITH_APPROVED_GCR_MODEL",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "radiation_model": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_action": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "habitable_system_support_duration_days": ">60",
      "mission_context": "BEYOND_LOW_EARTH_ORBIT_PER_RATIONALE"
    },
    "inputs": [
      {
        "name": "crew_support_duration_days",
        "type": "number",
        "required": true
      },
      {
        "name": "environment",
        "type": "enum",
        "values": ["FREE_SPACE", "PLANETARY_SURFACE"],
        "required": true
      },
      {
        "name": "nasa_effective_gcr_dose_rate",
        "type": "number",
        "canonical_unit": "mSv/day",
        "required": true
      },
      {
        "name": "design_verification_model_approved",
        "type": "boolean",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "decision": [
        {
          "when": "crew_support_duration_days <= 60",
          "result": "NOT_APPLICABLE"
        },
        {
          "when": "design_verification_model_approved != true",
          "result": "INCONCLUSIVE"
        },
        {
          "when": "environment == FREE_SPACE AND nasa_effective_gcr_dose_rate < 1.3",
          "result": "PASS"
        },
        {
          "when": "environment == FREE_SPACE AND nasa_effective_gcr_dose_rate >= 1.3",
          "result": "FAIL_REQUIREMENT"
        },
        {
          "when": "environment == PLANETARY_SURFACE AND nasa_effective_gcr_dose_rate < 0.9",
          "result": "PASS"
        },
        {
          "when": "environment == PLANETARY_SURFACE AND nasa_effective_gcr_dose_rate >= 0.9",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "FREE_SPACE": {
        "value": 1.3,
        "unit": "mSv/day",
        "operator": "<"
      },
      "PLANETARY_SURFACE": {
        "value": 0.9,
        "unit": "mSv/day",
        "operator": "<"
      }
    },
    "temporal_window": {
      "type": "DESIGN_EFFECTIVE_DOSE_RATE"
    },
    "confounders": [
      "shielding distribution",
      "crew time in differently shielded locations",
      "GCR spectrum model",
      "surface environment"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "For design verification, use the model and crew-location accounting required by the applicable NASA standard/program.",
    "output": {
      "primary": "rule_result",
      "clinical_assessment_status": "NOT_DETERMINED_BY_RULE"
    },
    "severity_semantics": {
      "on_failure": "GCR_DESIGN_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "ALARA/design review.",
      "Review shielding and crew occupancy assumptions.",
      "Do not treat the rate threshold as a diagnosis of radiation injury."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V1-REV-C",
        "requirement": "V1 4033",
        "section": "4.8.5",
        "printed_page": 45,
        "pdf_page_index_0based": 44,
        "url": "https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "RAD004-T01",
        "synthetic": true,
        "inputs": {
          "crew_support_duration_days": 180,
          "environment": "FREE_SPACE",
          "nasa_effective_gcr_dose_rate": 1.29,
          "design_verification_model_approved": true
        },
        "expected": "PASS"
      },
      {
        "id": "RAD004-T02",
        "synthetic": true,
        "inputs": {
          "crew_support_duration_days": 180,
          "environment": "FREE_SPACE",
          "nasa_effective_gcr_dose_rate": 1.3,
          "design_verification_model_approved": true
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "RAD004-T03",
        "synthetic": true,
        "inputs": {
          "crew_support_duration_days": 180,
          "environment": "PLANETARY_SURFACE",
          "nasa_effective_gcr_dose_rate": 0.9,
          "design_verification_model_approved": true
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "RAD004-T04",
        "synthetic": true,
        "inputs": {
          "crew_support_duration_days": 30,
          "environment": "FREE_SPACE",
          "nasa_effective_gcr_dose_rate": 1.5,
          "design_verification_model_approved": true
        },
        "expected": "NOT_APPLICABLE"
      }
    ]
  }
]
```

Para `VIGILE-RAD-001`, NASA especifica además que el cálculo de carrera incluye exposiciones espaciales previas y, en planificación, la exposición proyectada de una misión futura; las exposiciones médicas y de investigación biomédica no entran en ese límite concreto, aunque deben quedar registradas en el historial de exposición. citeturn24view0

La separación de unidades es crítica. La misma sección de NASA utiliza `mSv` para dosis efectiva y, en la tabla de efectos no cancerígenos por órgano, `mGy-Eq` o `mGy`; VIGILE no debe sumar esos campos o convertirlos automáticamente sin un modelo dosimétrico expresamente validado. citeturn24view0

El requisito SPE de 250 mSv es un **requisito de diseño frente al espectro solar de referencia**, no un punto diagnóstico universal para convertir automáticamente una lectura de dosímetro durante un evento real en “síndrome agudo por radiación”. Del mismo modo, V1 4033 prescribe un requisito de protección de diseño GCR para sistemas de larga duración y especifica el uso del modelo de referencia correspondiente para su verificación. citeturn24view1turn24view3

## Reglas ambientales de hábitat

NASA-STD-3001 Volume 2 Rev. F fija, entre otros requisitos, al menos 30 % de gas diluyente en la atmósfera de cabina; ppCO₂ promedio de una hora ≤3 mmHg; presión para exposición indefinida en el intervalo estricto `34,5 kPa < P ≤ 103 kPa`; y, para cambios de presión superiores a 1 psi, una velocidad de cambio ≤13,5 psi/min. citeturn22view3turn22view0turn22view1turn22view2

```json
[
  {
    "rule_id": "VIGILE-ENV-001",
    "rule_version": "1.0.0",
    "title": "Cabin inert diluent gas fraction",
    "domain": "ENVIRONMENTAL_HEALTH",
    "condition_id": "CABIN_ATMOSPHERE_COMPOSITION",
    "purpose": "Evaluate the cabin diluent-gas fraction under the standard balance-oxygen atmosphere assumption.",
    "rule_kind": "ENVIRONMENTAL_STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "alternate_diluent_interpretation": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_action": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "environment": "HABITABLE_CABIN",
      "default_diluent_assumption": "NITROGEN"
    },
    "inputs": [
      {
        "name": "diluent_fraction_percent",
        "type": "number",
        "canonical_unit": "%",
        "required": true
      },
      {
        "name": "diluent_type",
        "type": "string",
        "required": true
      },
      {
        "name": "balance_oxygen_assumption_valid",
        "type": "boolean",
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "decision": [
        {
          "when": "diluent_type != NITROGEN OR balance_oxygen_assumption_valid != true",
          "result": "REQUIRES_MISSION_AUTHORIZATION"
        },
        {
          "when": "data_quality_status != ACCEPTABLE",
          "result": "INCONCLUSIVE"
        },
        {
          "when": "diluent_fraction_percent >= 30",
          "result": "PASS"
        },
        {
          "when": "diluent_fraction_percent < 30",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "minimum_diluent_fraction": {
        "value": 30,
        "unit": "%",
        "operator": ">="
      }
    },
    "temporal_window": {
      "type": "VALID_ATMOSPHERE_OBSERVATION",
      "fixed_sampling_rate_in_V2_6002": false
    },
    "confounders": [
      "alternate diluent gas",
      "sensor calibration",
      "gas mixing",
      "local atmosphere heterogeneity"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Atmospheric composition measurement must be valid for the relevant habitable compartment.",
    "output": {
      "primary": "rule_result",
      "clinical_diagnosis": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "ATMOSPHERIC_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Atmospheric-control alert/review.",
      "Alternate diluent gases require program medical adjudication and separate requirements.",
      "Do not infer a specific pulmonary diagnosis solely from this rule."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V2-REV-F",
        "requirement": "V2 6002",
        "section": "6.2.1.1",
        "printed_page": 49,
        "pdf_page_index_0based": 48,
        "url": "https://standards.nasa.gov/system/files/tmp/NASA-STD-3001%20Vol%202%20Rev%20F.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "ENV001-T01",
        "synthetic": true,
        "inputs": {
          "diluent_fraction_percent": 30,
          "diluent_type": "NITROGEN",
          "balance_oxygen_assumption_valid": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "ENV001-T02",
        "synthetic": true,
        "inputs": {
          "diluent_fraction_percent": 29.9,
          "diluent_type": "NITROGEN",
          "balance_oxygen_assumption_valid": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "ENV001-T03",
        "synthetic": true,
        "inputs": {
          "diluent_fraction_percent": 30,
          "diluent_type": "HELIUM",
          "balance_oxygen_assumption_valid": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "REQUIRES_MISSION_AUTHORIZATION"
      }
    ]
  },
  {
    "rule_id": "VIGILE-ENV-002",
    "rule_version": "1.0.0",
    "title": "Nominal one-hour cabin ppCO2 limit",
    "domain": "ENVIRONMENTAL_HEALTH",
    "condition_id": "CABIN_CO2_EXPOSURE",
    "purpose": "Evaluate the one-hour average ppCO2 in a habitable volume against the nominal NASA limit.",
    "rule_kind": "ENVIRONMENTAL_STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "off_nominal_thresholds": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_action": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "environment": "HABITABLE_VOLUME",
      "mode": "NOMINAL"
    },
    "inputs": [
      {
        "name": "one_hour_average_ppco2",
        "type": "number",
        "canonical_unit": "mmHg",
        "required": true
      },
      {
        "name": "window_coverage_complete",
        "type": "boolean",
        "required": true
      },
      {
        "name": "aggregation_method_validated",
        "type": "boolean",
        "required": true
      },
      {
        "name": "compartment_id",
        "type": "string",
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "decision": [
        {
          "when": "window_coverage_complete != true OR aggregation_method_validated != true OR data_quality_status != ACCEPTABLE",
          "result": "INCONCLUSIVE"
        },
        {
          "when": "one_hour_average_ppco2 <= 3",
          "result": "PASS"
        },
        {
          "when": "one_hour_average_ppco2 > 3",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "maximum_one_hour_average_ppco2": {
        "value": 3,
        "unit": "mmHg",
        "operator": "<="
      }
    },
    "temporal_window": {
      "duration": 1,
      "unit": "hour",
      "aggregation": "VALIDATED_ONE_HOUR_AVERAGE",
      "note": "The NASA requirement specifies the one-hour average but does not itself prescribe VIGILE's signal-processing implementation."
    },
    "confounders": [
      "incomplete temporal coverage",
      "local CO2 pockets",
      "sensor drift",
      "compartment mixing",
      "crew activity and metabolic generation",
      "payload CO2 generation"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Do not calculate compliance from a single instantaneous sample when the required one-hour average cannot be established.",
    "output": {
      "primary": "rule_result",
      "environmental_alert": "GENERATE_ON_FAIL",
      "clinical_diagnosis": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "NOMINAL_CO2_REQUIREMENT_NOT_MET",
      "clinical_severity": "REQUIRES_SEPARATE_CLINICAL_ASSESSMENT"
    },
    "follow_up": [
      "Trigger environmental systems review/alert.",
      "Use mission-specific lower-level requirements for off-nominal exposure management.",
      "Assess symptoms through a separate clinical pathway when present."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V2-REV-F",
        "requirement": "V2 6004",
        "section": "6.2.1.3",
        "printed_page": 51,
        "pdf_page_index_0based": 50,
        "url": "https://standards.nasa.gov/system/files/tmp/NASA-STD-3001%20Vol%202%20Rev%20F.pdf"
      },
      {
        "source_id": "NASA-STD-3001-V2-REV-F",
        "requirement": "V2 6020",
        "section": "6.2.5.1",
        "printed_page": 58,
        "pdf_page_index_0based": 57,
        "use": "ATMOSPHERIC_DATA_RECORDING"
      }
    ],
    "test_cases": [
      {
        "id": "ENV002-T01",
        "synthetic": true,
        "inputs": {
          "one_hour_average_ppco2": 3.0,
          "window_coverage_complete": true,
          "aggregation_method_validated": true,
          "compartment_id": "HAB-1",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "ENV002-T02",
        "synthetic": true,
        "inputs": {
          "one_hour_average_ppco2": 3.01,
          "window_coverage_complete": true,
          "aggregation_method_validated": true,
          "compartment_id": "HAB-1",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "ENV002-T03",
        "synthetic": true,
        "inputs": {
          "one_hour_average_ppco2": 4.0,
          "window_coverage_complete": false,
          "aggregation_method_validated": true,
          "compartment_id": "HAB-1",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "INCONCLUSIVE"
      }
    ]
  },
  {
    "rule_id": "VIGILE-ENV-003",
    "rule_version": "1.0.0",
    "title": "Total cabin pressure range for indefinite crew exposure",
    "domain": "ENVIRONMENTAL_HEALTH",
    "condition_id": "CABIN_PRESSURE_EXPOSURE",
    "purpose": "Evaluate total pressure against the NASA range for indefinite crew exposure.",
    "rule_kind": "ENVIRONMENTAL_STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "special_suited_operation_interpretation": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_action": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "context": "INDEFINITE_CREW_EXPOSURE",
      "limited_duration_spacesuit_or_special_operations": "NOT_COVERED_BY_THIS_RULE"
    },
    "inputs": [
      {
        "name": "total_pressure",
        "type": "number",
        "canonical_unit": "kPa",
        "required": true
      },
      {
        "name": "exposure_context",
        "type": "enum",
        "values": ["INDEFINITE_CABIN", "LIMITED_SPECIAL_OPERATION"],
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "decision": [
        {
          "when": "exposure_context != INDEFINITE_CABIN",
          "result": "NOT_APPLICABLE"
        },
        {
          "when": "data_quality_status != ACCEPTABLE",
          "result": "INCONCLUSIVE"
        },
        {
          "when": "total_pressure > 34.5 AND total_pressure <= 103",
          "result": "PASS"
        },
        {
          "when": "total_pressure <= 34.5 OR total_pressure > 103",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "lower_bound": {
        "value": 34.5,
        "unit": "kPa",
        "operator": ">"
      },
      "upper_bound": {
        "value": 103,
        "unit": "kPa",
        "operator": "<="
      },
      "equivalent_english_units": {
        "lower": "5 psia, strict greater-than",
        "upper": "15.0 psia, inclusive"
      }
    },
    "temporal_window": {
      "type": "INDEFINITE_EXPOSURE"
    },
    "confounders": [
      "oxygen partial pressure",
      "CO2",
      "mission EVA architecture",
      "special pressure operations"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "Pressure sensor value must be calibrated and associated with the crew exposure compartment.",
    "output": {
      "primary": "rule_result",
      "clinical_diagnosis": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "PRESSURE_EXPOSURE_REQUIREMENT_NOT_MET",
      "clinical_severity": "REQUIRES_SEPARATE_ASSESSMENT"
    },
    "follow_up": [
      "Environmental control alert and mission-protocol response.",
      "Evaluate O2 and CO2 concurrently.",
      "Special operations require their own authorized pressure/decompression pathway."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V2-REV-F",
        "requirement": "V2 6006",
        "section": "6.2.2.1",
        "printed_page": 52,
        "pdf_page_index_0based": 51,
        "url": "https://standards.nasa.gov/system/files/tmp/NASA-STD-3001%20Vol%202%20Rev%20F.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "ENV003-T01",
        "synthetic": true,
        "inputs": {
          "total_pressure": 34.5,
          "exposure_context": "INDEFINITE_CABIN",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      },
      {
        "id": "ENV003-T02",
        "synthetic": true,
        "inputs": {
          "total_pressure": 34.6,
          "exposure_context": "INDEFINITE_CABIN",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "ENV003-T03",
        "synthetic": true,
        "inputs": {
          "total_pressure": 103.0,
          "exposure_context": "INDEFINITE_CABIN",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "ENV003-T04",
        "synthetic": true,
        "inputs": {
          "total_pressure": 103.1,
          "exposure_context": "INDEFINITE_CABIN",
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      }
    ]
  },
  {
    "rule_id": "VIGILE-ENV-004",
    "rule_version": "1.0.0",
    "title": "Internal vehicle pressure rate-of-change requirement",
    "domain": "ENVIRONMENTAL_HEALTH",
    "condition_id": "PRESSURE_CHANGE_AND_BAROTRAUMA_RISK",
    "purpose": "Evaluate the rate of pressure change when total pressure change exceeds 1 psi.",
    "rule_kind": "ENVIRONMENTAL_STANDARD_COMPLIANCE",
    "evidence_class": "NASA_STANDARD",
    "evidence_status": "DOCUMENTED_AND_COMPUTABLE_WITH_VALIDATED_SIGNAL_PROCESSING",
    "software_validation_status": "REQUIRES_IMPLEMENTATION_VALIDATION",
    "authorization": {
      "evaluation": "AUTO_EVALUATION_ALLOWED",
      "signal_processing_method": "REQUIRES_MISSION_AUTHORIZATION",
      "clinical_action": "REQUIRES_MEDICAL_AUTHORIZATION"
    },
    "applicability": {
      "condition": "absolute_total_pressure_change > 1.0 psi"
    },
    "inputs": [
      {
        "name": "absolute_total_pressure_change",
        "type": "number",
        "canonical_unit": "psi",
        "required": true
      },
      {
        "name": "maximum_absolute_pressure_change_rate",
        "type": "number",
        "canonical_unit": "psi/min",
        "required": true
      },
      {
        "name": "rate_calculation_method_validated",
        "type": "boolean",
        "required": true
      },
      {
        "name": "data_quality_status",
        "type": "enum",
        "required": true
      }
    ],
    "derived_variables": [],
    "logic": {
      "decision": [
        {
          "when": "absolute_total_pressure_change <= 1.0",
          "result": "NOT_APPLICABLE"
        },
        {
          "when": "rate_calculation_method_validated != true OR data_quality_status != ACCEPTABLE",
          "result": "INCONCLUSIVE"
        },
        {
          "when": "maximum_absolute_pressure_change_rate <= 13.5",
          "result": "PASS"
        },
        {
          "when": "maximum_absolute_pressure_change_rate > 13.5",
          "result": "FAIL_REQUIREMENT"
        }
      ]
    },
    "thresholds": {
      "trigger_total_pressure_change": {
        "value": 1.0,
        "unit": "psi",
        "operator": ">"
      },
      "maximum_rate": {
        "value": 13.5,
        "unit": "psi/min",
        "operator": "<="
      }
    },
    "temporal_window": {
      "type": "PRESSURE_CHANGE_EVENT"
    },
    "confounders": [
      "sensor sampling rate",
      "filtering",
      "derivative noise",
      "event segmentation",
      "sensor latency"
    ],
    "missing_data_policy": "INCONCLUSIVE",
    "data_quality_policy": "The maximum rate must be calculated using a validated pressure-signal processing method with sufficient temporal resolution.",
    "output": {
      "primary": "rule_result",
      "barotrauma_diagnosis": "NOT_DETERMINED_BY_THIS_RULE"
    },
    "severity_semantics": {
      "on_failure": "PRESSURE_RATE_REQUIREMENT_NOT_MET",
      "clinical_severity": "NOT_DETERMINED"
    },
    "follow_up": [
      "Trigger environmental/pressure-system review.",
      "Apply the separate V2 6150 barotrauma-prevention requirement where applicable.",
      "Evaluate crew symptoms separately; this engineering threshold alone does not diagnose barotrauma or DCS."
    ],
    "source_locators": [
      {
        "source_id": "NASA-STD-3001-V2-REV-F",
        "requirement": "V2 6007",
        "section": "6.2.2.2",
        "printed_page": 53,
        "pdf_page_index_0based": 52,
        "url": "https://standards.nasa.gov/system/files/tmp/NASA-STD-3001%20Vol%202%20Rev%20F.pdf"
      }
    ],
    "test_cases": [
      {
        "id": "ENV004-T01",
        "synthetic": true,
        "inputs": {
          "absolute_total_pressure_change": 0.9,
          "maximum_absolute_pressure_change_rate": 20.0,
          "rate_calculation_method_validated": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "NOT_APPLICABLE"
      },
      {
        "id": "ENV004-T02",
        "synthetic": true,
        "inputs": {
          "absolute_total_pressure_change": 1.1,
          "maximum_absolute_pressure_change_rate": 13.5,
          "rate_calculation_method_validated": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "PASS"
      },
      {
        "id": "ENV004-T03",
        "synthetic": true,
        "inputs": {
          "absolute_total_pressure_change": 1.1,
          "maximum_absolute_pressure_change_rate": 13.6,
          "rate_calculation_method_validated": true,
          "data_quality_status": "ACCEPTABLE"
        },
        "expected": "FAIL_REQUIREMENT"
      }
    ]
  }
]
```

En `VIGILE-ENV-002`, una lectura instantánea de 4 mmHg **no basta por sí misma para afirmar que V2 6004 fue violado**: la cláusula se define sobre el promedio de una hora. A la vez, NASA exige que las variables atmosféricas se registren automáticamente durante operaciones tripuladas y que el sistema alerte a la tripulación cuando parámetros atmosféricos estén fuera de límites seguros. citeturn22view0turn25view1turn25view2

En `VIGILE-ENV-004`, la norma indica expresamente que un cambio transitorio total ≤1 psi puede superar 13,5 psi/min; también advierte que el requisito de velocidad no sustituye el requisito separado de prevención de barotrauma V2 6150. Por eso el motor devuelve `NOT_APPLICABLE` para el comparador V2 6007 en un evento ≤1 psi en vez de producir un falso incumplimiento. citeturn22view2

## Salvaguardas, trazabilidad y estado de esta primera biblioteca

El catálogo reconstruido queda así:

| Rule ID | Dominio | Requisito primario | Operación |
|---|---|---|---|
| VIGILE-AER-001 | Aeróbico | V1 4001 | VO₂max ≥32,9 para EVA microgravedad |
| VIGILE-AER-002 | Aeróbico | V1 4002 | VO₂max ≥36,5 para EVA superficie |
| VIGILE-AER-003 | Aeróbico | V1 4003 | ≥80 % del baseline |
| VIGILE-MUS-001 | Muscular | V1 4023 | Tabla de fuerza preflight |
| VIGILE-MUS-002 | Muscular | V1 4024 | ≥80 % del baseline |
| VIGILE-BONE-001 | Óseo | V1 4027 | 95 % cadera/columna; 90 % cuello femoral |
| VIGILE-NUT-001 | Nutrición | V1 4020 | 100 % de requerimientos calculados proporcionados |
| VIGILE-RAD-001 | Radiación | V1 4030 | Carrera <600 mSv |
| VIGILE-RAD-002 | Radiación | V1 4031 | SPE de diseño <250 mSv |
| VIGILE-RAD-003 | Radiación | V1 4032 | Nuclear <20 mSv/año de misión prorrateado |
| VIGILE-RAD-004 | Radiación | V1 4033 | GCR <1,3 / <0,9 mSv/día |
| VIGILE-ENV-001 | Ambiente | V2 6002 | Diluyente ≥30 % |
| VIGILE-ENV-002 | Ambiente | V2 6004 | ppCO₂ 1 h ≤3 mmHg |
| VIGILE-ENV-003 | Ambiente | V2 6006 | 34,5 < P ≤103 kPa |
| VIGILE-ENV-004 | Ambiente | V2 6007 | >1 psi → ≤13,5 psi/min |

Los localizadores y valores de las primeras siete reglas proceden directamente de NASA-STD-3001 Volume 1 Rev. C, pp. 32–40 según la paginación impresa correspondiente a cada requisito; las reglas radiológicas se encuentran en §4.8, pp. 40–45; y las cuatro reglas ambientales se localizan en Volume 2 Rev. F, pp. 49–53. citeturn23view0turn21view2turn21view4turn21view5turn24view0turn24view1turn24view3turn22view3turn22view0turn22view1turn22view2

Para Codex, estas reglas deben almacenarse como **datos versionados**, no como `if` dispersos por el código. Cada resultado deberá conservar como mínimo `rule_id`, `rule_version`, revisión de la fuente, Requirement ID NASA, astronauta o compartimento afectado, inputs originales, unidades originales, conversiones, timestamps, calidad del dato, configuración de misión, variables derivadas, resultado, justificación y estado de autorización. NASA exige que los resultados de monitorización de salud permanezcan recuperables para evaluación y análisis de tendencias y que los registros estén protegidos. citeturn17view13turn17view14

El motor también debe fijar la revisión normativa que ejecutó. NASA señala que sus requisitos se revisan periódicamente conforme aparece nueva evidencia y se definen los parámetros de misión; la Rev. F de Volume 2 de julio de 2026 demuestra que esto no es un detalle hipotético. citeturn20view0turn16view1

No deben hardcodearse como reglas clínicas globales, todavía, los siguientes elementos:

**Sueño/fatiga:** NASA requiere límites operacionales y gestión del descanso, pero esos límites deben reconstruirse con su documentación específica y requisitos de programa antes de convertirlos en umbrales universales.

**Cognición y salud conductual:** NASA exige estado dentro de valores clínicamente aceptados y evaluación/monitorización, pero ello no proporciona por sí solo una puntuación diagnóstica universal que VIGILE pueda inventar. citeturn16view2

**Hematología e inmunología:** la norma remite a rangos normativos y valores críticos específicos del parámetro; esos valores deben asociarse con la prueba, laboratorio, población y protocolo concreto antes de programarlos.

**SANS, renal, infecciones, gastrointestinal, neurológico, dermatológico, urgencias y farmacología:** seguirán presentes en la arquitectura, pero no se debe rellenar artificialmente su lógica con los quince comparadores de esta parte.

**DCS:** la Rev. F aporta una regla muy relevante para **validación terrestre del protocolo** —probabilidad <4 % con 95 % de confianza—, pero la propia norma aclara que no es una regla para uso directo en vuelo; por ello debe entrar en el futuro catálogo como `PROTOCOL_VALIDATION_RULE`, no como un detector clínico onboard. citeturn22view2

**O₂, humedad, temperatura, contaminantes y límites radiológicos por órgano:** existen requisitos adicionales implementables, pero requieren extraer cuidadosamente sus tablas o figuras correspondientes antes de codificarlos. En especial, no se deben aproximar límites de una figura ni extrapolar tablas visuales sin revisar la fuente exacta.

La regla transversal para todo VIGILE debe ser:

```json
{
  "vigile_decision_separation_policy": {
    "measurement": "raw or derived datum",
    "requirement_compliance": "deterministic comparison against a documented requirement",
    "finding": "interpreted abnormality supported by evidence",
    "clinical_hypothesis": "possible condition requiring assessment",
    "diagnosis": "requires appropriate diagnostic evidence and authorization",
    "triage": "requires condition-specific severity evidence and mission protocol",
    "intervention": "requires an authorized protocol",
    "treatment": "never inferred solely from a standards-compliance rule",
    "recovery": "requires condition-specific reassessment criteria",
    "llm_role": "retrieve, explain, guide and summarize; never modify deterministic decisions or authorize clinical actions"
  }
}
```

Esto evita el error arquitectónico más peligroso para VIGILE: convertir, por ejemplo, `BMD <95 %`, `VO2max <32,9`, `ppCO2 >3 mmHg durante una hora` o `career dose ≥600 mSv` en una supuesta enfermedad genérica `CRITICAL`. Son clases de requisito distintas, con contextos y consecuencias diferentes. NASA-STD-3001 define requisitos de rendimiento, límites permisibles y criterios de diseño para proteger salud y rendimiento; su función no es convertir automáticamente cada incumplimiento técnico en un diagnóstico. citeturn16view2turn16view3

**Estado de verificación de PARTE 1:** las quince reglas anteriores quedan reconstruidas desde las revisiones activas de NASA-STD-3001 y con localizadores específicos de requisito, sección y página; los test cases son inequívocamente `SYNTHETIC` y verifican lógica de software, **no validación clínica**. La regla ósea incorpora además la limitación documentada del Evidence Report de NASA para impedir que Codex confunda retención de BMD con predicción individual de fractura. citeturn16view0turn16view1turn18view0