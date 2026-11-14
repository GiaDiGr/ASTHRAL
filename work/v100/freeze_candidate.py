from pathlib import Path
import json,sys,hashlib,zipfile,datetime
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.store import digest
files=[]
for folder in ('engine/vigile','engine/tests','engine/tools'):
 files.extend(p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.ps1','.js','.cjs','.css','.html','.json') and '__pycache__' not in p.parts)
files.extend(R/p for p in ['engine/pyproject.toml','engine/requirements.lock.txt','engine/requirements-v100.lock.txt','engine/local_ai/library-v080.json','engine/data/mission-v100-final/portal-config.json'])
files=[p for p in files if p.exists()];hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
impl=digest({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (R/'engine/vigile').glob('*.py')})
report={'version':'1.0.0-research-candidate','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'implementation_hash':impl,'knowledge_hash':'b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e','reserved_bank_content_read':False,'reserved_bank_sha256':hashlib.sha256((R/'docs/v09/reserved-bank.json').read_bytes()).hexdigest(),'files':hashes,'no_model_weights_or_credentials_in_code_archive':True}
assert report['reserved_bank_sha256']=='c1a75f8f0a792ebd094bda50bd5790b302a6c2c8475cdce0a0a5d239f76651e0'
with (R/'docs/v100/candidate-code.zip').open('xb') as out:
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:
   if 'data' not in p.relative_to(R).parts:z.write(p,p.relative_to(R))
report['code_archive_sha256']=hashlib.sha256((R/'docs/v100/candidate-code.zip').read_bytes()).hexdigest()
with (R/'docs/v100/CANDIDATE_FREEZE.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(impl,len(hashes),'frozen files; reserved content unread')