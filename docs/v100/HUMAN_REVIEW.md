# Revisión independiente y próximos trabajos

Codex prepara evidencia de software; no sustituye revisor clínico independiente ni autoriza uso médico/operacional/espacial.

Profesional clínico: revisar docs/ai/CONSISTENCY_AUDIT.md, auditorías anteriores y engine/vigile/clinical_knowledge (criterios/fuentes/contraindicaciones/espacio/casos). Confirmar operadores/unidades/condiciones/confirmación/excepciones/aplicabilidad contra originales. No completar vacíos por suposición ni ajustar umbrales para pasar escenarios. RAG diferencia autoridad y el extracto primario de hipoglucemia es parcial.

Casos representativos: DKA B18/B18p1 (alternativas cumplidas, seguridad separada); A35 (tendencia no enfermedad); v07 A15/stale (ausente/inválido no normal); ortostatismo/POTS en microgravedad NOT_APPLICABLE; hipoglucemia discordante; anafilaxia/diferencial de clinical_demo. Entradas/resultados esperados: informes de misión, casos originales y tests. Snapshot/versiones/hashes preservados. Plan sintético no acredita revisión sanitaria.

Lenguaje/voz: adjudicar referencias/predicciones/WAV de voice-benchmark y texto validado de e2e-r2. Evaluar números/unidades/negaciones y errores clínicamente relevantes, además de WER; inteligibilidad/naturalidad humana EN/ES y checklist físico DEMO. No dar autonomía por mejorar ASR.

RAG: revisión humana de qrels/pasajes/referencias; pertinencia ≠ evidencia suficiente de paciente. reserved/results.json conserva TODO R1; revisar especialmente02/05/09/11. R2 se corrigió después de leer banco: crear NUEVO banco ciego antes de generalización.

Seguridad: revisar sesiones/orígenes/scopes, ticket entre sesiones, audio malformado, presión de recursos, aislamiento/cifrado/rotación y protección externa de anclajes. Localhost/DPAPI/HMAC no bastan contra procesos de misma cuenta.

Formato de devolución: ID/revisión/hashes/entrada/esperado/observado/fuente-sección/gravedad/impacto/decisión/firma-fecha. Registrar evidencia versionada. Discrepancias clínicas importantes bloquean declaración de validez clínica. No ejecutar terapias.

Prioridad: (1) micrófono físico EN/ES e inteligibilidad; (2) revisión clínica independiente y seguridad de despliegue; (3) nuevo banco ciego R2/pertinencia/preguntas fuera de capacidad; (4) ASR con habla humana diversa, ruido/canales/dispositivos reales; (5) cifrado y aislamiento antes de datos reales; (6) potencia instrumentada/hardware objetivo. No ampliar enfermedades antes de cerrar consistencia.