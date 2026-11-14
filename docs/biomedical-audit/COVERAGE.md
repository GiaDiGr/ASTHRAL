# Matriz de cobertura biomédica

Todas las filas requieren revisión clínica independiente. «Probado» significa prueba de software sintética. El inventario `criterion-inventory.json` contiene los 42 predicados de los documentos fijados, con ruta JSON, operador, valor y fuentes. No contiene automáticamente las condiciones adicionales del código, enumeradas aquí.

| Ruta | Implementación computacional | Pruebas de software | Respaldo documental contrastado | Pendiente clínico / contextual |
|---|---|---|---|---|
| Diabetes | Cuatro vías de elegibilidad; confirmación por pruebas distintas o repetición; muestras y contexto; discordancia | Casos DM-01…04, igualdad A1C/FPG, duplicados, misma ocasión, muestras discordantes, contexto invalidado, negativo con alternativas desconocidas | ADA 2026 tabla 2.1 y Confirming the Diagnosis; pasajes indexados del original | Interferencias A1C, embarazo, excepciones de ensayo, oportunidad de repetición y discordancia clínica. No clasifica tipo de diabetes ni episodios de tratamiento. |
| DKA | Tres componentes AND con alternativas OR; resolución bioquímica; potasio separado | DM-05/06, caso 180/4.2/7.22 sin alternativas, límites de pH/bicarbonato, invalidación, OR válidas y seguridad K | Consenso 2024 figura 2A, criterios y resolución; pasajes originales indexados | Método/controles para cada cetonómetro, contemporaneidad, gravedad completa, otros trastornos ácido-base y recuperación clínica. |
| OH | Caídas SBP/DBP derivadas OR, ≤3 min y reducción sostenida; bloqueo por gravedad | ORTHO-01…03/06, alternativa DBP ausente, cronología invertida, gravedad parcial/microgravedad | AHA 2024 definición y protocolo de medición; pasajes originales indexados | Baseline supino 5–10 min, posición, técnica, comidas/fármacos, etiología. La ventana y sostenimiento son declaraciones, no reconstrucción de una serie. |
| POTS | HR sostenida, ventana, síntomas, duración, ausencia de OH y causas alternativas; sólo ≥20 años | ORTHO-04/05, umbrales exactos 30/10/3, edad, OH concomitante, causas alternativas | HRS 2015 y NIH 2021 sección 2; pasajes originales indexados | Definiciones limítrofes de OH entre documentos; causas excluidas por profesional, frecuencia/sostenimiento, población adolescente, gravedad espacial. |
| AKI | Cambio absoluto/relativo con ventana, diuresis fiable, mínimo estadio sustentado | AKI-01…06, 48 h/7 días exactos, orden UTC, 0.5/0.3 y duración, baseline ausente, creatinina aislada, binding histórico | KDIGO 2012 2.1.1, tabla 2 y razonamiento; texto completo recuperado con DOI/hash | Baseline apropiado, CKD/masa muscular, balance real y método de orina; máxima severidad del episodio y ramas RRT/anuria; no hay eGFR pediátrico. |
| Anafilaxia | Dos vías WAO; exclusiones inhalatorias; BP actual y caída porcentual; urgencia separada | ANAPH-01…06, 90 y 30% estrictos, broncoespasmo/exclusiones, piel ausente, coexistencia DKA, no confundir OH | WAO 2020 **tabla 2** y figura 1; texto completo recuperado | Inicio/simultaneidad, relación causal con exposición, severidad GI, juicio clínico; BP supino/actual no demuestra por sí sola causalidad. |
| Diferencial | Orden ordinal, apoyo y contradicciones; rutas externas explícitas; pruebas pendientes separadas de seguridad | DIFF-01…06, coexistencia, reader y contrato de pruebas | Investigación local `differential_rules.json`; fuentes de cada ruta | No hay probabilidades, calibración clínica del ranking ni recomendador exhaustivo. No diagnostica arritmia o hipovolemia. |
| Baselines / tendencias | Mediana/MAD, versionado, retiro/caducidad, comparabilidad; pendiente, EWMA/CUSUM configurables | Suite existente v0.2 y seguridad: orden, caducidad, retiro, revisión, conflictos, replay | Fórmulas y políticas técnicas documentadas; no umbrales clínicos añadidos | Calibrar población, cadencia, mínimos de datos, parámetros y validez clínica. No vincular automáticamente baseline estadístico a baseline renal. |
| Calidad / sensores | Tipos, unidades, calibración, rangos técnicos, antigüedad configurada, tiempos y ámbitos | Unidades incorrectas, booleanos numéricos, no finitos, future/window, sensor caducado, conflictos | Políticas del dispositivo y métodos declarados | No asegura disponibilidad espacial ni certifica un sensor real. Glucosa mmol/L ×18 es la conversión específica vigente; otras unidades no compatibles se bloquean. |

