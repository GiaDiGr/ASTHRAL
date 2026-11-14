from pathlib import Path
import json,sys,httpx,hashlib,xml.etree.ElementTree as ET
root=Path(r'C:\Users\Gianni\Desktop\Vigile');sys.path.insert(0,str(root/'engine'))
from vigile.store import Store,digest
from vigile.integration import deny_external_network
deny_external_network()
folder=root/'engine/data/portal-v080-final'
old=json.loads((root/'engine/data/portal-v070/monitoring-report.json').read_text())
new=json.loads((folder/'monitoring-report.json').read_text())
def vector(rows):
 return {r['id']:{k:{condition:{f:result.get(f) for f in ('diagnostic_status','urgency','confirmation_status','protocol_status','treatment_status')} for condition,result in e['results'].items()} for k,e in r['clinical_evaluations'].items()} for r in rows}
assert vector(old['outputs'])==vector(new['outputs'])
originals=json.loads((root/'MANIFIESTO_SHA256.json').read_text(encoding='utf-8-sig'))
assert all(hashlib.sha256((root/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in originals)
manifest=json.loads((root/'engine/vigile/clinical_knowledge/manifest.json').read_text())
assert all(hashlib.sha256((root/'engine/vigile/clinical_knowledge'/n).read_bytes()).hexdigest()==h for n,h in manifest['files'].items())
summary={'old_new_clinical_vectors_equal':True,'clinical_fields':['diagnostic_status','urgency','confirmation_status','protocol_status','treatment_status'],'original_scientific_files':len(originals),'original_clinical_files':len(manifest['files']),'implementation_hash':new['implementation_hash'],'network':'LOOPBACK_ONLY_ENFORCED','clinical_validation':False}
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=30,headers={'Origin':'http://127.0.0.1:8896','Connection':'close'}) as c:
 c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status()
 modes={}
 try:
  for mode in ('FULL','LOW_POWER','CRITICAL'):
   c.post('/api/mode',json={'mode':mode}).raise_for_status()
   r=c.post('/api/assistant',json={'monitoring_id':'C-cycle-28','question':'What data are missing or invalid?'});r.raise_for_status();out=r.json()
   assert out['status']=='DETERMINISTIC_DATA_SUFFICIENCY' and not out['inference_attempted'] and out['mode']==mode
   modes[mode]={'status':out['status'],'inference_attempted':out['inference_attempted']}
  r=c.post('/api/assistant',json={'monitoring_id':'C-cycle-28','question':'Explain radiation dose coverage limitations.'});r.raise_for_status();out=r.json()
  assert out['status']=='EXTRACTIVE_ONLY' and not out['inference_attempted']
  assert any(b['category']=='RADIATION' for b in out['answer'])
  (root/'docs/v08/monitoring-response-example.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
 finally:c.post('/api/mode',json={'mode':'FULL'}).raise_for_status()
 summary['portal_modes']=modes
s=Store(folder/'vigile.sqlite3')
try:assert s.verify();summary['audit_valid']=True
finally:s.close()
(root/'docs/v08/integrity-and-modes-release.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
print(json.dumps(summary,indent=2))

