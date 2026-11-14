# VIGILE v0.10.0 — Entrega de integración

Prototipo local de investigación. Datos sintéticos; tratamientos bloqueados. Informes: [auditoría computacional](A_COMPUTATIONAL_AUDIT.md), [desarrollo e infraestructura](B_FULLSTACK_INFRASTRUCTURE.md), [contratos](INTEGRATION_CONTRACTS.md), [demostración](DEMO.md).

Base activa: `C:\Users\Gianni\Desktop\Vigile\engine\data\portal-v0100-integrated`. No iniciar sobre una base histórica con el código nuevo para simular que se ha reproducido su versión original; utilizar el código archivado correspondiente.

## Arranque exacto en Windows

Los servicios pueden estar ya activos. Comprobar primero:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8895/health'
Invoke-RestMethod 'http://127.0.0.1:8891/api/version'
```

Solo si están detenidos, abrir tres terminales locales. No ejecutar instancias duplicadas ni detener procesos de otro trabajo.

Terminal 1, backend:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -m vigile serve --integration-dir '.\data\portal-v0100-integrated' --port 8895
```

Terminal 2, portal:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -m vigile.portal --config '.\data\portal-v0100-integrated\portal-config.json' --port 8896
```

Terminal 3, Ollama, solamente si 8891 está libre:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' '.\tools\start_ollama_vigile.py'
```

