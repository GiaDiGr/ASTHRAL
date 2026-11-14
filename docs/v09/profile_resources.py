from pathlib import Path
import sys,time,json,os
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/v09/resources-profiles.json');args=parser.parse_args()
if args.output.exists():raise ValueError('OUTPUT_EXISTS_PRESERVE_REFERENCE_RESULTS')
sys.path.insert(0,str(ROOT/'docs/v09'))
from benchmark_compute import Sampler,pids
from vigile.conversational import ConversationalInference
from vigile.local_assistant import ReaderClient
from vigile.longitudinal_assistant import monitoring_blocks
import httpx
folder=ROOT/'engine/data/portal-v090-release';reader=ReaderClient('http://127.0.0.1:8895',(folder/'reader-token.txt').read_text().strip());run=reader.get('/monitoring/cycles/A-cycle-14');reader.close();blocks=[b for b in monitoring_blocks(run) if b['category'] in ('BASELINE','TREND','LIMITATION')][:5];out={}
for mode in ['FULL','LOW_POWER']:
 model=ConversationalInference('http://127.0.0.1:8891','vigile-qwen3-4b:latest',mode,'ollama');warm=model.explain('Explain recorded baseline values.',blocks);requests=[]
 with Sampler() as sampler:
  for i in range(6):
   t=time.perf_counter()
   try:response=model.explain('Explain recorded baseline values.',blocks);requests.append({'seconds':time.perf_counter()-t,'response':response})
   except Exception as e:requests.append({'seconds':time.perf_counter()-t,'error_type':type(e).__name__})
 with httpx.Client(trust_env=False,timeout=3) as c:loaded=c.get('http://127.0.0.1:8891/api/ps').json()
 out[mode]={'warmup':warm,'rows':sampler.rows,'requests':requests,'loaded':loaded,'target_pids':sampler.targets}
 print(mode,'pids',sampler.targets,'samples',len(sampler.rows),flush=True)
args.output.write_text(json.dumps({'profiles':out,'note':'Warm stable runner process, PIDs include Ollama descendants and observer. Working sets are per-process, not additive unique RAM. Global GPU utilization includes other applications.','energy':'NOT_MEASURED'},indent=2),encoding='utf8')
