from pathlib import Path
import sys,json,time,threading
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'docs/v09')]
from benchmark_compute import pids
from vigile.space_compute import telemetry,release_model
from vigile.conversational import ConversationalInference
from vigile.integration import deny_external_network
URL='http://127.0.0.1:8891';MODEL='vigile-qwen3-4b:latest'
a=json.loads((ROOT/'docs/v010/compute-audit/audit.json').read_text())
blocks=a['sessions'][0]['modes']['CRITICAL']['rows'][0]['response']['retrieved']
blocks=[b for b in blocks if b.get('category') in ('BASELINE','TREND','LIMITATION')][:5]
if not blocks:raise ValueError('NO_FIXED_BLOCKS')
deny_external_network();report={'protocol':'CORRECTED_PID_CREATION_ORDER_RESOURCE_SAMPLE','note':'Original process attribution invalid due reused conhost PID; global GPU and timing remain global/valid respectively. Corrected samples include explicit collector PID. No energy measurements.','sessions':[]}
path=ROOT/'docs/v010/compute-audit/corrected-resources.json'
for session in range(3):
 row={'session':session+1,'modes':{}};report['sessions'].append(row)
 for mode in ('FULL','LOW_POWER'):
  out={};row['modes'][mode]=out;out['pre_unload']=telemetry(pids());out['release']=release_model(URL,MODEL);out['post_unload']=telemetry(pids())
  model=ConversationalInference(URL,MODEL,mode,'ollama');start=time.perf_counter()
  try:out['cold_response']=model.explain('Report numerical baseline comparison for cardiovascular monitoring.',blocks)
  except ValueError as e:out['cold_response']={'fallback':str(e)}
  out['cold_seconds']=time.perf_counter()-start;targets=pids();out['pids']=targets;out['samples']=[];out['responses']=[];stop=threading.Event()
  def sample():
   while not stop.is_set():out['samples'].append(telemetry(targets));stop.wait(.5)
  thread=threading.Thread(target=sample);thread.start()
  try:
   for i in range(5):
    start=time.perf_counter()
    try:value=model.explain('Report numerical baseline comparison for cardiovascular monitoring.',blocks)
    except ValueError as e:value={'fallback':str(e)}
    out['responses'].append({'seconds':time.perf_counter()-start,'response':value})
  finally:stop.set();thread.join()
  path.write_text(json.dumps(report,indent=2),encoding='utf8');print(session+1,mode,len(targets),flush=True)
print('CORRECTED_RESOURCES_COMPLETE',flush=True)
