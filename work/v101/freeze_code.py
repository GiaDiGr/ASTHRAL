from pathlib import Path
import json,sys,zipfile,hashlib,importlib.metadata,platform
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));D=R/'docs/v101'
from vigile.local_protection import verified_backup,restrict_directory
backup=verified_backup(R/'engine/data/mission-v101-final/vigile.sqlite3',R/'work/v101/final-db-backup');restrict_directory(R/'work/v101/final-db-backup');(D/'demo-backup-checkpoint.json').write_text(json.dumps(backup,indent=2),encoding='utf8')
old=zipfile.ZipFile(R/'docs/v100/candidate-code-r2.zip');change=json.loads((D/'change-manifest.json').read_text());names=sorted(set(old.namelist())|{x['path'] for x in change['added_implementation']})
assert all(not p.startswith(('engine/data/','engine/.venv/','work/')) for p in names)
files=[{'path':p,'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest()} for p in names]
with zipfile.ZipFile(D/'candidate-code-v101.zip','x',zipfile.ZIP_DEFLATED) as z:
 for row in files:z.write(R/row['path'],row['path'])
with zipfile.ZipFile(D/'candidate-code-v101.zip') as z:
 assert all(hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256'] for row in files)
freeze={'version':'1.0.1','implementation_hash':json.loads((D/'demo-report.json').read_text(encoding='utf8'))['scenarios'][0]['evaluation']['implementation_hash'],'archive':'candidate-code-v101.zip','sha256':hashlib.sha256((D/'candidate-code-v101.zip').read_bytes()).hexdigest(),'files':files,'excludes':['databases','credentials','weights','virtualenv','private-work-artifacts'],'synthetic_only':True,'clinical_execution':'BLOCKED'}
(D/'CODE_FREEZE.json').write_text(json.dumps(freeze,indent=2),encoding='utf8')
(D/'environment.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ('fastapi','pydantic','uvicorn','pytest','httpx')},'new_dependencies':[],'sqlite_encryption':'NONE'},indent=2),encoding='utf8')
print(json.dumps({'archive_files':len(files),'code_archive_verified':True,'demo_backup_audit_verified':True,'implementation_hash':freeze['implementation_hash']}))