## Condiciones adicionales implementadas fuera del JSON científico

- OH: `upright_window_minutes <= 3` AND `sustained_reduction == true`. Deltas = presión erguida − baseline. No derivar si baseline posterior.
- POTS: `sustained_delta_hr_bpm` requiere `sustained_hr_rise == true`; se usa delta aportado, no una derivación completa de la señal. OH computada verdadera excluye POTS. La edad desconocida no se interpreta como adulta; la rama 12–19 se bloquea.
- DM: `ogtt_2h_timing_valid == true`; ayuno, carga y ensayo vinculados a muestra; síntomas/crisis vinculados para vía aleatoria. Dos ensayos distintos pueden confirmar en una ocasión; un mismo ensayo exige muestras e instantes distintos. Discordancia requiere revisión/repetición, no voto mayoritario.
- Anafilaxia: broncoespasmo de la segunda vía requiere `common_inhalant_trigger == false` y `food_inhalation_without_ingestion == false`. La caída porcentual usa **presión actual** y baseline válido, no `upright_sbp_mm_hg`.
- AKI: baseline previo y positivo, cambio ≤48 h o razón ≤7 días; no reconstruir baseline. Diuresis exige `body_mass_known` y `urine_collection_reliable`. Estadio 2: razón ≥2 o diuresis <0.5 durante ≥12 h. Estadio 3: razón ≥3, o creatinina ≥4 con cambio agudo documentado, o RRT declarada, o diuresis <0.3 durante ≥24 h, o anuria ≥12 h; únicamente si la ruta AKI se cumple. Son mínimos del snapshot, no máximo longitudinal garantizado.
- DKA: potasio ausente/inutilizable bloquea seguridad; valor ≤3.5 mantiene bloqueo conservador previo. Ningún valor elimina el bloqueo de autorización de misión.
- Todas: población, calidad, fuente utilizable y gravedad se aplican además del árbol. Por eso la raíz TRUE puede coexistir con estado final INSUFFICIENT_DATA/NOT_APPLICABLE y una limitación explícita. El consumidor debe mostrar ambos, sin convertir la raíz aislada en decisión final.

## Cobertura por etapas

| Etapa | Estado real |
|---|---|
| Prevención | Estructura/documentación; no protocolo preventivo automatizado. |
| Monitorización | Adquisición y análisis descriptivo implementados; disponibilidad real de sensores no acreditada. |
| Detección | Seis rutas restringidas y comparadores normativos de simulación; no cobertura automática de las 44 condiciones. |
| Evaluación / confirmación | Lógica computable parcial; juicios clínicos e interferencias pendientes. |
| Diferencial | Ranking ordinal de investigación; ramas externas explícitas. |
| Triaje | Etiquetas de urgencia existentes; no validación operativa de triaje. |
| Intervención autorizada | **Bloqueada**. No prescripción ni ejecución terapéutica. |
| Recuperación | Criterio bioquímico DKA y registros humanos; no determinación automática de recuperación clínica. |
| Seguimiento | Episodios, planes, revisiones y reevaluaciones inmutables; no nueva evidencia inventada. |
| Pronóstico | Estructura/documentación; sin modelo pronóstico clínico operativo. |

El endpoint genérico de cobertura de las 44 condiciones mantiene su taxonomía histórica y no fusiona automáticamente esos identificadores con las seis rutas. Para integración, consultar esta matriz junto con `/clinical/conditions/{condition}/criteria`; no presentar el catálogo genérico como lista de detectores validados.
