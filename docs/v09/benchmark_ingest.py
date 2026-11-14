"""Synthetic ingestion benchmark; does not touch demonstration databases."""
from pathlib import Path
import sys,json,time,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.store import Store
from vigile.registry import Registry
from vigile.service import Engine
from vigile.monitoring_demo import scenarios
from vigile.space_compute import summarize
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise ValueError('OUTPUT_EXISTS')
s=Store(':memory:');e=Engine(Registry(ROOT),s);original=e.ingest;rows=[]
def measured(m,actor):
 t=time.perf_counter();result=original(m,actor);rows.append({'id':m.id,'ms':1000*(time.perf_counter()-t)});return result
e.ingest=measured
try:scenarios(e)
finally:s.close()
a.output.write_text(json.dumps({'timing_ms':summarize(r['ms'] for r in rows),'rows':rows,'note':'Synthetic in-memory SQLite ingestion includes scope, device quality assessment, storage and audit; excludes external hardware sampling.'},indent=2),encoding='utf8')
