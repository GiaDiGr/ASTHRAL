# VIGILE — PAQUETE REAL PARA CODEX (14-10-2026)

## QUÉ ES

Exportación local y verificable de cinco informes reales de Deep Research disponibles en la biblioteca del usuario, incluyendo el **documento original de 15 reglas JSON**, el último informe consolidado, y catálogos tabulares extraídos del último informe.

**Este archivo ZIP sí contiene archivos físicos reales**, no punteros a rutas sandbox remotas. Los archivos CSV/JSON se extrajeron del texto literal publicado en el informe final y no fueron generados mediante nueva investigación científica.

## EMPEZAR

1. Leer `10_CODEx_ESPECIFICACION/PROMPT_PARA_CODEX.md`.
2. Abrir `01_INFORMES/REPORTE_CONSOLIDADO_COMPLETO.md` y `01_INFORMES/15_REGLAS_ENTREGA_ORIGINAL_COMPLETA.md`.
3. Cargar el catálogo `03_CATALOGO/condiciones_con_rutas_y_cobertura.json` (44), y `03_CATALOGO/matriz_cobertura_44x11.csv`.
4. Cargar **las 15 reglas originales** desde `02_REGLAS_ORIGINALES_15/REGLAS_15_ORIGINALES.json` y **el inventario de 10 reglas reconstruidas** desde `02_REGLAS_ORIGINALES_15/inventario_10_reconstruidas.json`.
5. Auditar diferencias; **no mezclar reglas automáticamente**. La tabla de correspondencias solo sugiere candidatos.
6. Construir prototipo de investigación/simulación offline, no dispositivo médico validado.

## CONTENIDO

- `01_INFORMES`: investigación íntegra, referencias y contexto original.
- `02_REGLAS_ORIGINALES_15`: JSON original de 15 reglas con detalles científicos y pruebas, inventario de 10 reconstruidas y mapa de posibles coincidencias.
- `03_CATALOGO`: catálogo de 44 condiciones, rutas resumidas y matriz de 44 x 11 estados de cobertura.
- `04_ALGORITMOS`: 12 algoritmos documentados.
- `05_SENSORES`: 28 variables/sensores.
- `06_MULTISISTEMA`: 12 relaciones.
- `07_EVIDENCIAS`: 38 fuentes, 24 extracciones y URLs asociadas a investigaciones.
- `08_DATASETS`: 12 datasets o repositorios (no incluye los datos brutos de personas).
- `09_TESTS`: 20 pruebas sintéticas documentadas (textos para convertir en tests).
- `10_CODEx_ESPECIFICACION`: prompt, core model y ejemplo de regla CO2.
- `99_MATERIALES_HISTORICOS_SOLO_REFERENCIA`: archivos anteriores preservados como referencia, no para ejecución directa.

## LIMITACIONES IMPORTANTES

1. **Se recuperaron literalmente las 15 reglas del informe "PARTE 1"**, pero eso **no implica** que estén validadas para uso clínico ni que todas las fuentes/revisiones sean correctas. Codex debe hacer auditoría cruzada.
2. El último informe reconstruyó 10 reglas. Son un inventario y una regla de ejemplo, no diez JSON originales completos; las 10 no sustituyen las 15 ni se añaden ciegamente.
3. Las 44 rutas son perfiles abreviados y la matriz especifica estados. **No son 44 protocolos diagnósticos o terapéuticos aprobados**.
4. Los informes retienen tokens de cita propios de Deep Research, y la lista de URLs se extrajo de los registros de búsqueda guardados. La vinculación fina de todas las citas a páginas/versiones debe verificarse antes de activar una regla.
5. El antiguo supuesto `VIGILE_FINAL_BIOMEDICAL_KNOWLEDGE.zip` no fue recuperado ni incluido; los ZIP históricos presentes son otros archivos reales.
6. No hay sensores conectados, datos clínicos reales, validación médica, autorización NASA ni despliegue operacional.

## ESTADOS RECOMENDADOS

`RESEARCH_ONLY`, `REQUIRES_VALIDATION`, `REQUIRES_MISSION_AUTHORIZATION`, `REQUIRES_MEDICAL_AUTHORIZATION`, `NOT_PUBLICLY_AVAILABLE`, `INCONCLUSIVE`.

El LLM local será de solo lectura respecto al motor determinista y a autorizaciones; no puede crear diagnósticos ni prescribir.
