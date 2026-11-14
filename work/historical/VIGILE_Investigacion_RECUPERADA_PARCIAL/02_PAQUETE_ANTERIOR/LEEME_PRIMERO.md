# VIGILE — paquete revisado para Codex

**Empieza copiando el texto íntegro de `PROMPT_CODEX_CON_EVIDENCIA_PRIMARIA.md` en Codex, y añade todos estos archivos como entrada al repositorio o sesión.**

## Lo que sí se revisó

- Las normas NASA-STD-3001 Vol. 1 Rev. C y Vol. 2 Rev. F, con secciones y tablas localizadas; además, partes relevantes de los informes NASA de hueso 2024 y sueño 2016.
- El abstract original de un estudio cardiovascular de 2025 (no el artículo completo).
- La relación de fuentes recopiladas en el primer Deep Research.

## Lo que NO se afirma

- No se auditaron íntegramente todos los artículos, guías y datasets.
- Las 35 entradas de `PRIMARY_EVIDENCE_LOCATORS.csv` NO son 35 protocolos médicos completos ni 35 reglas clínicamente certificadas.
- Requisitos normativos, análisis estadísticos y decisiones terapéuticas están claramente separados.
- Algunos apartados y condiciones deben volver a comprobarse en la versión oficial que Codex descargue antes de activar reglas de cumplimiento.

## Orden de lectura

1. `PROMPT_CODEX_CON_EVIDENCIA_PRIMARIA.md`
2. `AUDITORIA_Y_PROTOCOLOS.md`
3. `PRIMARY_EVIDENCE_LOCATORS.csv`
4. `evidence_registry.csv`, `clinical_coverage.csv`, `evidence_gaps.csv`, `datasets_registry.csv`
5. `rule_template_RESEARCH_ONLY.json`
6. `DEEP_RESEARCH_1_ORIGINAL.md`

El informe final que Codex escriba en el chat se compartirá con ChatGPT para continuar las decisiones biomédicas e ingenieriles.
