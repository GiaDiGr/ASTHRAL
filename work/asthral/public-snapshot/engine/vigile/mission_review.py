"""Read-only mission verification and bounded assistant questions (no reserved bank).
--real-inference uses the configured existing loopback Ollama, without reconfiguration.
Otherwise zero network/inference requests are made.
"""
from pathlib import Path
import argparse,json,time
from fastapi.testclient import TestClient
from .api import create_app
from .local_assistant import ReaderClient
from .local_protection import read_secret
from .conversational import ConversationalInference
from .longitudinal_assistant import answer_monitoring
from .offline_library import OfflineLibrary
from .mission_demo import SUBJECTS,MID
from .store import digest

QUESTIONS=[('baseline',SUBJECTS[0]+'-cycle-35','What is changing compared with my baseline?'),
 ('alert',SUBJECTS[0]+'-cycle-35','Why did I receive this alert?'),
 ('missing',SUBJECTS[1]+'-cycle-18','What information is missing?'),
 ('criteria',SUBJECTS[1]+'-cycle-18','Which criteria have been met?'),
 ('tests',SUBJECTS[1]+'-cycle-18','What tests could resolve the uncertainty?'),
 ('documents',SUBJECTS[1]+'-cycle-18','Which documents support this information?'),
 ('protocol',SUBJECTS[1]+'-cycle-18','Why is the protocol blocked?'),
 ('change',SUBJECTS[1]+'-cycle-18p1','What changed since the previous evaluation?')]

class ASGIReader(ReaderClient):
    """Real authenticated read requests through the existing ASGI API; no write method."""
    def __init__(self,client,token):
        class Transport:
            def call(self,method,path):
                if method!='GET':raise ValueError('READ_ONLY_CLIENT')
                r=client.get(path,headers={'Authorization':'Bearer '+token});r.raise_for_status();return r.json()
            def close(self):pass
        self.client=Transport()

def review(folder,real_inference=False):
    folder=Path(folder).resolve();config=json.loads((folder/'portal-config.json').read_text(encoding='utf8'))
    token=read_secret(folder/'reader-token.txt');tokens=json.loads(read_secret(folder/'server-tokens.json'))
    library=OfflineLibrary(config['library_manifest']);result={'clinical_validation':False,'real_inference_requested':real_inference,'questions':[],'modes':[]}
    with TestClient(create_app(db_path=folder/'vigile.sqlite3',tokens=tokens)) as client:
        engine=client.app.state.engine;bridge=ASGIReader(client,token)
        model=ConversationalInference(config['model_url'],config['model'],provider=config['inference_provider'])
        def ask(kind,target,question):
            before=model.model_http_calls;t=time.perf_counter()
            response=answer_monitoring(bridge,model,target,question,library=library)
            return {'kind':kind,'target':target,'question':question,'elapsed_seconds':time.perf_counter()-t,
                    'model_requests_attempted':model.model_http_calls-before,'generation_accepted':bool(response['generated']),'response':response}
        if not real_inference:model.status=lambda:{'available':False,'reason':'OFFLINE_DEMO_NO_GENERATION_REQUESTED'}
        for kind,target,question in QUESTIONS:result['questions'].append(ask(kind,target,question))
        target=SUBJECTS[0]+'-cycle-35';original=engine.store.get('monitoring_run',target)['output_hash']
        for mode in ('FULL','LOW_POWER','CRITICAL'):
            model.set_mode(mode);row=ask('resource_mode',target,'What changed from baseline?');row['mode']=mode
            row['clinical_output_unchanged']=original==engine.store.get('monitoring_run',target)['output_hash'];result['modes'].append(row)
        # Inject unavailability only into this demonstration's adapter, never stop Ollama.
        old_status=model.status;model.set_mode('FULL')
        model.status=lambda:{'available':False,'reason':'CONTROLLED_OUTAGE_ADAPTER_FAULT_INJECTION'}
        result['controlled_outage']=ask('controlled_outage',target,'What changed from baseline?')
        model.status=old_status;result['restored_full']=ask('restored_full',target,'What changed from baseline?')
        result['restored_full']['clinical_output_unchanged']=original==engine.store.get('monitoring_run',target)['output_hash']
        result['monitoring_replays']=[client.app.state.monitoring.replay(r['id']) for r in engine.store.all('monitoring_run')]
        result['clinical_replays']=[client.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')]
        result['audit_valid']=engine.store.verify();result['checkpoint']=engine.store.checkpoint()
        assert all(r['matches'] for r in result['monitoring_replays']+result['clinical_replays']) and result['audit_valid']
        assert all(r['clinical_output_unchanged'] for r in result['modes']) and result['restored_full']['clinical_output_unchanged']
        assert result['modes'][-1]['model_requests_attempted']==result['controlled_outage']['model_requests_attempted']==0
        result['implementation_hash']=engine.implementation_hash
    result['hash']=digest(result)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--real-inference',action='store_true');a=p.parse_args()
    if a.report.exists():raise ValueError('REPORT_EXISTS_PRESERVE_PREVIOUS_RESULT')
    r=review(a.output,a.real_inference);a.report.write_text(json.dumps(r,indent=2),encoding='utf8')
    print(json.dumps({'questions':[{'kind':q['kind'],'status':q['response']['status'],'requests':q['model_requests_attempted'],'generated':q['generation_accepted']} for q in r['questions']],
                      'monitoring_replays':len(r['monitoring_replays']),'clinical_replays':len(r['clinical_replays']),'audit_valid':r['audit_valid']},indent=2))
if __name__=='__main__':main()
