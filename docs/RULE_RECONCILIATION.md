# Reconciliación de reglas — 2026-10-14

Se conservaron los 15 objetos originales, las 15 copias individuales y el inventario reconstruido de 10 entradas. No son 25 reglas independientes.
Las nueve correspondencias siguientes comparten requisito y comparación básica; el inventario abreviado no reproduce todas las precondiciones, autorizaciones, ventanas o exclusiones del original. Se elige el original como especificación de simulación; no se fusionan fuentes ni se activan automáticamente aliases R-*.

| Original | Reconstruida | Decisión |
|---|---|---|
| VIGILE-AER-001 | R-AER-001 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-AER-002 | R-AER-002 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-AER-003 | R-AER-003 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-MUS-001 | R-MUS-001 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-MUS-002 | R-MUS-002 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-BONE-001 | R-BONE-001 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-RAD-001 | R-RAD-001 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-ENV-002 | R-CO2-001 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |
| VIGILE-ENV-003 | R-PRESS-001 | Coincide el núcleo numérico; se ejecuta solo el original en simulación. Sin equivalencia operacional certificada. |

Seis originales no tienen contraparte en las diez: NUT-001, RAD-002/003/004, ENV-001/004. R-ORTHO-001 es adicional: representa disponibilidad de contramedidas, no un test diagnóstico. Queda REQUIRES_MISSION_AUTHORIZATION sin comparador operacional. La biblioteca contiene 15 comparadores de simulación, 10 registros reconstruidos conservados y un estado explícito para ortostatismo.

## Diferencias y contradicciones

- El consolidado afirma que las 15 no estaban recuperadas. El paquete actual sí las recupera del informe PARTE 1; este informe, a su vez, declara que reconstruyó las reglas desde fuentes primarias. «Original» significa original de esa entrega, no recuperación del ZIP perdido.
- Los IDs R-AER-01/R-CO2-01 en extracciones/casos no coinciden literalmente con R-AER-001/R-CO2-001. Se conservan; no se usan como IDs ejecutables.
- S27 identifica OSD-198 en fuentes, pero C015/C027 lo mencionan para CO2. C027 en la matriz integrada solo refiere S02. Conflicto semántico registrado, sin alterar el original ni resolver S27 hacia un documento distinto.
- El original aporta páginas de V2 Rev F que el consolidado marca NOT_FOUND. La consulta puntual al PDF oficial confirmó Rev F y V2 6004 p.51 / V2 6020 p.58. No equivale a validar el conjunto completo.
- Nutrición: original 100% de provisión, no 90%, ni consumo real o diagnóstico de deficiencia. Ventanas/objetivos requieren protocolo de misión.
- CO2: promedio horario, no pico ni lectura aislada. La agregación implementada exige medias de intervalos contiguos que cubran exactamente 3600 segundos. Esta política conservadora es ingeniería, no frecuencia NASA.
- Presión: límite inferior estricto; dosis/radiación también preservan sus desigualdades estrictas. No se redondea antes de comparar.
- Carrera, SPE de diseño, tecnología nuclear y tasa GCR son magnitudes/contextos distintos. No se suman dosis de órgano, dosis médicas o tasas a la dosis efectiva de carrera.
- BMD: resultados por sitio; faltar un sitio requerido deja el global INCONCLUSIVE. TC007 verifica incumplimiento de cadera; no prueba cumplimiento global de los tres sitios ni riesgo de fractura.
- Los reportes anteriores mencionan SANS/OCT 20 µm, orina 2 L/día, PIO2, tablas de órgano y DCS de validación terrestre. No están en los 15 objetos ejecutables: permanecen pendientes, no se reconstruyen umbrales desde resúmenes.
- RMA tiene expansión médica/misión ambigua entre textos. Se preserva literalmente en cobertura, sin tratar ambos permisos como equivalentes.
- Los antiguos 13 comparadores, 34 condiciones y 53 fuentes son conteos de otro paquete no recuperado; no sustituyen los conteos reales actuales.

## Activación

Todas las reglas: estado operacional REQUIRES_VALIDATION, ejecución clínica BLOCKED. Solo SIMULATION con perfil, misión y mediciones marcados synthetic permite comparadores. Banderas de aprobación en los escenarios son supuestos sintéticos; nunca conceden autorización. No hay endpoint para activar reglas o protocolos.
