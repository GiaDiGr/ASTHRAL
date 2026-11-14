from pathlib import Path
import sys,json,subprocess,time,httpx
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/v09/runtime-failure-recovery.json');args=parser.parse_args()
if args.output.exists():raise ValueError('OUTPUT_EXISTS_PRESERVE_REFERENCE_RESULTS')

from vigile.space_compute import release_model
folder=ROOT/'engine/data/portal-v090-release';record=json.loads((ROOT/'engine/local_ai/ollama-process.json').read_text());expected=ROOT/'engine/local_ai/ollama-v0.40.6/ollama.exe'
assert Path(record['exe'])==expected and record['host']=='127.0.0.1:8891'
report={'clinical_validation':False,'selected_runtime_pid':record['pid'],'explicit_unload':release_model('http://127.0.0.1:8891','vigile-qwen3-4b:latest')}
script="$runtimeVigile = Get-Process -Id "+str(int(record['pid']))+" -ErrorAction Stop; if ($runtimeVigile.Path -ne '"+str(expected)+"') { throw 'PROCESS_IDENTITY_MISMATCH' }; Stop-Process -Id $runtimeVigile.Id"
subprocess.run(['powershell','-NoProfile','-Command',script],check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 with httpx.Client(trust_env=False,timeout=2) as c:
  try:c.get('http://127.0.0.1:8891/api/version').raise_for_status();raise AssertionError('RUNTIME_STILL_AVAILABLE')
  except httpx.HTTPError:report['runtime_physically_unavailable']=True
 with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=30,headers={'Origin':'http://127.0.0.1:8896'}) as c:
  c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status()
  for mode in ('FULL','CRITICAL'):
   c.post('/api/mode',json={'mode':mode}).raise_for_status();r=c.post('/api/assistant',json={'monitoring_id':'A-cycle-14','question':'Explain recorded baseline values.'});r.raise_for_status();out=r.json();assert not out['inference_attempted'] and out['answer'];report['down_'+mode]=out
  report['backend_health_while_runtime_down']=c.get('http://127.0.0.1:8895/health').json()
finally:
 t=time.perf_counter();r=subprocess.run([str(ROOT/'engine/.venv/Scripts/python.exe'),str(ROOT/'engine/tools/start_ollama_vigile.py')],cwd=ROOT/'engine',check=True,capture_output=True,text=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW);report['runtime_restart_seconds_n1']=time.perf_counter()-t;report['restarted']=json.loads(r.stdout)
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=90,headers={'Origin':'http://127.0.0.1:8896'}) as c:
 c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status();c.post('/api/mode',json={'mode':'FULL'}).raise_for_status()
 r=c.post('/api/assistant',json={'monitoring_id':'A-cycle-14','question':'Explain recorded baseline values.'});r.raise_for_status();report['recovered_response']=r.json();report['status']=c.get('/api/status').json();assert report['status']['assistant']['available']
args.output.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'runtime_loss_tested':True,'backend_available':report['backend_health_while_runtime_down']['status'],'restart_seconds_n1':report['runtime_restart_seconds_n1'],'recovery_status':report['recovered_response']['status']}))
