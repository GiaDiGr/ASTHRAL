from pathlib import Path
import sys,json,time,httpx
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/v09/endtoend-benchmark.json');args=parser.parse_args()
if args.output.exists():raise ValueError('OUTPUT_EXISTS_PRESERVE_REFERENCE_RESULTS')

from vigile.space_compute import summarize
from vigile.integration import deny_external_network
from vigile.store import Store,digest
deny_external_network();folder=ROOT/'engine/data/portal-v090-release'
def snapshot():
 s=Store(folder/'vigile.sqlite3')
 try:assert s.verify();return digest([dict(r) for r in s.db.execute('SELECT kind,id,payload FROM records ORDER BY seq')])
 finally:s.close()
before=snapshot();report={'clinical_validation':False,'modes':{},'energy':'NOT_MEASURED','network':'LOOPBACK_ONLY_ENFORCED'}
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=90,headers={'Origin':'http://127.0.0.1:8896'}) as c:
 c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status()
 try:
  for mode in ['FULL','LOW_POWER','CRITICAL']:
   c.post('/api/mode',json={'mode':mode}).raise_for_status();rows=[]
   for i in range(6):
    t=time.perf_counter();response=c.post('/api/assistant',json={'monitoring_id':'A-cycle-14','question':'Explain recorded baseline values.'});elapsed=time.perf_counter()-t;response.raise_for_status();rows.append({'seconds':elapsed,'response':response.json()})
   report['modes'][mode]={'rows':rows,'warm_seconds':summarize(r['seconds'] for r in rows[1:])};print(mode,report['modes'][mode]['warm_seconds'],flush=True)
 finally:c.post('/api/mode',json={'mode':'FULL'}).raise_for_status()
 # Restore actual FULL context allocation as well as the mode label.
 r=c.post('/api/assistant',json={'monitoring_id':'A-cycle-14','question':'Explain recorded baseline values.'});r.raise_for_status();report['restored_full']=r.json()
assert snapshot()==before;report['clinical_records_unchanged']=True
args.output.write_text(json.dumps(report,indent=2),encoding='utf8')
