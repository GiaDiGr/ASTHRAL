"""Independent computational audit protocol, not the v0.9 development benchmark.
Three unload/load sessions, fixed synthetic workload, 20 warm repetitions per mode.
No reserved LLM questions are read. Writes only the new output directory.
"""
from pathlib import Path
import sys,json,time,argparse,concurrent.futures,subprocess,statistics
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'));sys.path.insert(0,str(ROOT/'docs/v09'))
import httpx
from vigile.space_compute import release_model,telemetry,summarize
from vigile.conversational import ConversationalInference
from vigile.local_assistant import ReaderClient
from vigile.longitudinal_assistant import monitoring_blocks,answer_monitoring
from vigile.offline_library import OfflineLibrary
from vigile.store import Store,digest
from vigile.integration import deny_external_network
from benchmark_compute import pids
URL='http://127.0.0.1:8891';MODEL='vigile-qwen3-4b:latest'

def main(output,soak):
 output.mkdir(exist_ok=False,parents=True);deny_external_network();folder=ROOT/'engine/data/portal-v090-release'
 def snapshot():
  s=Store(folder/'vigile.sqlite3')
  try:assert s.verify();return digest([dict(r) for r in s.db.execute('SELECT kind,id,payload FROM records ORDER BY seq')])
  finally:s.close()
 baseline=snapshot();reader=ReaderClient('http://127.0.0.1:8895',(folder/'reader-token.txt').read_text().strip());library=OfflineLibrary(ROOT/'engine/local_ai/library-v080.json')
 run=reader.get('/monitoring/cycles/A-cycle-14');blocks=[b for b in monitoring_blocks(run) if b['category'] in ('BASELINE','TREND','LIMITATION')][:5]
 report={'protocol':'INDEPENDENT_COMPUTE_AUDIT_1','sessions':[],'clinical_validation':False,'energy':'NOT_MEASURED','network':'LOOPBACK_CLIENT_ENFORCED','input_run_id':run['id'],'input_output_hash':run['output_hash'],'conditions':'Desktop not physically isolated; request times exclude telemetry. Native model unload before each measured FULL/LOW_POWER session; OS file cache remains warm.'}
 def save(): (output/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 try:
  for session in range(3):
   entry={'session':session+1,'modes':{}};report['sessions'].append(entry)
   for mode in ['FULL','LOW_POWER','CRITICAL']:
    model=ConversationalInference(URL,MODEL,mode,'ollama');entry['modes'][mode]={'rows':[]};m=entry['modes'][mode]
    if mode!='CRITICAL':
     # Model operations are done only after the previous request has returned.
     m['pre_unload']=telemetry(pids());m['release']=release_model(URL,MODEL);m['post_unload']=telemetry(pids())
     t=time.perf_counter()
     try:cold=model.explain('Report numerical baseline comparison for cardiovascular monitoring.',blocks);m['cold']={'seconds':time.perf_counter()-t,'response':cold}
     except Exception as e:m['cold']={'seconds':time.perf_counter()-t,'error_type':type(e).__name__}
    targets=pids()
    for i in range(20):
     t=time.perf_counter();calls=model.model_http_calls
     try:
      response=answer_monitoring(reader,model,run['id'],'Report numerical baseline comparison for cardiovascular monitoring.',library=library) if mode=='CRITICAL' else model.explain('Report numerical baseline comparison for cardiovascular monitoring.',blocks)
      row={'seconds':time.perf_counter()-t,'response':response,'model_http_calls':model.model_http_calls-calls}
     except httpx.HTTPError as e:row={'seconds':time.perf_counter()-t,'failure_layer':'HTTP','error_type':type(e).__name__}
     except ValueError as e:row={'seconds':time.perf_counter()-t,'failure_layer':'INFERENCE_VALIDATION','error_type':type(e).__name__,'code':str(e)}
     except Exception as e:row={'seconds':time.perf_counter()-t,'failure_layer':'APPLICATION','error_type':type(e).__name__}
     if mode=='CRITICAL':assert row.get('model_http_calls',0)==0
     row['telemetry']=telemetry(targets);m['rows'].append(row);save()
    with httpx.Client(trust_env=False,timeout=5) as c:m['loaded']=c.get(URL+'/api/ps').json()
    m['timings']=summarize(r['seconds'] for r in m['rows']);m['records_unchanged']=snapshot()==baseline;assert m['records_unchanged'];save();print('session',session+1,mode,m['timings'].get('median'),flush=True)
   # Explicit transition back to FULL before the next session.
   restored=ConversationalInference(URL,MODEL,'FULL','ollama')
   try:entry['full_restoration']=restored.explain('Report numerical baseline comparison for cardiovascular monitoring.',blocks)
   except ValueError as e:entry['full_restoration']={'fallback':str(e)}
   save()
  # Independent document retrieval repetitions.
  report['rag']=[]
  for i in range(60):
   t=time.perf_counter();found,issues=library.search(['baseline longitudinal comparison','radiation intervals coverage','quality invalid measurement'][i%3],5);report['rag'].append({'seconds':time.perf_counter()-t,'ids':[b['id'] for b in found],'issues':issues})
  report['soak']={'planned_seconds':soak,'health':[],'assistant':[]};save();start=time.perf_counter();last=-100
  with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=75,headers={'Origin':'http://127.0.0.1:8896'}) as c:
   c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status()
   while time.perf_counter()-start<soak:
    t=time.perf_counter()
    try:r=c.get('http://127.0.0.1:8895/health');report['soak']['health'].append({'seconds':time.perf_counter()-t,'status':r.status_code})
    except httpx.HTTPError as e:report['soak']['health'].append({'layer':'HTTP','error_type':type(e).__name__})
    if time.perf_counter()-last>5:
     def ask(i):
      t=time.perf_counter()
      try:
       r=c.post('/api/assistant',json={'monitoring_id':run['id'],'question':'Explain recorded baseline values.'});return {'seconds':time.perf_counter()-t,'http_status':r.status_code,'response':r.json()}
      except httpx.HTTPError as e:return {'layer':'HTTP','error_type':type(e).__name__}
     with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:report['soak']['assistant'].append(list(ex.map(ask,range(3))))
     last=time.perf_counter();save()
    time.sleep(.5)
  report['soak']['elapsed_seconds']=time.perf_counter()-start;report['final_records_unchanged']=snapshot()==baseline;save()
 finally:reader.close()
 print('AUDIT_COMPLETE',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--soak-seconds',type=int,default=600);a=p.parse_args()
 if not 360<=a.soak_seconds<=1200:raise ValueError('BOUNDED_SOAK_LONGER_THAN_FIVE_MINUTES_REQUIRED')
 main(a.output,a.soak_seconds)
