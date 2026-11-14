# Paquete para revisión clínica independiente

Estado: **PENDIENTE**. Revisor: sin asignar. Fecha, credenciales, especialidad, conflictos de interés y firma: por completar. Codex ha realizado una revisión técnica/documental y pruebas de software; no una validación clínica independiente.

## Material entregado

1. `AUDIT.md`: hallazgos, correcciones y límites.
2. `SOURCE_REVIEW.md` y `source-checks/`: referencias, localizadores, copias recuperadas y fallos de adquisición.
3. `criterion-inventory.json` y `COVERAGE.md`: predicados documentados, condiciones adicionales del código y cobertura parcial por etapa.
4. `cases-30-reviewed.json`: solicitudes enteramente sintéticas, expectativas de la reconciliación previa, resultados reales completos y replay.
5. `test_biomedical_audit.py`: nuevos casos y expectativas explícitas. `tests-final.xml` y `test-summary.json`: ejecución real. Aprobar estas pruebas no valida su idoneidad médica.
6. `CONTRACTS.md`, `openapi.json`, `change-manifest.json` y `preservation.json`: interfaz, identidad y preservación.

## Casos representativos que requieren valoración

| Caso | Resultado esperado del software | Pregunta para el revisor |
|---|---|---|
| Diabetes conocida, glucosa 180, beta-OHB 4.2, pH 7.22, bicarbonato/cetonuria/K ausentes | DKA CRITERIA_MET; alternativas no bloqueantes; K bloquea seguridad; ninguna ejecución | Confirmar separación entre suficiencia diagnóstica y datos terapéuticos, y alcance de la palabra «criterios». |
| FPG 90 con ayuno válido; otras vías no evaluadas | UNKNOWN/INSUFFICIENT_DATA, no exclusión de diabetes | ¿Es adecuada esta representación conservadora para el flujo previsto sin inducir pruebas indiscriminadas? |
| Dos FPG positivas con contexto de ayuno invalidado en una muestra | Sin confirmación automática | Revisar asociación por muestra, correcciones de laboratorio y cuándo sustituir una atestación previa. |
| FPG 126 y A1C 6.5 válidas en una ocasión | Confirmación computable satisfecha | Revisar interferencias, población y evidencia mínima del ensayo. |
| Glucosa aleatoria positiva y síntomas en otro contexto | No combinar automáticamente | Definir formalmente episodio/colección y asociación de síntomas, sin que IDs sustituyan juicio. |
| OH en Tierra, caída sostenida 20/10, ventana 3 min | Se cumple el criterio numérico; etiología no confirmada | Incorporar/restablecer requisitos de reposo, postura y técnica mediante una política aprobada. |
| Mismos datos en microgravedad o gravedad parcial | NOT_APPLICABLE / INSUFFICIENT_DATA respectivamente | ¿Qué protocolos alternativos de misión serían válidos? No están implementados ni autorizados. |
| HR +30, 10 min, síntomas 3 meses y exclusiones declaradas | POTS computable sólo con población compatible | Resolver diferencia HRS/NIH en OH limítrofe y validar exclusiones completas. |
| Creatinina 1→1.3 en 48 h; frente a 48 h + fracción | Primera alternativa positiva exactamente a 48 h; segunda no se asume | Revisar incertidumbre analítica/temporal y manejo de valores cerca del umbral. |
| Oliguria fiable 0.4 durante 6 h y creatinina aislada 4, sin baseline | AKI con mínimo estadio 1; no estadio 3 por esa creatinina aislada | Ratificar aplicación del razonamiento KDIGO y diseño longitudinal del máximo estadio. |
| Exposición probable/inicio agudo, SBP actual 90 o caída exactamente 30% | Esas hojas estrictas son FALSE; otras ramas pueden seguir UNKNOWN | Confirmar límites, episodio, causalidad, población y contexto de presión. |
| Caída ortostática, exposición probable, sin presión actual de reacción | No usar presión erguida como sustituto automático de hipotensión alérgica | Aprobar separación semántica entre maniobra ortostática y evento agudo. |
| DKA y anafilaxia simultáneas | Ambas rutas pueden cumplir criterios; urgencia agregada; protocolos bloqueados | Revisar prioridad y coexistencia; el ranking no impone exclusividad ni probabilidad. |

## Decisiones pendientes de aprobación profesional

- Obtener y revisar integralmente ADA, DKA, AHA, HRS y NIH; confirmar versión, erratas, localizadores y suficiencia de la traducción computable. Precisar por uso los localizadores WAO: tabla 2/figura 1 para diagnóstico; el registro también incluye manejo y tabla 6. No reescribir el manifiesto actual.
- Definir población, embarazo, interferencias A1C, método válido por biomarcador, incertidumbre y datos contradictorios. Aprobar políticas de vigencia y contemporaneidad específicas de cada ruta.
- Precisar cuándo un dato «no medido» es candidato útil, cuándo un resultado negativo permite terminar evaluación y cuándo debe solicitarse confirmación/repetición. El catálogo de pruebas es incompleto y no debe sustituir ese juicio.
- Revisar el significado de gravedad, urgencia, confirmación, resolución bioquímica y episodio; validar la política de prioridad diferencial y sus ramas externas.
- Definir requerimientos de dispositivos, recursos, tripulación, comunicación y autorización en misión. Actualmente no existe ejecución terapéutica y no debe habilitarse con este paquete.
- Establecer un protocolo de validación independiente, casos adversariales revisados por clínicos, métricas y criterios de aceptación antes de emplear datos reales o estudiar uso operacional. Obtener aprobaciones éticas/regulatorias que correspondan al uso futuro.

## Registro de revisión a completar

Por cada ruta/predicado: `aceptado | requiere corrección | evidencia insuficiente | no aplicable`; justificación, fuente/localizador, caso adversarial, decisión, responsable, fecha y versión revisada. Mantener separados el visto bueno documental, el ensayo técnico y la validación clínica. Ninguno está prefirmado en este paquete.

Conclusión actual: listo para revisión e integración técnica de investigación, **no aprobado para decisión clínica real ni operación espacial**.
