from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[2]
version=sys.argv[1];sys.path.insert(0,str(ROOT/('work/v100/v011-runtime/engine' if version=='before' else 'engine')))
from vigile.offline_library import OfflineLibrary
library=OfflineLibrary(ROOT/'engine/local_ai/library-v080.json');qrels=json.loads((ROOT/'docs/v09/rag-qrels.json').read_text());rows=[]
for q in qrels['queries']:
 t=time.perf_counter();found,issues=library.search(q['question'],5);ids=[b['id'] for b in found];gold=set(q['relevant_fragment_ids'])
 rows.append({'id':q['id'],'question':q['question'],'gold':sorted(gold),'retrieved_ids':ids,'top3':bool(set(ids[:3])&gold),'top5':bool(set(ids[:5])&gold),'seconds':time.perf_counter()-t,'issues':issues})
report={'development_only':True,'reserved_bank_read':False,'version':version,'rows':rows,'top3_hits':sum(r['top3'] for r in rows),'top5_hits':sum(r['top5'] for r in rows),'unchanged_qrels_and_fragment_ids':True}
(ROOT/('docs/v100/rag-'+version+'.json')).write_text(json.dumps(report,indent=2),encoding='utf8');print(version,report['top3_hits'],report['top5_hits'])