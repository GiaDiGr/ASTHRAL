from pathlib import Path
import sys,json,httpx,time
root=Path(r'C:\Users\Gianni\Desktop\Vigile');sys.path.insert(0,str(root/'engine'))
from vigile.store import Store,digest
folder=root/'engine/data/portal-v080-final'
def snapshot():
    s=Store(folder/'vigile.sqlite3')
    try:assert s.verify();return digest([dict(r) for r in s.db.execute('SELECT kind,id,payload FROM records ORDER BY seq')])
    finally:s.close()
before=snapshot();cycles=[];latencies=[]
with httpx.Client(base_url='http://127.0.0.1:8895',trust_env=False,timeout=30,headers={'Authorization':'Bearer '+(folder/'reader-token.txt').read_text().strip()}) as c:
    assert c.get('/health').json()['version']=='0.8.0'
    for scenario in 'ABC':
        t=time.perf_counter();r=c.get('/monitoring/cycles',params={'subject_id':'v07-crew-'+scenario,'mission_id':'v07-mission-'+scenario});r.raise_for_status();latencies.append((time.perf_counter()-t)*1000);cycles+=r.json()
    for cycle in cycles:
        assert 'replay_records' not in cycle
        r=c.get('/monitoring/cycles/'+cycle['id']+'/replay');r.raise_for_status();assert r.json()['matches']
        for evaluation in cycle['clinical_evaluations'].values():assert c.get('/clinical/evaluations/'+evaluation['id']+'/replay').json()['matches']
    assert c.post('/monitoring/cycles',json={}).status_code==403
    assert c.get('/monitoring/cycles',params={'subject_id':'other','mission_id':'v07-mission-A'}).status_code==403
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=120,headers={'Origin':'http://127.0.0.1:8896'}) as c:
    assert 'space-monitoring' in c.get('/').text
    c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status()
    data=c.get('/api/dashboard/v07-crew-B?mission_id=v07-mission-B').json();assert len(data['monitoring'])==5
    eid=next(r for r in cycles if r['id']=='B-cycle-0')['clinical_evaluations']['HYPOGLYCEMIA']['id']
    r=c.post('/api/assistant',json={'evaluation_id':eid,'question':'¿Qué datos faltan?'});r.raise_for_status();exact=r.json()
    assert exact['consistency_policy']=='ENGINE_DATA_REQUIREMENTS_ONLY' and not exact['inference_attempted']
    assert any('CRITERIA_MET' in a['text'] for a in exact['answer'])
    t=time.perf_counter();r=c.post('/api/assistant',json={'evaluation_id':eid,'question':'Explica el criterio evaluado por el motor.'});r.raise_for_status();generated=r.json();inference_seconds=time.perf_counter()-t
    status=c.get('/api/status').json()
with httpx.Client(trust_env=False,timeout=10) as c:
    tags=c.get('http://127.0.0.1:8891/api/tags');tags.raise_for_status();assert any(m['name']=='vigile-qwen3-4b:latest' for m in tags.json()['models'])
assert snapshot()==before
old=json.loads((root/'engine/data/portal-v070/portal-config.json').read_text());new=json.loads((folder/'portal-config.json').read_text())
assert {k:v for k,v in old.items() if k not in ('reader_token_file','access_code_file','library_manifest')}=={k:v for k,v in new.items() if k not in ('reader_token_file','access_code_file','library_manifest')}
report={'synthetic_only':True,'clinical_validation':False,'monitoring_http_replays':len(cycles),'clinical_http_replays':sum(len(r['clinical_evaluations']) for r in cycles),'reader_write_denied':True,'scope_enforced':True,'persisted_records_unchanged':True,'audit_valid':True,'dashboard_cycles_B':len(data['monitoring']),'read_list_latencies_ms':latencies,'ollama_configuration_unchanged':True,'model_present':'vigile-qwen3-4b:latest','assistant_sufficiency':exact,'assistant_generation':generated,'inference_seconds':inference_seconds,'portal_status':status}
(root/'docs/v08/live-release.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('assistant_sufficiency','assistant_generation','portal_status')}|{'generation_status':generated['status'],'inference_attempted':generated['inference_attempted'],'inference_executed':generated['inference_executed']},indent=2))


