# ASTHRAL — Biomedical / Health Intelligence Engine (v0.1.0 historical note)

ASTHRAL is the current project and product name. The deterministic biomedical engine and its original evidence lineage were first developed under the name VIGILE. The Python package remains `vigile` for compatibility with the documented API and historical datasets; this identifier is not the product brand.

This file records the original first-version runtime instructions. For the current product, browser experience, integration contracts, security boundaries and portability requirements, start with [README.md](README.md) and [docs/asthral/PORTABILITY_AND_GIT.md](docs/asthral/PORTABILITY_AND_GIT.md).

---
# VIGILE Health Intelligence Engine — v0.1.0

Motor local determinista de investigación/simulación. Implementado en Python, FastAPI, Pydantic 2 y SQLite, con pruebas pytest. No realiza diagnósticos, prescripciones ni intervenciones autónomas.

## Ejecutar en este equipo

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -m pytest -q
& '.\.venv\Scripts\python.exe' -m vigile demo
& '.\.venv\Scripts\python.exe' -m vigile serve
```

API en http://127.0.0.1:8765. `GET /health` público; demás rutas requieren Bearer token de `engine/data/tokens.json`. No publicar ni entregar tokens de escritura al LLM. Base creada en engine/data/vigile.sqlite3; no hay datos de personas. El servidor no queda ejecutándose después de la entrega.

## Instalación offline

Python 3.13 x64 instalado es requisito para los wheels incluidos. Desde engine ejecutar `powershell -NoProfile -File scripts/install_offline.ps1`, o crear venv y usar `python -m pip install --no-index --find-links wheelhouse -r requirements.lock`. No se consulta una red durante la ejecución del motor ni del demo. Los PDFs científicos externos no son necesarios en runtime. Al portar, conservar la documentación original junto a engine; VIGILE_CORPUS y VIGILE_DB permiten configurar rutas mediante la factory `uvicorn vigile.api:create_app --factory --host 127.0.0.1`.

## Estructura

- 01..10 y 99: documentación original intacta.
- engine/vigile: modelos, registro de evidencia, calidad/unidades, algoritmos, 15 comparadores, servicio, SQLite, API, CLI y demo.
- engine/tests: pruebas originales, TC001–TC020, seguridad, API e integración.
- engine/requirements.lock y wheelhouse: dependencias fijadas para instalación offline.
- engine/scripts: instalador y comprobación de servidor real.
- docs: auditoría, reconciliación, cobertura, evidencia, limitaciones, contratos, OpenAPI, resultados y contexto de continuidad.
- work/historical: ZIPs extraídos para inspección, conservando originales.

Leer docs/RULE_RECONCILIATION.md y docs/LIMITATIONS.md antes de integrar. Todas las evaluaciones operacionales quedan REQUIRES_VALIDATION. La cobertura 44×11 es representación documental; no son 44 protocolos clínicos validados.

