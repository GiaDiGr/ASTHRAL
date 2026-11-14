from pathlib import Path
import sys,json,time,sqlite3,statistics,gc
ROOT=Path(__file__).resolve().parents[2];version=sys.argv[1];sys.path.insert(0,str(ROOT/('work/v100/v011-runtime/engine' if version=='before' else 'engine')))
from vigile.store import Store,digest
from vigile.registry import Registry
from vigile.service import Engine
from vigile.monitoring import MonitoringService
from vigile.monitoring_models import MonitoringRequest
source=sqlite3.connect((ROOT/'engine/data/backups/v011-before-v100/vigile.sqlite3').as_uri()+'?mode=ro',uri=True);source.row_factory=sqlite3.Row
report={'version':version,'paired_same_original_receipt_prefixes':True,'storage':'IN_MEMORY_SQLITE_TIMED_COMPUTE_ONLY','clinical_validation':False,'rows':[]}
for day in ('0','14','21','47'):
 rid='mission-crew-A-cycle-'+day;record=json.loads(source.execute("SELECT payload FROM records WHERE kind='monitoring_run' AND id=?",(rid,)).fetchone()[0]);req=MonitoringRequest.model_validate(record['request']);first=req.measurements[0].id
 boundary=source.execute("SELECT seq FROM records WHERE kind='measurement' AND id=?",(first,)).fetchone()[0]
 prefix=source.execute('SELECT kind,id,payload FROM records WHERE seq<? ORDER BY seq',(boundary,)).fetchall();records=[(r['kind'],r['id'],json.loads(r['payload'])) for r in prefix]
 elapsed=[];checks=[]
 for _ in range(3):
  store=Store(':memory:');store.put_many(records,'benchmark');engine=Engine(Registry(ROOT),store)
  t=time.perf_counter();out=MonitoringService(engine).run(req,'benchmark');elapsed.append(time.perf_counter()-t)
  def domains(r):return [{**d,'indicators':[{k:v for k,v in i.items() if k!='normative_finding_id'} for i in d['indicators']]} for d in r['domains']]
  checks.append(domains(out)==domains(record) and {k:v['results'] for k,v in out['clinical_evaluations'].items()}=={k:v['results'] for k,v in record['clinical_evaluations'].items()} and out['events']==record['events']);store.close();gc.collect()
 row={'day':day,'prefix_records':len(records),'prefix_json_bytes':sum(len(r['payload'].encode()) for r in prefix),'seconds':elapsed,'median_seconds':statistics.median(elapsed),'all_clinical_descriptive_events_unchanged':all(checks)};report['rows'].append(row);print(version,day,round(row['median_seconds'],4),all(checks),flush=True)
 assert all(checks)
source.close();(ROOT/('docs/v100/mission-performance-'+version+'.json')).write_text(json.dumps(report,indent=2),encoding='utf8')