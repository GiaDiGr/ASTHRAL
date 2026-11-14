> Configuración vigente tras la corrección de consistencia: [CONSISTENCY_AUDIT.md](../docs/ai/CONSISTENCY_AUDIT.md). Usar `portal-consistency-v061`; los comandos previos con `portal-v06-final` corresponden a la demostración histórica conservada.

> Actualización 19/10/2026: IA local recuperada con Ollama oficial. Configuración vigente, pruebas y arranque: [OLLAMA_RECOVERY.md](../docs/ai/OLLAMA_RECOVERY.md). Las notas de bloqueo anteriores son históricas.

# VIGILE 0.6.0 — IA local y modos de operación

298 pruebas aprobadas. Inferencia real ejecutada con Qwen3-4B Q4_K_M y llama.cpp. **Estado actual: CRITICAL operativo; FULL bloqueado porque desapareció llama-server.exe durante un reinicio. Causa pendiente de revisión; no desactivar seguridad ni restaurar automáticamente.**

Entrega vigente: [docs/ai/DELIVERY.md](../docs/ai/DELIVERY.md), con resultados reales, comandos, contratos y límites. Criterios médicos intactos, sin validación clínica ni tratamiento autorizado.

---

# VIGILE 0.5.0 — Dashboard y consulta local

Integración incremental. 275 pruebas aprobadas. No validación clínica ni ejecución terapéutica. Frontend funcional y RAG extractivo; inferencia local opcional no instalada en la entrega.

Entrega vigente: [docs/portal/DELIVERY.md](../docs/portal/DELIVERY.md). Contratos: [CONTRACTS.md](../docs/portal/CONTRACTS.md). Incluye comandos para demo, backend y portal. La documentación histórica de v0.4 y anteriores se conserva debajo.

---

# VIGILE Health Intelligence Engine — v0.4.0

Ampliación clínica determinista de investigación. Criterios computables, no diagnósticos clínicamente validados ni autorización terapéutica.

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile clinical-demo
& .\.venv\Scripts\python.exe -m vigile serve --port 8765
```

Entrega y contratos actuales: ../docs/clinical/DELIVERY.md, INTEGRATION.md, DECISIONS.md y openapi-v04.json. 251 pruebas aprobadas. El historial de integración v0.3 se conserva a continuación; su conteo y ejemplos corresponden a esa versión.

---

# VIGILE Health Intelligence Engine — v0.3.0

Motor determinista local de investigación. Sin validación clínica ni operacional. No diagnósticos, prescripciones ni intervenciones autónomas. Los originales se conservan.

Desde esta carpeta:

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m vigile integration-demo --seed 42
& .\.venv\Scripts\python.exe -m vigile serve --integration-dir data\spaceapps-demo --port 8765
```

Demo completa crea una carpeta nueva, ejecuta HTTP end-to-end, verifica persistencia y termina su servidor. La carpeta data/spaceapps-demo de entrega permite conectar clientes a http://127.0.0.1:8765. Credenciales en archivos privados separados; nunca entregues frontend-token o credenciales de escritura al LLM.

Documentación: ../docs/INTEGRATION_DELIVERY_V03.md (comandos y contratos por equipo), ../docs/openapi.json (esquemas), ../docs/API_EXAMPLES_V03.json (tráfico sintético sin tokens), ../docs/PERFORMANCE_V03.json y ../docs/integration-tests.xml. 172 pruebas aprobadas. Simulador: python -m vigile simulate --seed 42.

Instalación offline: scripts/install_offline.ps1 requiere Python 3.13 x64 y usa requirements.lock/wheelhouse sin índice remoto. No dependencias nuevas descargadas; HTTPX ya incluido se utiliza en integración. Motor normal: python -m vigile serve, base principal independiente. SQLite no está cifrada; requeridos aislamiento de procesos y revisión biomédica antes de datos reales.

