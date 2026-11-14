# Flujo comprobado y cambios acotados

## Lo que ya existía

Selección de astronauta/misión, checkpoints de recepción inmutables, 26 ciclos para dos astronautas, métricas/calidad, gráfica temporal y tabla, baselines/tendencias, hallazgos normativos, siete rutas clínicas y diferencial, árboles AND/OR, episodios/seguimiento, manejo documental v1.0.1, permisos reader, prioridades persistentes y replays. Se reutiliza todo. No se hizo nueva auditoría general.

## Brechas comprobadas y correcciones

1. Navegación fragmentada: panel permanente Tu recorrido de salud con cinco accesos; abre explícitamente prevención y hallazgos, sin mutaciones ni relaciones nuevas.
2. Selección clínica y ciclo podían corresponder a fechas diferentes: la UI identifica IDs/fechas y vínculo explícito, avisa si difieren, y permite ir al checkpoint origen. No asigna causalidad ni simultaneidad. Se verifica ámbito y contexto después de la carga asíncrona; respuestas tardías de otro astronauta/checkpoint se descartan.
3. La gráfica buscaba cualquier baseline visible por variable: ahora sólo dibuja el que el motor realmente comparó en el ciclo seleccionado, y sólo en unidades compatibles con la serie. Unidades heterogéneas no se grafican juntas; la tabla mantiene las unidades originales. Sin nuevas conversiones/algoritmos.
4. Indicadores/limitaciones principalmente técnicos: nueva orientación por indicador con qué se midió, estado utilizable o motivo de ausencia, baseline utilizado y cambio, pendiente ya calculada, incertidumbre, riesgos del catálogo como biblioteca (no diagnóstico), fuente legible y límites de prevención. Traducciones de estados/limitaciones preexistentes, sin contenido médico nuevo.
5. La biblioteca de contramedidas podía seleccionarse por variables históricas o por cognición genérica: ahora la selección documental usa indicadores utilizables del ciclo; cognición no implica automáticamente contramedidas de sueño/fatiga. Con dato no utilizable no se presenta una contramedida como acción indicada. Las contramedidas no mapeadas/recursos no estructurados quedan explícitos, no completados por suposición.
6. La prioridad persistía pero podía ser temporalmente ambigua: se mantienen prioridad y aviso de no cierre, añadiendo IDs/fechas visibles. No cambia urgencia ni criterios del motor.
7. Carga/error: los accesos y contexto de la vista anterior se vacían al empezar carga; no quedan asociaciones antiguas bajo otro astronauta. HTTP/DOM cubren fallos y cambio de contexto.

## Archivos

Modificados: engine/vigile/web/index.html (panel), app.js (limpieza y baseline/unidades gráfica), management.js (orientación/navegación/biblioteca/fechas), style.css (estilo mínimo), engine/tests/management_ui_unit.cjs (adaptación del harness a ciclo con ámbito).
Nuevos: engine/tools/demo_astronaut_v101.py, engine/tests/test_astronaut_ux_v101.py, engine/tests/astronaut_ui_unit.cjs; docs/v101-ux, work/v101-ux y punto de entrada VIGILE_v101_ASTRONAUT_START_HERE.md.

Ningún engine/vigile/*.py, clinical_knowledge/*.json, protocolo o fuente científica original modificado. Sin endpoints nuevos, cambios de SQL, permisos o integración de red. Runtime implementation_hash de v1.0.1 permanece igual; los assets tienen nuevo hash y archivo separado UX. Archivos exactos y hashes en CHANGE_MANIFEST.json/CODE_FREEZE_UX.json. R2 y v1.0.1 originales recuperables, con backup privado verificado antes de editar.

## Cobertura de los cuatro objetivos indicados por el usuario

| Objetivo | Flujo disponible | Límite |
|---|---|---|
| Autoevaluación visual | Métricas, gráfica/tabla, baselines, estados y checkpoints | No diagnóstico firmado; lectura de registros, sin autodiagnóstico automático |
| Recopilación/interpretación | Adquisición existente y resultado determinista de ciclo, calidad y tendencias | No formulario nuevo reader ni dispositivos presumidos |
| Orientación sobre tratamientos | Evaluación → manejo documental → condiciones/recursos/autoridad → seguimiento | Todo bloqueado para ejecución y pendiente de revisión humana |
| Mejora/prevención | Biblioteca contextual del catálogo, fuentes, condiciones y límites por indicador | No pauta individual; recursos específicos de varias contramedidas sin estructurar |

No se verificó aquí el texto externo oficial del reto; se atendieron los cuatro objetivos explícitos de esta solicitud. No gamificación ni figura humana nueva. No predicción individual, dosis por gravedad o terapias adicionales.
