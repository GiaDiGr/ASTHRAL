"""ONE-SHOT reserved evaluation, only after freeze. Locks before opening questions.
Never reuse this bank as unseen. Does not change code, clinical rules or model settings.
"""
from pathlib import Path
import sys,json,secrets,time,hashlib,datetime
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
def main():
 from fastapi.testclient import TestClient
 from vigile.api import create_app
 from vigile.clinical_demo import run
 from vigile.monitoring_demo import scenarios
 from vigile.conversational import ConversationalInference
 from vigile.local_assistant import answer
 from vigile.longitudinal_assistant import answer_monitoring
 from vigile.offline_library import OfflineLibrary
 from vigile.mission_review import ASGIReader
 from vigile.integration import deny_external_network
 from vigile.store import digest
 freeze=json.loads((ROOT/'docs/v100/CANDIDATE_FREEZE.json').read_text())
 for rel,expected in freeze['files'].items():
  if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:raise ValueError('CANDIDATE_CHANGED: '+rel)
 bank=ROOT/'docs/v09/reserved-bank.json';expected='c1a75f8f0a792ebd094bda50bd5790b302a6c2c8475cdce0a0a5d239f76651e0'
 if hashlib.sha256(bank.read_bytes()).hexdigest()!=expected:raise ValueError('BANK_HASH_CHANGED')
 output=ROOT/'docs/v100/reserved';output.mkdir(exist_ok=False)
 used=ROOT/'docs/v100/RESERVED_USED.json'
 with used.open('x',encoding='utf8') as f:json.dump({'status':'USED_EXECUTION_STARTED_NO_RERUN','bank_sha256':expected,'freeze_sha256':hashlib.sha256((ROOT/'docs/v100/CANDIDATE_FREEZE.json').read_bytes()).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},f,indent=2)
 cases=json.loads(bank.read_text(encoding='utf8'))['cases'] # FIRST content read, after lock + freeze
 deny_external_network()
 folder=ROOT/'engine/data/v100-reserved-fixture';run(ROOT,folder)
 writer,reader=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
 tokens={writer:'researcher',reader:{'id':'reserved-reader','role':'reader','subject_ids':['clinical-crew']+['v07-crew-'+s for s in 'ABC'],'mission_ids':['clinical-earth']+['v07-mission-'+s for s in 'ABC']}}
 config=json.loads((ROOT/'engine/data/mission-v100-final/portal-config.json').read_text())
 report={'bank_used':True,'single_execution':True,'candidate_freeze':freeze['implementation_hash'],'clinical_validation':False,'rows':[],'grader':'Functional status/citations retained; expected semantic category requires independent human adjudication'}
 library=OfflineLibrary(ROOT/'engine/local_ai/library-v080.json')
 with TestClient(create_app(ROOT,folder/'vigile.sqlite3',tokens)) as client:
  engine=client.app.state.engine
  def submit(req):
   r=client.post('/monitoring/cycles',json=req.model_dump(mode='json'),headers={'Authorization':'Bearer '+writer});r.raise_for_status();return r.json()
  scenarios(engine,submit)
  dka=next(r for r in engine.store.all('clinical_evaluation') if r['snapshot']['request']['condition_id']=='DKA' and not r.get('parent_id'))
  bridge=ASGIReader(client,reader);before=digest([(r['id'],r['output_hash']) for r in engine.store.all('monitoring_run')]);model=ConversationalInference(config['model_url'],config['model'],'FULL',config['inference_provider']);model.structured_explanations=True
  calls=[];complete=model._complete
  def traced(*args):
   out=complete(*args);calls.append({'raw_output':out[0],'metrics':out[1]});return out
  model._complete=traced
  for case in cases:
   start=time.perf_counter();calls.clear();row={'case':case}
   try:
    if case['target']=='DKA':reply=answer(bridge,model,dka['id'],case['question'],case.get('history',()),library)
    else:reply=answer_monitoring(bridge,model,case['target'],case['question'],case.get('history',()),library,'es' if any(w in case['question'].lower() for w in ('¿','qué','como','explica','glucosa','datos','puede')) else 'en')
    row.update(response=reply,raw_model_calls=list(calls),generated_sentences=len(reply.get('generated',[])),status=reply['status'])
   except Exception as exc:row.update(error_type=type(exc).__name__,error_code=str(exc)[:200],raw_model_calls=list(calls))
   row['seconds']=time.perf_counter()-start;report['rows'].append(row);(output/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8');print(case['id'],row.get('status',row.get('error_code')),flush=True)
  report['clinical_outputs_unchanged']=before==digest([(r['id'],r['output_hash']) for r in engine.store.all('monitoring_run')]);report['audit_valid']=engine.store.verify()
 report['total']=len(report['rows']);report['generated_cases']=sum(r.get('generated_sentences',0)>0 for r in report['rows']);report['errors']=sum('error_type' in r for r in report['rows']);(output/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 state=json.loads(used.read_text());state.update(status='USED_COMPLETED_NO_LONGER_UNSEEN',cases_recorded=report['total']);used.write_text(json.dumps(state,indent=2),encoding='utf8')
if __name__=='__main__':main()