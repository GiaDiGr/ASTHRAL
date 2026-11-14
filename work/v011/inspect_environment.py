"""Read-only v0.10 baseline and preserved code before v0.11 edits."""
from pathlib import Path
import sys,json,hashlib,zipfile,sqlite3,importlib.metadata
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
import httpx
from vigile.store import Store,digest
from vigile.encrypted_storage import capabilities
from vigile.local_protection import verified_backup

folder=ROOT/'docs/v011';folder.mkdir(exist_ok=True)
archive=folder/'before-v011.zip'
if not archive.exists():
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for directory in ('engine/vigile','engine/tests','engine/tools'):
            for file in (ROOT/directory).rglob('*'):
                if file.is_file() and '__pycache__' not in file.parts:
                    z.write(file,file.relative_to(ROOT).as_posix())
        z.write(ROOT/'engine/pyproject.toml','engine/pyproject.toml')
bank=ROOT/'docs/v09/reserved-bank.json'
store=Store(ROOT/'engine/data/portal-v0100-integrated/vigile.sqlite3')
try:
    baseline={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
      'reserved_bank_sha256':hashlib.sha256(bank.read_bytes()).hexdigest(),
      'reserved_bank_action':'HASH_ONLY_NOT_EXECUTED','audit_valid':store.verify(),
      'checkpoint':store.checkpoint(),'record_count':store.db.execute('SELECT count(*) FROM records').fetchone()[0],
      'records_digest':digest([list(r) for r in store.db.execute('SELECT seq,kind,id,payload FROM records ORDER BY seq')]),
      'python':sys.version,'dependencies':{n:importlib.metadata.version(n) for n in ('fastapi','pydantic','uvicorn','httpx','pytest')},
      'storage':capabilities(),'services':{}}
finally:store.close()
with httpx.Client(trust_env=False,timeout=3) as client:
    for name,url in [('backend','http://127.0.0.1:8895/health'),('portal','http://127.0.0.1:8896/'),('ollama','http://127.0.0.1:8891/api/version')]:
        try:
            result=client.get(url);baseline['services'][name]={'status':result.status_code}
            if name!='portal':baseline['services'][name]['response']=result.json()
        except httpx.HTTPError as exc:baseline['services'][name]={'state':'UNAVAILABLE','error_type':type(exc).__name__}
destination=ROOT/'engine/data/backups/v0100-before-v011'
if not destination.exists():baseline['backup']=verified_backup(ROOT/'engine/data/portal-v0100-integrated/vigile.sqlite3',destination)
path=folder/'initial-environment.json'
if path.exists():raise ValueError('BASELINE_ALREADY_EXISTS_PRESERVE_ORIGINAL')
path.write_text(json.dumps(baseline,indent=2),encoding='utf8')
print(json.dumps(baseline,indent=2))
