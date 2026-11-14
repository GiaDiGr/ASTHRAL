"""Read-only release verification. No reserved questions, no real patient data."""
from pathlib import Path
import sys,json,hashlib,httpx
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.store import Store,canonical
from vigile.local_protection import read_secret,verify_anchor
folder=ROOT/'engine/data/portal-v0100-integrated';old=ROOT/'engine/data/portal-v090-release';report={'clinical_validation':False,'replays':[]}
with httpx.Client(base_url='http://127.0.0.1:8895',headers={'Authorization':'Bearer '+read_secret(folder/'reader-token.txt')},trust_env=False,timeout=30) as client:
 report['health']=client.get('/health').json()
 for subject in client.get('/dashboard/subjects').json():
  data=client.get('/dashboard/subjects/'+subject['id'],params={'mission_id':subject['mission_id']});data.raise_for_status()
  for key,prefix in [('evaluations','/clinical/evaluations/'),('monitoring','/monitoring/cycles/')]:
   for e in data.json()[key]:
    response=client.get(prefix+e['id']+'/replay');response.raise_for_status();report['replays'].append({'id':e['id'],'matches':response.json()['matches']})
 report['reader_write_status']=client.post('/measurements',json={}).status_code
 report['cross_scope_status']=client.get('/dashboard/subjects/other?mission_id=other').status_code
 report['openapi_status']=client.get('/openapi.json').status_code
 (ROOT/'docs/v010/backend-openapi.json').write_text(json.dumps(client.get('/openapi.json').json(),indent=2),encoding='utf8')
a=Store(old/'vigile.sqlite3');b=Store(folder/'vigile.sqlite3')
try:
 report['implementation_hashes']=sorted({e['implementation_hash'] for e in b.all('clinical_evaluation')})
 report['knowledge_hashes']=sorted({e['knowledge_hash'] for e in b.all('clinical_evaluation')})
 report['clinical_vectors']=[]
 for x,y in zip(a.all('clinical_evaluation'),b.all('clinical_evaluation')):
  keys=['results','urgency','next_tests','differential','presentation_protocol','treatment_status','knowledge_hash'];report['clinical_vectors'].append({'old_id':x['id'],'new_id':y['id'],'equal':all(canonical(x[k])==canonical(y[k]) for k in keys)})
 report['clinical_counts']=[len(a.all('clinical_evaluation')),len(b.all('clinical_evaluation'))]
 report['monitoring_vectors']=[{'id':y['id'],'equal':{k:canonical(x.get(k))==canonical(y.get(k)) for k in ['domains','events','relations']}} for x,y in zip(a.all('monitoring_run'),b.all('monitoring_run'))]
 def domain_values(run):
  return [{**domain,'indicators':[{k:v for k,v in indicator.items() if k!='normative_finding_id'} for indicator in domain['indicators']]} for domain in run['domains']]
 report['monitoring_descriptive_values_equal']=all(canonical(domain_values(x))==canonical(domain_values(y)) for x,y in zip(a.all('monitoring_run'),b.all('monitoring_run')))
 assert report['monitoring_descriptive_values_equal']
 report['audit_valid']=b.verify();report['checkpoint']=b.checkpoint()
finally:a.close();b.close()
external=Path.home()/'AppData/Local/Vigile/integrity';report['external_anchor']=verify_anchor(folder/'vigile.sqlite3',external/'v0100-integrated.anchor.json',external/'audit-key.dpapi')
pin=json.loads((ROOT/'docs/v010/reserved-bank-pin.json').read_text());report['reserved_bank_unchanged']=hashlib.sha256((ROOT/pin['path']).read_bytes()).hexdigest()==pin['sha256']
assert report['reader_write_status']==403 and report['cross_scope_status']==403
assert report['audit_valid'] and report['external_anchor']['valid'] and report['reserved_bank_unchanged']
assert all(x['matches'] for x in report['replays']) and all(x['equal'] for x in report['clinical_vectors'])
(ROOT/'docs/v010/release-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'replays':len(report['replays']),'clinical_vectors_equal':len(report['clinical_vectors']),'audit_valid':report['audit_valid'],'reserved_bank_unchanged':report['reserved_bank_unchanged'],'health':report['health']},indent=2))
