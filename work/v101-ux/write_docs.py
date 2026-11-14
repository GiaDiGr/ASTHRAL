from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'docs/v101-ux'
(D/'README.md').write_text('''# VIGILE v1.0.1 — experiencia del astronauta

Cierre incremental de presentación. No nuevo motor, enfermedades, algoritmos, terapias, umbrales, dosis, autorizaciones, servicios de Internet ni cambios de Ollama/Norton. La demostración reutiliza exactamente mission_demo seed=42 con el motor v1.0.1 existente; conserva fechas/mediciones/escenarios y resultados de R2. Los cuerpos de solicitud sólo añaden el default v1.0.1 resource_policy=DECLARED_R2, por lo que el hash de solicitudes completo cambia respecto a R2, pero es idéntico al retirar ese único campo. Hash semántico de resultados igual a R2 en http-and-invariance.json.

## Iniciar la demo preparada

Mientras el supervisor está activo: http://127.0.0.1:8912/ (backend 8911). No reiniciarlo sobre puertos ocupados. Para iniciarlo una vez detenido:

```powershell
Set-Location 'C:\\Users\\Gianni\\Desktop\\Vigile\\engine'
.\\.venv\\Scripts\\python.exe tools\\demo_astronaut_v101.py serve --output data\\mission-v101-astronaut
```

Obtener el código del portal sólo en una consola privada. No copiarlo a informes/prompts ni utilizar un token backend como código:

```powershell
Set-Location 'C:\\Users\\Gianni\\Desktop\\Vigile\\engine'
.\\.venv\\Scripts\\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/mission-v101-astronaut/portal-access.txt'))"
```

Guion: DEMO_5_MIN.md. El usuario navega por los selectores Astronauta/misión y Momento de misión. El panel Tu recorrido de salud abre mediciones/tendencias, hallazgos, prevención, evaluación/manejo y seguimiento. No crea resultados o relaciones. Un botón de evaluación sólo aparece si el ID está explícitamente en clinical_evaluations del ciclo y en la proyección autorizada. Cambiar fecha invalida contexto anterior; una evaluación de otra fecha queda identificada, con vínculo al checkpoint de origen. Urgencia preservada con fechas/IDs de sus contextos.

## Repetición independiente, con directorio NUEVO

```powershell
Set-Location 'C:\\Users\\Gianni\\Desktop\\Vigile\\engine'
$py = '.\\.venv\\Scripts\\python.exe'
& $py tools\\demo_astronaut_v101.py prepare --output data\\mission-v101-astronaut-repeat
& $py tools\\demo_astronaut_v101.py verify --output data\\mission-v101-astronaut-repeat --report ..\\work\\v101-ux\\repeat-verification.json
& $py tools\\demo_astronaut_v101.py serve --output data\\mission-v101-astronaut-repeat
```

prepare rechaza una carpeta existente; verify rechaza un informe existente. Para segunda repetición usar otros nombres. serve reutiliza supervisor v1.0.1: sólo loopback, puertos 8911/8912, rechaza ocupados y termina sólo sus propios hijos al finalizar. No altera procesos R2/v1.0.1/Ollama. La demo descarta bootstrap researcher y conserva credenciales nuevas protegidas por DPAPI/ACL para reader y adquisición. El portal sigue siendo reader; no puede crear inventario, tratamientos, mediciones o seguimiento clínico.

## Pruebas

```powershell
Set-Location 'C:\\Users\\Gianni\\Desktop\\Vigile\\engine'
.\\.venv\\Scripts\\python.exe -m pytest -q --junitxml=..\\work\\v101-ux\\my-full-tests.xml
.\\.venv\\Scripts\\python.exe -m pytest tests\\test_astronaut_ux_v101.py tests\\test_management_v101.py -q
```

Se reutilizan dependencias existentes. Python>=3.11, FastAPI/Pydantic/SQLite/pytest/httpx; Windows DPAPI para demo protegida. Node sólo para DOM simulado (si falta, pytest lo declara omitido). No nuevas dependencias, descargas o pesos. Suite exacta y tiempos en RESULTS.json y XML. Las pruebas no son validación clínica. La inspección visual real falló al inicializar el kernel Computer Use, antes de abrir navegador; no sustituida por automatización alternativa. Checklist humano en MANUAL_VISUAL_QA.md. Voz física sigue pendiente; no se solicitó micrófono ni se cambió Ollama.

## Límites

Mediciones ausentes/invalidas/desactualizadas/contradictorias no significan normalidad. La tendencia y el requisito normativo no son diagnóstico. Fuentes y contramedidas proceden del catálogo previo; no se elevó su evidencia. Algunas fichas no estructuran condiciones/recursos: la vista declara esa limitación y no infiere hardware disponible. Cognición/inmunidad muestran datos/incertidumbre/biblioteca, sin nueva contramedida integrada. No se supone disponibilidad a bordo de DXA, laboratorio o pruebas terrestres. No hay pauta personalizada ni nuevas horas, dosis, ejercicios, umbrales o agenda de prevención.

La misión longitudinal usa recursos DECLARED_R2, no inventario NASA ni disponibilidad ficticia. Todas las intervenciones continúan AUTHORIZATION_REQUIRED/NO_VERIFIED_MISSION_POLICY y clinical_execution=BLOCKED. Datos históricos no se rellenan con inventario actual. Planes conocidos con fecha de revisión futura son planes, no eventos ya realizados. No se infiere cierre de un aviso antiguo por ausencia de datos.

SQLite/WAL/backups sin cifrado; DPAPI/ACL no aíslan procesos de la misma cuenta ni impiden manipulación por control del almacenamiento. Mantener datos sintéticos. Revisión médica pendiente de docs/v101/CLINICAL_REVIEW.md intacta. Integración opcional de Internet corresponde a otro integrante: ver OPTIONAL_INTERNET_RAG_CONTRACT.md, sólo documentación, sin código nuevo de red.
''',encoding='utf8')
(D/'FLOW_AND_CHANGES.md').write_text('''# Flujo comprobado y cambios acotados

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
''',encoding='utf8')
(D/'MANUAL_VISUAL_QA.md').write_text('''# Inspección visual humana pendiente

Estado: NO COMPLETADA. Computer Use/node_repl falló dos veces (incluido reset) antes de abrir navegador: failed to write kernel assets: Impossibile trovare il percorso specificato. (os error 3). HTTP y DOM simulado no verifican píxeles, layout, accesibilidad real o foco. No se usó Playwright ni otro navegador alternativo para afirmar inspección.

Registrar persona, fecha, navegador, resolución, zoom y resultado de cada punto; adjuntar captura sin códigos/tokens/sesión. Usar sólo datos sintéticos. No cambiar seguridad de Windows/Norton, Ollama ni permisos de micrófono para completar esta tarea.

- [ ] Abrir http://127.0.0.1:8912/ y entrar con código protegido, nunca token backend. Comprobar que no queda visible tras login.
- [ ] A 35: nombre/misión/fase/gravedad/checkpoint/fecha legibles. Cinco pasos accesibles por ratón y teclado; foco visible.
- [ ] Gráfica VO2 con unidades/fechas, puntos observados y baseline del ciclo. Tabla coincide con puntos; no solapamientos a 100%/200% de zoom.
- [ ] A 21: músculo inválido, sueño con fase incompatible, frecuencia cardíaca contradictoria y muestra obsoleta no aparecen como normales. La información pendiente se lee sin depender sólo de color.
- [ ] Prevención abre orientación; fuentes legibles; biblioteca no aparece como orden personalizada; recursos no estructurados se distinguen de recursos verificados/no disponibles.
- [ ] Cambiar astronauta A→B y checkpoint: no quedan datos, chat, recomendaciones o asociaciones de A. Verificar respuesta lenta/error con contexto vacío y mensaje claro.
- [ ] B 18: DKA CRITERIA_MET, EMERGENCY y potasio pendiente, bicarbonato/cetonas urinarias opcionales. Banner visible también en Seguimiento/Asistente.
- [ ] B 18.1: potasio disponible en reevaluación, autorización aún bloqueada, tratamiento NOT_STARTED; revisión documental de capacidad IV no equivale a orden.
- [ ] B 47 seleccionando evaluación B 18: se advierte fecha distinta; botón lleva al checkpoint origen sin inventar asociación temporal.
- [ ] Seguimiento: episodio/plan/fecha/estado legibles; no se muestra recuperación confirmada ni acción administrada por VIGILE.
- [ ] Si no hay radiación, hueso, cognición o inmunidad medidos, se muestra ausencia/incertidumbre y no normalidad. No presentar cobertura de sensores como disponibilidad en vuelo.
- [ ] A 47: contexto postmisión y biblioteca de retorno, sin extrapolación automática a microgravedad.
- [ ] Estrecho/móvil: controles, tablas con scroll, menús, fuentes y alerta permanecen utilizables; sin recortes/horizontal global.
- [ ] Desconectar Internet de forma manual SIN bloquear localhost; refrescar y navegar resultados/checkpoints. No cerrar Ollama ni cambiar configuración de protección. Motor determinista y biblioteca local siguen disponibles.
- [ ] FULL/LOW_POWER/CRITICAL: revisar visualmente estado/limitaciones. No confundir no inferencia con descarga de memoria; ninguna selección autoriza terapia.
- [ ] Logout y expiración: contenido oculto/sesión invalidada. Voz física STT/TTS sigue pendiente y requiere prueba humana aparte; no declarar realizada por ver botones.
''',encoding='utf8')
print('Wrote flow, commands and manual visual QA checklist')