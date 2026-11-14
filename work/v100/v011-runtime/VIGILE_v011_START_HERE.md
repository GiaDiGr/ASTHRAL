# VIGILE v0.11.0 — Integrated Mission

Implementación y demostración local de investigación. La documentación original y las bases anteriores se conservan.

- [Comandos y contexto técnico](docs/v011/README.md)
- [A. Auditoría Full-stack / Infrastructure](docs/v011/A_FULLSTACK_AUDIT.md)
- [B. Simulación integral de misión](docs/v011/B_INTEGRATED_MISSION.md)
- [Contratos para el equipo](docs/v011/INTEGRATION_CONTRACTS.md)
- [Guion de cinco minutos](docs/v011/DEMO.md)
- [Resultados reales y hashes](docs/v011/RESULTS.json)

Nueva base: engine/data/mission-v011-final. Backend 8897, portal 8898; 0.10 se conserva en 8895/8896. Ollama permanece en 8891 con vigile-qwen3-4b:latest.

582 pruebas aprobadas; 26 ciclos, 50 evaluaciones clínicas y 76 reproducciones coincidentes. Son pruebas sintéticas de software: no validación clínica, operativa o espacial. Tratamientos bloqueados. SQLite/backups sin cifrar y procesos de misma cuenta sin aislamiento efectivo.