"""Bounded burst-load desktop soak; synthetic read-only queries."""
from pathlib import Path
import sys,time,json,argparse,httpx
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.integration import deny_external_network
from vigile.space_compute import summarize,telemetry
from vigile.store import Store,digest
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=int,default=300);a=p.parse_args()
if a.output.exists() or not 30<=a.seconds<=600:raise ValueError('NEW_OUTPUT_AND_BOUNDED_DURATION_REQUIRED')
deny_external_network();folder=ROOT/'engine/data/portal-v090-release'
def snapshot():
 s=Store(folder/'vigile.sqlite3')
 try:assert s.verify();return digest([dict(r) for r in s.db.execute('SELECT kind,id,payload FROM records ORDER BY seq')])
 finally:s.close()
before=snapshot();start=time.perf_counter();rows=[];models=[];last=-100;report={'planned_seconds':a.seconds,'clinical_validation':False,'load':'one health request per second, one assistant burst every 20 seconds, read-only synthetic A-cycle-14','health':rows,'assistant':models}
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=75,headers={'Origin':'http://127.0.0.1:8896'}) as c:
 c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status();c.post('/api/mode',json={'mode':'FULL'}).raise_for_status()
 while time.perf_counter()-start<a.seconds:
  t=time.perf_counter()
  try:r=c.get('http://127.0.0.1:8895/health');rows.append({'elapsed':t-start,'seconds':time.perf_counter()-t,'status':r.status_code})
  except httpx.HTTPError as e:rows.append({'elapsed':t-start,'seconds':time.perf_counter()-t,'error_type':type(e).__name__})
  if time.perf_counter()-last>=20:
   t=time.perf_counter()
   try:r=c.post('/api/assistant',json={'monitoring_id':'A-cycle-14','question':'Explain recorded baseline values.'});models.append({'elapsed':t-start,'seconds':time.perf_counter()-t,'http_status':r.status_code,'response':r.json(),'telemetry':telemetry()})
   except httpx.HTTPError as e:models.append({'elapsed':t-start,'seconds':time.perf_counter()-t,'error_type':type(e).__name__})
   last=time.perf_counter()
  a.output.write_text(json.dumps(report,indent=2),encoding='utf8');time.sleep(1)
report['duration_seconds']=time.perf_counter()-start;report['health_seconds']=summarize(r['seconds'] for r in rows);report['clinical_records_unchanged']=snapshot()==before
assert report['clinical_records_unchanged'];a.output.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'duration':report['duration_seconds'],'health_n':len(rows),'assistant_n':len(models),'health_ok':sum(r.get('status')==200 for r in rows),'assistant_http_ok':sum(r.get('http_status')==200 for r in models)}))
