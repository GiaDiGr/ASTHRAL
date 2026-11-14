from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.conversational import ConversationalInference
from vigile.documentary import explain_documents
from vigile.offline_library import OfflineLibrary
m=ConversationalInference('http://127.0.0.1:8891','vigile-qwen3-4b:latest','FULL','ollama');library=OfflineLibrary(ROOT/'engine/local_ai/library-v080.json');rows=[];original=m._complete;traces=[]
def traced(*a):
 value=original(*a);traces.append(value);return value
m._complete=traced
for q in ['Quote the hypoglycemia Level 1 glucose classification.','Cita literalmente el limite de la suma de radiacion por intervalos.']:
 traces.clear();result=explain_documents(m,library,q);rows.append({'question':q,'response':result,'raw_calls':list(traces)})
(ROOT/'docs/v09/documentary-probes.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf8');print([(x['response']['status'],len(x['response']['quotations'])) for x in rows])
