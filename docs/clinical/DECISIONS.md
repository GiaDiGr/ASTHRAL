# Decisiones y límites clínicos de VIGILE v0.4

Fecha: 2026-10-16. Prototipo de investigación. Ningún resultado representa validación clínica, certificación, autorización de misión ni ejecución terapéutica.

## Conservación y procedencia

Se conservó byte por byte el informe `deep-research-report-2026-10-16.md`; el SHA-256 está en `engine/vigile/clinical_knowledge/manifest.json`. Sus ocho JSON se extrajeron sin modificar contenido semántico ni IDs. El manifiesto comprueba sus bytes al cargar. Las correcciones computables viven en código versionado, nunca sobrescriben los JSON originales. `knowledge_hash` cubre los ocho documentos y `implementation_hash` cubre los módulos Python, incluyendo las adaptaciones. El registro inmutable de cada evaluación conserva ambos hashes, snapshot, hash de entrada, árbol, fuentes, versión de criterio y hash de salida.

La etiqueta VERIFIED procede del informe; no es vigilancia continua de vigencia. El resultado la presenta como `PINNED_VERIFIED_AT_REPORT_DATE_NOT_CONTINUOUSLY_VERIFIED`. Los estados borrador/no verificado/no vigente bloquean criterios positivos. KDIGO 2026 permanece documental, sin activar reglas; se usa la versión final 2012 especificada. El runtime no consulta Internet.

## Inconsistencias resueltas

| Hallazgo | Decisión explícita |
|---|---|
| La prueba usa metadata.aki_stage, ausente del modelo | Contrato ClinicalMetadata con aki_stage 1/2/3 o null, stage mínimo sustentado, resolución DKA y entradas de derivaciones. |
| ELIGIBLE aparece sin política de misión | Separar indication_supported de protocol_status. Siempre BLOCKED_AUTHORIZATION entre las razones. No se implementa un emisor de autorizaciones. |
| Varios bloqueos simultáneos | Conservar todas las razones. Prioridad de presentación: no indicado, contraindicación, falta de datos, recursos, autorización. No rebaja urgencia. |
| DM-05 espera bloqueo de autorización pese a faltar potasio | Criterios DKA satisfechos y emergencia; bloqueo primario por datos de seguridad, además de recursos y autorización. |
| DIABETES frente a DM | Alias explícito en diferencial; ID original se conserva en reported_condition_id. |
| ORTHOSTATIC_SYNDROME y DIZZINESS_TACHYCARDIA_PRESENTATION | Agrupaciones de protocolo, no nuevos diagnósticos. OH/POTS comparten protocolo documental; presentación tiene elegibilidad separada. |
| TIME_CRITICAL_SUSPECTED usado como estado diagnóstico | Es un nivel ordinal del diferencial. No se incorpora al enum diagnóstico ni se convierte en diagnóstico confirmado. |
| Pruebas esperadas no registradas: potasio, electrolitos, acciones de reevaluación | No inventar IDs. Para potasio, next_tests incluye test_id=null, acción explícita y TEST_ID_NOT_DEFINED_IN_REPORT. Otras acciones documentales no son pruebas ejecutables. |
| Casos sin timestamps, métodos, población o unidades | Adaptador exclusivo de fixtures añade andamiaje sintético explícito: fecha fija, adulto no gestante de 30 años, unidades canónicas, métodos sintéticos declarados. No añade hallazgos clínicos ausentes. |
| ORTHO-01/02 no documentan reducción sostenida | Sospecha, no cumplimiento completo. La prueba adicional de OH completa aporta sustained_reduction explícito. |
| ORTHO-04 tiene delta HR pero no persistencia sostenida | Sospecha. Caso adicional completo verifica POTS; no inferir persistencia del delta. |
| Umbral POTS adulto podría aplicarse a 18–19 años | Exigir edad conocida >=20 para esta ruta de 30 bpm. Ruta adolescente no implementada. Población adulta y edad <18 se rechazan por contradicción. |
| AKI-03 no documenta masa ni fiabilidad de colección | Dato de diuresis insuficiente. Pruebas adicionales sí suministran ambas verificaciones y cubren etapas 1–3. |
| DIFF-01 solo contiene delta SBP sin medidas originales | No aceptar derivados externos como evidencia calculada. Falta baseline/upright y persistencia. |
| DIFF-05 contiene delta creatinina sin muestras y diuresis sin validación | Insuficiente para confirmar AKI. No inventar muestras ni masa corporal. |
| ANAPH-04 omite elementos de segunda vía WAO | No asumir que todo lo no descrito es falso; queda sospecha con reevaluación pendiente. |
| DIFF-03 omite inicio agudo | Emergencia por signos de peligro, pero criterio completo pendiente. |
| ANAPH-06 omite exclusiones de broncoespasmo de segunda vía | Preservar emergencia; no afirmar criterio completo sin contexto de exposición. |
| ANAPH-01/02/05 omiten recursos de epinefrina | Criterios satisfechos; bloqueo de recursos además de autorización. No es una contraindicación farmacológica inventada. |
| HYPOVOLEMIA/AKI faltan en la lista original de mareo, pero aparecen en sus casos | Enrutamiento explícito hacia ramas ya descritas en otras presentaciones. Hipovolemia sigue siendo hipótesis externa sin criterios implementados. |
| DIFF-02 y DIFF-06 mezclan estado global con estado de hipótesis | No generar un diagnóstico agregado. Se prueban las salidas por condición y el ranking por separado. |
| Rangos KDIGO escritos 1.5–1.9 y 2.0–2.9 | Clasificar por límites >=1.5, >=2 y >=3, sin huecos artificiales para 1.95/2.95. Stage es el máximo sustentado y puede faltar información para uno mayor. |
| Clasificaciones espaciales no coinciden con el enum propuesto | Normalizar Earth a APPLICABLE_WITH_LIMITATIONS, microgravedad libre a NOT_APPLICABLE. Gravedad parcial bloquea confirmación ortostática hasta validación. |
| Repetición de glucemia podría contar duplicados | Dos registros del mismo test/muestra no confirman. El mismo test requiere muestra y tiempo diferentes; pruebas distintas pueden confirmar en una misma ocasión. |
| OGTT carece de comprobación temporal en árbol original | Exigir ogtt_2h_timing_valid además de carga 75 g, ligado a la misma muestra. |

