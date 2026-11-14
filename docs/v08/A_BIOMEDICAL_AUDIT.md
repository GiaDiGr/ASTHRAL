# A. Auditoría acotada del bloque biomédico v0.7.0

Entrega técnica v0.8.0 · 21-10-2026 · datos exclusivamente sintéticos.

## Alcance y conclusión

Se revisaron `docs/v07/README.md`, `docs/v07/CONTRACTS.md`, contratos clínicos previos, `monitoring.py`, `monitoring_models.py`, escenarios y pruebas del bloque longitudinal. No se repitió la auditoría general de las seis rutas anteriores. La suite completa comprueba regresiones del resto del proyecto. Los resultados reproducidos por software no constituyen validación clínica, espacial ni operativa.

El bloque es integrable como prototipo de investigación, sujeto a los límites siguientes. No habilita tratamientos ni un servicio autónomo de vigilancia de vuelo: los ciclos se solicitan explícitamente a la API.

## Problemas encontrados y correcciones

1. **Fase de misión de la medida actual:** una medida de otra fase podía alimentar el indicador actual o un enlace clínico del ciclo. Ahora el indicador informa `CURRENT_MISSION_PHASE_MISMATCH`, sin valor utilizable. El enlace clínico incompatible se representa como INVALID con procedencia explícita. No se sustituye silenciosamente por una medida antigua normal. La creatinina basal histórica conserva su excepción documentada.
2. **Identidad de muestras:** las observaciones enlazadas automáticamente compartían el identificador del contexto clínico como si fuera una única muestra. Ahora cada medición conserva su propio ID como identidad de muestra. El campo opcional `sample_ids` permite declarar una toma compartida real; solo acepta IDs de mediciones incluidas en la solicitud. El sistema no certifica esa declaración por sí solo.
3. **RAG/asistente, sin cambiar el criterio biomédico:** se corrigieron equivalencias bilingües de recuperación sobre radiación y un falso rechazo de la consulta informativa sobre dosis de radiación registrada. Véase el informe B.

No se modificaron umbrales de diagnóstico, protocolos, dosis terapéuticas ni el catálogo de enfermedades. La extensión de hipoglucemia mantiene su hash `b258ff2d79ab79355f65826466c9fc3e7a52380b749ec18ef2eb4700759e4fd8`.

## Matriz de cobertura revisada

| Bloque | Implementación comprobada | Verificación de software | Límite clínico/documental |
|---|---|---|---|
| Mediciones longitudinales | Ventanas declaradas, calidad, orden temporal, contexto/fase | Entradas inválidas, fases erróneas, muestras distintas, series tardías | No existe umbral universal validado de simultaneidad entre sensores |
| Baselines y tendencias | Baselines explícitos, comparación personal, pendiente, EWMA/CUSUM | Incompatibilidades, historia incompleta, escenario A | Estadística descriptiva; parámetros no son umbrales clínicos |
| Ciclos clínicos | Evaluación determinista con snapshots | 20 evaluaciones asociadas y replay por HTTP | Criterios satisfechos no equivalen a diagnóstico firmado |
| Alertas y episodios | Deduplicación, actualización, prioridad, seguimiento | Repetición sin nueva notificación, escalamiento a emergencia y replay | Prioridades de investigación; sin recuperación/cierre automático |
| Radiación | Suma de intervalos de dosis efectiva registrados, cobertura explícita | Huecos, orden inverso, solapamiento/duplicado sin doble conteo, escenario C | No convierte dosis de órgano/tasas; no calcula riesgo de cáncer ni dosis vitalicia |
| Cardiovascular | Indicadores y cambios de capacidad/valores | Escenario A, control de fase, baseline | No inferencia automática de POTS/hipotensión por una tendencia en microgravedad |
| Musculoesquelético | Fuerza y densidad cuando están disponibles | Escenario C y cobertura de ausencias | Cambio numérico no diagnostica enfermedad ósea/muscular |
| Inmunológico | Carga viral como observación descriptiva | Escenario C, calidad/historia | No predice inmunodeficiencia ni infección clínica por sí sola |
| Sueño/comportamiento | Duración, eficiencia, fatiga y reacción según datos disponibles | Escenario C y faltantes | No genera diagnóstico neuroconductual |
| Electrolitos/oxigenación | Medidas, calidad y restricciones separadas | Escenarios y contratos clínicos previos | No convierte vigilancia en autorización terapéutica |
| Hipoglucemia | Adulto con diabetes conocida; métodos admitidos; niveles y atribución clínica | Límites/ausencias del bloque v0.7 y escalamiento adicional | ADA 2026, tabla 6.4; CGM solo no se acepta; nivel 3 requiere atribución clínica; falta validación espacial |
| Persistencia/replay | Snapshots, hashes y auditoría | 15 ciclos/20 evaluaciones coincidentes; reader no escribe | Hash local no protege frente a propietario malicioso del almacenamiento |

## Evidencia y reproducibilidad

La fuente de hipoglucemia registrada sigue siendo ADA 2026, sección 6, DOI [10.2337/dc26-S006](https://doi.org/10.2337/dc26-S006). No se reconstruyó un protocolo terapéutico. Las fuentes S01/S16 y demás relaciones de vigilancia conservan las referencias del registro y las limitaciones del informe v0.7. Una síntesis de investigación no se presenta como artículo original ni como validación independiente.

Se verificó la integridad de los 105 archivos científicos originales y los 8 JSON del manifiesto clínico original. Se compararon los estados diagnósticos, urgencia, confirmación, protocolo y tratamiento de los escenarios anteriores y actuales. Los vectores clínicos coinciden; los hashes de implementación cambian legítimamente.

El replay requiere la implementación exacta. Se conservaron `before-v08.zip`, la entrega v0.7 y todas las bases anteriores. La demostración final utiliza `engine/data/portal-v080-final`; no se reescribieron hashes ni historias antiguas para hacerlas pasar con código distinto.

## Pruebas y resultados

Consulte `RESULTS.md`, `test-summary.json`, `tests-release.xml`, `live-release.json` e `integrity-and-modes-release.json` para los resultados finales exactos. Se añadieron 8 pruebas biomédicas, además de las 30 de monitorización previas. La suite final incluye todas las rutas antiguas, sus contratos y pruebas de seguridad.

## Pendientes para revisión humana

- Validar selección de ventanas, frecuencia de adquisición, caducidad de sensores y sincronización multimodal por escenario.
- Revisar aplicabilidad de criterios terrestres y métodos disponibles en misión; calibración/errores instrumentales no quedan resueltos por simulación.
- Revisar las políticas de prioridad, atribución de episodios y planes de seguimiento, sin confundirlas con órdenes médicas.
- Evaluar prospectivamente con profesionales y un protocolo apropiado antes de cualquier uso clínico.
- SQLite permanece sin cifrado. La auditoría es verificable dentro del diseño local; quien controla disco y código puede recalcularla. Se necesita aislamiento de procesos, ACL, gestión de secretos y una raíz de integridad externa para un despliegue más fuerte.
