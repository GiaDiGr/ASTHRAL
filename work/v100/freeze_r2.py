from pathlib import Path
import sys,json,hashlib,zipfile,datetime
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.store import digest
old=json.loads((R/'docs/v100/CANDIDATE_R1_FREEZE.json').read_text());files={}
for rel in old['files']:
 if rel=='engine/data/mission-v100-final/portal-config.json':rel='engine/data/mission-v100-r2/portal-config.json'
 files[rel]=hashlib.sha256((R/rel).read_bytes()).hexdigest()
report={**old,'version':'1.0.0-research-r2','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'implementation_hash':digest({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (R/'engine/vigile').glob('*.py')}),'files':files,'reserved_bank_content_read':True,'reserved_status':'USED_ON_R1_NOT_RERUN_ON_R2','post_bank_changes':'Explicit generic cross-context/risk refusals; deterministic clinical-interpretation routing; regression tests. No clinical criteria change.'}
with (R/'docs/v100/candidate-code-r2.zip').open('xb') as stream:
 with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
  for rel in files:
   if '/data/' not in rel:z.write(R/rel,rel)
report['code_archive_sha256']=hashlib.sha256((R/'docs/v100/candidate-code-r2.zip').read_bytes()).hexdigest()
for name in ('CANDIDATE_R2_FREEZE.json','CANDIDATE_FREEZE.json'):(R/'docs/v100'/name).write_text(json.dumps(report,indent=2),encoding='utf8')
print(report['implementation_hash'])