`case-reconciliation.json` conserva cada expectativa original junto al resultado real y diferencias. `case-reconciliation.md` permite revisarlas sin ejecutar código. Los 30 tests usan expectativas explícitas revisadas, no expectativas regeneradas a partir de la salida. Pruebas adicionales verifican casos completos y fronteras.

## Contrastes con fuentes primarias

La confirmación de diabetes exige resultados anormales independientes; CGM no sustituye una muestra diagnóstica. [ADA 2026](https://doi.org/10.2337/dc26-S002).

La DKA conserva sus tres componentes y puede presentarse con glucemia inferior al umbral cuando existe diabetes conocida. El bloqueo por potasio usa la condición de seguridad publicada; el valor exactamente 3.5 se conserva bloqueado por cautela ante la ambigüedad del informe entre iniciar y reanudar. No se calcula ninguna dosis. [Consenso DKA 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11272983/).

La segunda vía de anafilaxia no exige piel afectada; la nota sobre broncoespasmo excluye desencadenantes inhalantes comunes y reacciones atribuidas a inhalación de alimentos sin ingestión. Se añaden dos datos explícitos para no omitir esa restricción. [WAO 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7607509/).

El umbral de incremento de frecuencia no es el mismo para 12–19 años. La ruta incluida queda limitada a >=20 años; no se implementa la rama adolescente. [HRS 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC5267948/).

Las ventanas de creatinina son 48 h y 7 días; no se imputa un baseline. [KDIGO 2012](https://kdigo.org/wp-content/uploads/2016/10/KDIGO-2012-AKI-Guideline-English.pdf).

## Lagunas que permanecen bloqueadas o limitadas

- No hay política de misión firmada/verificada ni motor de ejecución. READY_FOR_CREW/ELIGIBLE son estados reservados del contrato, no alcanzables mediante credenciales o campos del cliente. Medicación, dosis y órdenes a dispositivos no tienen endpoints.
- Los recursos son declaraciones de disponibilidad para análisis, no inventario certificado ni reserva transaccional. No habilitan tratamientos.
- window_start/as_of delimitan una evaluación retrospectiva declarada por el investigador. No se inventó un intervalo clínico universal de simultaneidad/obsolescencia. Antes de uso operativo deben validarse ventanas por ruta, adquisición, estabilidad y método. La coincidencia temporal dentro de una ventana amplia no acredita simultaneidad clínica.
- La calidad de observaciones clínicas introducidas manualmente es una atestación del emisor autorizado. Las mediciones referenciadas pasan además por controles existentes de dispositivo, calibración, rango técnico y conflicto. No se demuestra fidelidad física del sensor ni se inventan rangos clínicos para cada analito.
- Las unidades convertibles entre masa y molaridad dependen del analito. Solo se aplica la conversión de glucosa documentada, mmol/L *18. Creatinina en micromol/L queda incompatible hasta incorporar conversión y validación explícitas. No convertir genéricamente mmol/L a mg/dL.
- Baseline clínico de AKI significa muestra previa identificada y temporalmente válida; no se usa automáticamente la mediana personalizada de monitoreo como si fuese baseline KDIGO. No hay imputación de eGFR.
- Reassessment recibe un snapshot explícito completo, crea un nuevo ID y enlaza parent_id; no fusiona silenciosamente síntomas antiguos ni modifica el resultado previo. Exige mismo sujeto, misión, ruta y tiempo no regresivo.
- Diferencial ordinal sin probabilidades. Hipótesis externas no tienen diagnóstico implementado. Coste/riesgo de pruebas no especificados quedan desconocidos; orden estable por urgencia, disponibilidad declarada e ID. No se ejecutan pruebas.
- Resolución bioquímica de DKA es un indicador separado; no demuestra recuperación completa ni cancela seguimiento. Stage AKI requiere AKI sustentada; creatinina crónicamente alta o RRT aislada no inventan episodio agudo.
- Las otras condiciones históricas no se convierten en nuevos diagnósticos. Los comparadores y módulos previos conservan sus restricciones de investigación.
- Microgravedad terrestre no validada, validación espacial específica pendiente. No hay umbrales espaciales nuevos, prevención/prognóstico autónomos ni protocolos pediátricos/gestacionales.
- SQLite sigue sin cifrado. Los hashes detectan modificaciones dentro del diseño, pero un atacante con control del almacenamiento/código puede reconstruir la cadena y manifiestos. Hace falta anclaje externo firmado, control de integridad del despliegue, ACL/aislamiento de procesos y protección de credenciales/backups.
- RAG solo recibe proyección autorizada, sin snapshot, credenciales, perfil o misión en la respuesta clínica. Las cifras del árbol pueden ser sensibles: aplicar controles de acceso y retención también en el consumidor. Nunca montar la BD ni archivos de credenciales de escritura en el proceso LLM.
- Replay exige mismos hashes de código y conocimiento. Se conserva ZIP de código/tests v0.3 anterior; no se reescribe historial antiguo para aparentar compatibilidad de replay tras una actualización.
- Se mantiene el aviso de deprecación Starlette/httpx. Resolverlo requiere cambio de dependencias y pruebas de compatibilidad; no se actualizó el entorno sin necesidad.
