from pathlib import Path
import json,sys,time
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.offline_library import OfflineLibrary
qrels=json.loads((R/'docs/v09/rag-qrels.json').read_text())['queries']
questions=[(0,'Where does the engine document personal baseline eligibility and selection?'),(0,'¿Dónde se documenta la selección y validez de una referencia personal basal?'),(2,'How does the event mechanism suppress duplicate notifications?'),(2,'¿Se notifica otra vez un evento idéntico sin cambios?'),(6,'What numeric capillary glucose boundaries define level 1 and level 2 hypoglycemia?'),(6,'¿Cuáles son los límites de glucosa capilar para los niveles de hipoglucemia?'),(8,'Explain stale sensor values and the declared clinical time window.'),(10,'Does the muscle and bone module assume a DXA device is present?')]
queries=[{'id':'additional-'+str(i+1),'question':q,'relevant_fragment_ids':qrels[g]['relevant_fragment_ids'],'annotation':'Developer-authored literal passage relevance assigned before retrieval; not independent clinical adjudication'} for i,(g,q) in enumerate(questions)]
path=R/'docs/v100/rag-additional-qrels.json'
if path.exists():raise ValueError('EXISTING_QRELS')
path.write_text(json.dumps({'development_only':True,'reserved':False,'queries':queries},ensure_ascii=False,indent=2),encoding='utf8')
library=OfflineLibrary(R/'engine/local_ai/library-v080.json');rows=[]
for q in queries:
 found,issues=library.search(q['question'],5);ids=[b['id'] for b in found];gold=set(q['relevant_fragment_ids']);rows.append({**q,'retrieved_ids':ids,'top3':bool(set(ids[:3])&gold),'top5':bool(set(ids)&gold),'issues':issues})
report={'rows':rows,'top3_hits':sum(r['top3'] for r in rows),'top5_hits':sum(r['top5'] for r in rows),'total':len(rows),'used_for_further_tuning':False}
(R/'docs/v100/rag-additional-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(report['top3_hits'],report['top5_hits'],report['total'])