from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[2];version=sys.argv[1];suffix=sys.argv[2] if len(sys.argv)>2 else '';runtime=ROOT/('work/v100/v011-runtime/engine' if version=='before' else 'engine');sys.path.insert(0,str(runtime))
from fastapi.testclient import TestClient
from vigile.api import create_app
from vigile.local_assistant import ReaderClient
from vigile.local_protection import read_secret
from vigile.conversational import ConversationalInference
from vigile.longitudinal_assistant import answer_monitoring
from vigile.offline_library import OfflineLibrary
from vigile.integration import deny_external_network
folder=ROOT/'engine/data'/('backups/v011-before-v100' if version=='before' else 'v100-development')
credentials=ROOT/'engine/data'/('mission-v011-final' if version=='before' else 'v100-development')
reader_token=read_secret(credentials/'reader-token.txt');mapping=json.loads(read_secret(credentials/'server-tokens.json'))
questions=[('baseline','mission-crew-A-cycle-35','What is changing compared with my baseline?','en'),('condition','mission-crew-A-cycle-35','VIGILE, how has my physical condition changed during the mission?','en'),('alert','mission-crew-B-cycle-18','VIGILE, why am I receiving this medical alert?','en'),('missing','mission-crew-B-cycle-18','What information is missing from my evaluation?','en'),('change','mission-crew-B-cycle-18p1','¿Qué cambió desde mi última evaluación?','es')]
report={'version':version,'reserved_bank_read':False,'rows':[]};model=ConversationalInference('http://127.0.0.1:8891','vigile-qwen3-4b:latest',provider='ollama');model.structured_explanations=version=='after';calls=[];original=model._complete

def tracked(*args):
 try:
  value=original(*args);calls.append({'raw_model_output':value[0],'metrics':value[1]});return value
 except Exception as exc:calls.append({'error_type':type(exc).__name__});raise
model._complete=tracked
class Bridge(ReaderClient):
 def __init__(self,client):
  class Transport:
   def call(self,method,path):
    assert method=='GET';r=client.get(path,headers={'Authorization':'Bearer '+reader_token});r.raise_for_status();return r.json()
   def close(self):pass
  self.client=Transport()
deny_external_network()
with TestClient(create_app(ROOT,folder/'vigile.sqlite3',mapping)) as client:
 bridge=Bridge(client);library=OfflineLibrary(ROOT/'engine/local_ai/library-v080.json')
 for kind,target,question,language in questions:
  calls.clear();t=time.perf_counter();out=answer_monitoring(bridge,model,target,question,library=library,**({'language':language} if version=='after' else {}));row={'kind':kind,'target':target,'question':question,'seconds':time.perf_counter()-t,'response':out,'raw_model_calls':list(calls)};report['rows'].append(row)
  (ROOT/('docs/v100/llm-'+version+suffix+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8');print(version,kind,out['status'],len(out.get('generated',[])),flush=True)