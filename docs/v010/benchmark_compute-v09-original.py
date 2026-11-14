"""Reproducible local benchmarks; model unload is explicit and selected-model only."""
from pathlib import Path
import sys,json,time,argparse,threading,os,subprocess,concurrent.futures,zipfile,statistics
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
import httpx
from vigile.space_compute import telemetry,summarize,release_model
from vigile.conversational import ConversationalInference
from vigile.offline_library import OfflineLibrary
from vigile.integration import deny_external_network
MODEL='vigile-qwen3-4b:latest';URL='http://127.0.0.1:8891'

def pids():
 cmd="& { $tableVigile = @(Get-CimInstance Win32_Process); $idsVigile = [System.Collections.Generic.HashSet[int]]::new(); foreach ($rowVigile in $tableVigile) { if ($rowVigile.Name -match '^ollama') { [void]$idsVigile.Add([int]$rowVigile.ProcessId) } }; for ($levelVigile=0; $levelVigile -lt 5; $levelVigile++) { foreach ($rowVigile in $tableVigile) { if ($idsVigile.Contains([int]$rowVigile.ParentProcessId)) { [void]$idsVigile.Add([int]$rowVigile.ProcessId) } } }; @($idsVigile) | ConvertTo-Json }"
 r=subprocess.run(['powershell','-NoProfile','-Command',cmd],capture_output=True,text=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
 try:v=json.loads(r.stdout);return ([v] if isinstance(v,int) else v)+[os.getpid()]
 except (ValueError,TypeError):return [os.getpid()]

class Sampler:
 def __enter__(self):
  self.rows=[];self.stop=threading.Event();self.targets=pids()
  def loop():
   while not self.stop.is_set():self.rows.append(telemetry(self.targets));self.stop.wait(1)
  self.thread=threading.Thread(target=loop,daemon=True);self.thread.start();return self
 def __exit__(self,*a):self.stop.set();self.thread.join(timeout=10)

def benchmark(output,n=6,soak_seconds=120):
 output=Path(output)
 if output.exists():raise ValueError('OUTPUT_EXISTS')
 deny_external_network();report={'n_per_mode':n,'clinical_validation':False,'energy':'NOT_MEASURED','network':'LOOPBACK_ONLY_ENFORCED','telemetry_note':'Global GPU values are not attributable exclusively to VIGILE. Windows working sets per recorded PID; dynamic new runner may not be in initial PID set. CPU seconds are cumulative process time.','modes':{},'rag':{},'clinical':{}}
 def save():output.write_text(json.dumps(report,indent=2),encoding='utf8')
 lib=OfflineLibrary(ROOT/'engine/local_ai/library-v080.json');qrels=json.loads((ROOT/'docs/v09/rag-qrels.json').read_text())['queries'];rag=[]
 for i in range(48):
  t=time.perf_counter();rows,issues=lib.search(qrels[i%12]['question'],5);rag.append({'ms':1000*(time.perf_counter()-t),'ids':[b['id'] for b in rows],'issues':issues})
 report['rag']={'timing_ms':summarize(x['ms'] for x in rag),'rows':rag};save()
 from vigile.service import Engine
 from vigile.registry import Registry
 from vigile.store import Store
 from vigile.monitoring_demo import scenarios
 registry=Registry(ROOT);clinical=[]
 for i in range(5):
  store=Store(':memory:')
  try:
   engine=Engine(registry,store);t=time.perf_counter();out=scenarios(engine);clinical.append({'ms':1000*(time.perf_counter()-t),'cycles':out['cycles'],'replays_match':all(r['matches'] for r in out['replays'])})
  finally:store.close()
 report['clinical']={'scenario_batch_ms':summarize(r['ms'] for r in clinical),'rows':clinical,'note':'Each batch includes acquisition, 15 cycles, clinical rules, persistence and replay in a new in-memory SQLite store. Not per-measurement latency.'};save()
 # Source from a controlled persisted synthetic monitoring result, never clinical user data.
 from vigile.longitudinal_assistant import monitoring_blocks,answer_monitoring
 from vigile.local_assistant import ReaderClient
 folder=ROOT/'engine/data/portal-v080-final';reader=ReaderClient('http://127.0.0.1:8895',(folder/'reader-token.txt').read_text().strip());run=reader.get('/monitoring/cycles/A-cycle-14');blocks=[b for b in monitoring_blocks(run) if b['category'] in ('BASELINE','TREND','LIMITATION')][:5]
 question='Explain the recorded baseline values.'
 try:
  for mode in ('BASELINE_V08','FULL','LOW_POWER','CRITICAL'):
   if mode=='BASELINE_V08':
    with zipfile.ZipFile(ROOT/'docs/v09/before-v09.zip') as z:source=z.read('engine/vigile/conversational.py')
    namespace={'__name__':'vigile.benchmark_v08','__package__':'vigile'};exec(compile(source,'before-v09/conversational.py','exec'),namespace);cls=namespace['ConversationalInference'];model=cls(URL,MODEL,'FULL','ollama')
   else:model=ConversationalInference(URL,MODEL,mode,'ollama')
   report['modes'][mode]={'requests':[]}
   if mode!='CRITICAL':report['modes'][mode]['unload_before_cold']=release_model(URL,MODEL)
   with Sampler() as samples:
    for i in range(n):
     t=time.perf_counter()
     try:
      if mode=='CRITICAL':response=answer_monitoring(reader,model,'A-cycle-14',question,library=lib)
      else:response=model.explain(question,blocks)
      row={'seconds':time.perf_counter()-t,'cold_model_unloaded':i==0 and mode!='CRITICAL','response':response}
     except (httpx.HTTPError,ValueError,KeyError,TypeError) as e:row={'seconds':time.perf_counter()-t,'cold_model_unloaded':i==0 and mode!='CRITICAL','error_type':type(e).__name__,'error_code':str(e) if isinstance(e,ValueError) else None}
     report['modes'][mode]['requests'].append(row);save();print(mode,i,round(row['seconds'],2),row.get('response',{}).get('status',row.get('error_type')),flush=True)
   report['modes'][mode]['samples']=samples.rows
   with httpx.Client(trust_env=False,timeout=5) as c:report['modes'][mode]['ollama_ps_after']=c.get(URL+'/api/ps').json()
   report['modes'][mode]['warm_seconds']=summarize(r['seconds'] for r in report['modes'][mode]['requests'][1:]);save()
  # CRITICAL avoids model requests but does not release an already loaded model.
  report['critical_explicit_release']=release_model(URL,MODEL);report['telemetry_after_release']=telemetry(pids());save()
  # Two real simultaneous generation requests to measure runtime queuing, no daemon configuration change.
  with httpx.Client(trust_env=False,timeout=90) as c:
   def raw_request(i):
    t=time.perf_counter();r=c.post(URL+'/api/generate',json={'model':MODEL,'prompt':'Reply exactly OK.','stream':False,'options':{'num_ctx':2048,'num_predict':8,'num_thread':4},'keep_alive':'30s'});r.raise_for_status();return {'seconds':time.perf_counter()-t,'response':r.json()}
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:report['raw_concurrent_2']=list(ex.map(raw_request,range(2)))
  # Bounded CPU-only placement probe; no additional model or persistent runtime options.
  report['cpu_only_unload_before']=release_model(URL,MODEL)
  with Sampler() as samples:
   t=time.perf_counter()
   with httpx.Client(trust_env=False,timeout=90) as c:
    r=c.post(URL+'/api/generate',json={'model':MODEL,'prompt':'Reply exactly OK.','stream':False,'options':{'num_ctx':2048,'num_predict':8,'num_thread':4,'num_gpu':0},'keep_alive':'30s'});r.raise_for_status();cpu=r.json();loaded=c.get(URL+'/api/ps').json()
   report['cpu_only_probe']={'seconds':time.perf_counter()-t,'response':cpu,'loaded':loaded}
  report['cpu_only_probe']['samples']=samples.rows;save()
  release_model(URL,MODEL)
  # Re-load normal FULL placement for the next operator without altering server configuration.
  with httpx.Client(trust_env=False,timeout=90) as c:
   r=c.post(URL+'/api/generate',json={'model':MODEL,'prompt':'Reply exactly OK.','stream':False,'options':{'num_ctx':6144,'num_predict':8,'num_thread':8},'keep_alive':'5m'});r.raise_for_status();report['restored_full']=c.get(URL+'/api/ps').json()
  health=[];start=time.perf_counter()
  with httpx.Client(trust_env=False,timeout=5) as c:
   while time.perf_counter()-start<soak_seconds:
    t=time.perf_counter()
    try:r=c.get('http://127.0.0.1:8895/health');health.append({'seconds':time.perf_counter()-t,'status':r.status_code})
    except httpx.HTTPError as e:health.append({'seconds':time.perf_counter()-t,'error_type':type(e).__name__})
    time.sleep(1)
  report['stability']={'duration_seconds':time.perf_counter()-start,'requests':health,'note':'Short desktop soak, not mission-duration stability'};save()
 finally:reader.close()
 print(json.dumps({'completed':True,'modes':list(report['modes']),'rag_median_ms':report['rag']['timing_ms'].get('median')}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--samples',type=int,default=6);p.add_argument('--soak-seconds',type=int,default=120);a=p.parse_args()
 if not 5<=a.samples<=30 or not 0<=a.soak_seconds<=600:raise ValueError('BOUNDED_WORKLOAD_REQUIRED')
 benchmark(a.output,a.samples,a.soak_seconds)
