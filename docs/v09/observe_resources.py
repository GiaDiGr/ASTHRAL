from pathlib import Path
import sys,time,json,os,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'));sys.path.insert(0,str(ROOT/'docs/v09'))
import httpx
from benchmark_compute import pids
from vigile.space_compute import telemetry
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=int,default=30);a=p.parse_args()
if a.output.exists():raise ValueError('OUTPUT_EXISTS')
start=time.perf_counter();rows=[]
with httpx.Client(trust_env=False,timeout=3) as c:
 while time.perf_counter()-start<a.seconds:
  sample=telemetry(pids());sample['ollama_ps']=c.get('http://127.0.0.1:8891/api/ps').json();rows.append(sample);time.sleep(1)
cpu=[]
for before,after in zip(rows,rows[1:]):
 old={r['pid']:r for r in before['processes']};delta=sum(max(0,r['cpu_seconds']-old[r['pid']]['cpu_seconds']) for r in after['processes'] if r['pid'] in old and 'cpu_seconds' in r and 'cpu_seconds' in old[r['pid']]);dt=after['monotonic']-before['monotonic'];cpu.append({'seconds':dt,'cpu_seconds':delta,'total_machine_cpu_percent':100*delta/dt/(os.cpu_count() or 1)})
report={'duration_seconds':time.perf_counter()-start,'logical_cpus':os.cpu_count(),'note':'Read-only observer during audit; GPU memory/utilization global; process metrics for current Ollama executable PIDs and observer. Observer contributes overhead. No energy measured.','rows':rows,'cpu_deltas':cpu,'clinical_validation':False}
a.output.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'samples':len(rows),'duration':report['duration_seconds']}))
