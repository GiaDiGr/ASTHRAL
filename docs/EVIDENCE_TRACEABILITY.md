# Evidencia y trazabilidad

`DOCUMENT_AUDIT.json`: inventario completo, SHA-256, estructura de JSON/CSV, secciones de informes, 24 miembros de ZIP y duplicados idénticos. Los ZIP originales se conservan; las copias extraídas viven en `work/historical/`.
`TRACEABILITY_MATRIX.json`: 15 reglas → entradas, requisitos/localizadores, candidatos Cxxx, etapa, tests y bloqueo operacional. Los candidatos Cxxx son enlaces de ingeniería, no equivalencias diagnósticas.
`SOURCE_REVISIONS.json`: revisiones declaradas y alcance real de verificación externa. No se descargaron ni redistribuyeron artículos científicos externos ni datos de personas.

El importador verifica los 105 hashes del manifiesto, conteos, IDs únicos, referencias de fuentes, las 15 copias individuales y la matriz 44×11 contra los registros integrados. Fuentes 38; extracciones 24; enlaces de investigación 833. Se conserva el texto original, incluidos tokens de cita que no son resolubles por sí solos offline.

Cada evaluación persiste regla completa y hash, hash del corpus, hash de implementación, versión del algoritmo, perfil/misión, mediciones, dispositivos, conversiones, tiempo as_of explícito, entradas normalizadas, contexto y decisión. El ID es hash del bundle; repetirlo no crea otro hallazgo. El replay de comparadores vuelve a calcular sobre el snapshot. Para bloqueos previos se verifica integridad del bundle; no se afirma reejecución de todos los quality gates. Un cambio de implementación requiere conservar el ejecutable anterior para reproducirlo.

La auditoría SQLite usa transacciones, triggers que impiden UPDATE/DELETE y cadena hash. Cada registro se ancla en su evento. Detecta modificaciones respecto a esa cadena; no protege frente a un administrador que reescriba archivo y cadena o trunque ambos. Requiere sellado externo/backup protegido para producción.

Consulta puntual oficial: [Volumen 1](https://standards.nasa.gov/standard/NASA/NASA-STD-3001_VOL_1), [PDF Volumen 2 Rev F](https://standards.nasa.gov/system/files/tmp/NASA-STD-3001%20Vol%202%20Rev%20F.pdf). Estas consultas no habilitan uso clínico.