Abrir [portal local](http://127.0.0.1:8896/). El código del portal existente se conserva. Si se necesita consultarlo en la terminal privada del usuario, mostrar **solo el código de acceso del portal**, nunca el token reader:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -c "from vigile.local_protection import read_secret; print(read_secret('data/portal-v0100-integrated/portal-access.txt'))"
```

DPAPI requiere la misma identidad Windows que protegió estos archivos. Para otra máquina/cuenta se necesita reaprovisionamiento seguro de credenciales; no distribuir estos archivos como si fueran portables.

## Verificación exacta

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -m pytest -q
& '.\.venv\Scripts\python.exe' '..\docs\v010\verify_release.py'
& '.\.venv\Scripts\python.exe' '..\docs\v010\client_example.py'
& '.\.venv\Scripts\python.exe' -m vigile.local_protection verify-anchor --database '.\data\portal-v0100-integrated\vigile.sqlite3' --anchor "$env:LOCALAPPDATA\Vigile\integrity\v0100-integrated.anchor.json" --key "$env:LOCALAPPDATA\Vigile\integrity\audit-key.dpapi"
```

Resultado de entrega: 561 pruebas aprobadas; 39 replays; 24 evaluaciones clínicas iguales a v0.9; auditoría/anclaje válidos y banco reservado intacto. `release-tests.xml`, `release-verification.json`.

## Preparar otra demostración sintética

Estos comandos crean carpetas nuevas y fallan si ya existen. Elegir otro nombre para una repetición; nunca sobrescribir la base activa.

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -m vigile.monitoring_portal_demo --output '.\data\portal-v0100-demo-new' --reuse-config '.\data\portal-v090-release\portal-config.json'
& '.\.venv\Scripts\python.exe' '..\docs\v010\protect_demo.py' --folder '.\data\portal-v0100-demo-new' --backup '.\data\backups\v0100-demo-new' --anchor "$env:LOCALAPPDATA\Vigile\integrity\v0100-demo-new.anchor.json" --key "$env:LOCALAPPDATA\Vigile\integrity\audit-key.dpapi"
```

El primer comando reutiliza solamente la configuración y credenciales sintéticas históricas y crea 15 ciclos, 24 evaluaciones incluyendo escenarios del portal. El segundo protege los nuevos secretos y verifica copia/anclaje. No es simulación clínicamente validada ni presupone disponibilidad real de todos los sensores.

Generador de datos general, sin importarlos a la base activa:

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -m vigile simulate --seed 42 --output '.\data\synthetic-v010-new.json'
```

## Copia y recuperación sin sobrescritura

```powershell
Set-Location 'C:\Users\Gianni\Desktop\Vigile\engine'
& '.\.venv\Scripts\python.exe' -m vigile.local_protection backup --database '.\data\portal-v0100-integrated\vigile.sqlite3' --destination '.\data\backups\manual-v0100-01'
& '.\.venv\Scripts\python.exe' -m vigile.local_protection restore --backup '.\data\backups\manual-v0100-01' --destination '.\data\restored-v0100-01'
```

No se migra esquema ni se sustituye la base en ejecución. Revisar manifest, SHA-256, auditoría y replays antes de seleccionar una restauración. Respaldar también el código/registro de evidencia de su versión; las credenciales y el material de integridad se gestionan por separado y siguen ligados al usuario Windows. SQLite y copias siguen sin cifrado.

## Requisitos y estructura

Python declarado >=3.11; entorno probado y versiones efectivas en `dependencies.json`. FastAPI, Pydantic, Uvicorn, httpx y pytest existentes. No se añadieron paquetes externos. DPAPI y ACL requieren Windows. SQLCipher es opcional y no está instalado ni activo.

```text
engine/vigile/             motor existente, BFF y protección local
engine/vigile/web/         frontend reutilizado y reorganizado
engine/tests/             suite original + 16 regresiones
engine/tools/             lanzador portable existente, entorno filtrado
engine/data/portal-v0100-integrated/   demostración activa y secretos DPAPI
engine/data/portal-v090-release/      historia v0.9 conservada
engine/data/backups/       snapshots verificados, sin cifrado
engine/local_ai/           Ollama, modelo y biblioteca originales
docs/v010/                dos informes, contratos, comandos, capturas y mediciones
work/v010-v09-replay/      código v0.9 extraído para comprobar restauración
%LOCALAPPDATA%/Vigile/integrity/       anclajes y clave DPAPI; fuera del paquete
```

## Integración con el equipo

Frontend usa BFF 8896 y cookie, sin token backend. IA/RAG recibe exclusivamente reader/proyecciones verificadas; las reglas y autorizaciones siguen en el motor. Sensores/simuladores usan los contratos backend ya existentes y una credencial de adquisición aprovisionada por separado; ninguna se obtiene del portal. Space Computing modifica presupuestos de inferencia sin cambiar criterios, snapshots ni resultados del motor.

Prioridades: aislamiento real entre procesos, cifrado SQLite y recuperación de claves; revisión sanitaria independiente y aplicabilidad espacial; pertinencia documental; carga prolongada y potencia instrumentada. No hay validación clínica, operativa ni espacial.

## CONTEXTO PARA CONTINUAR CON CHATGPT

VIGILE v0.10.0. Base activa portal-v0100-integrated; backend 8895, portal 8896, Ollama 8891, modelo vigile-qwen3-4b:latest. Python hash c896211d20b52ade1279aeb306421891f5e29b542f910074d542321c4b815db9; conocimiento b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e. 561 pruebas; 39 replays; 24 vectores clínicos iguales; banco reservado intacto. Cinco áreas de interfaz, sesiones acotadas, control de origen/roles/scopes, errores seguros, calidad/contexto histórico, fuente exacta y metadatos de intentos/aceptación. DPAPI/ACL en archivos nuevos, HMAC externo; SQLite/copias sin cifrado, procesos del mismo usuario no aislados. SQLCipher preparado pero no integrado. Mantener criterios y tratamientos bloqueados. Ejecutar los comandos de verificación anteriores antes de cambiar código; los replays exigen la versión de implementación correspondiente.

El ZIP de código/revisión no incluye credenciales, bases, modelo ni el corpus científico completo: se aplica al proyecto original conservado. Los paquetes de versiones anteriores dentro de docs/v010 permiten revisar la historia del código; los anclajes y su clave permanecen fuera.
