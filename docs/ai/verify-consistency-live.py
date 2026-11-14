from pathlib import Path
import sys,json,time,hashlib,httpx
root=Path(r'C:\Users\Gianni\Desktop\Vigile');sys.path.insert(0,str(root/'engine'))
from vigile.store import Store,digest
folder=root/'engine/data/portal-consistency-v061'
def snapshot():
 s=Store(folder/'vigile.sqlite3');h=digest([dict(r) for r in s.db.execute('SELECT kind,id,payload FROM records ORDER BY seq')]);assert s.verify();s.close();return h
before=snapshot();rows=[]
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=280,headers={'Origin':'http://127.0.0.1:8896'}) as c:
 c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text()}).raise_for_status()
 data=c.get('/api/dashboard/clinical-crew?mission_id=clinical-earth').json()
 ev=next(e for e in data['evaluations'] if e['condition_id']=='DKA' and not e.get('parent_id'))
 result=ev['results']['DKA']
 assert result['diagnostic_status']=='CRITERIA_MET' and result['missing_required']==[]
 assert result['optional_not_measured']==['bicarbonate_mmol_l','urine_ketones_plus']
 assert result['required_for_protocol_safety']==['potassium_mmol_l']
 assert 'BLOCKED_MISSING_DATA:POTASSIUM' in result['protocol']['block_reasons']
 for mode in ('FULL','LOW_POWER','CRITICAL'):
  c.post('/api/mode',json={'mode':mode}).raise_for_status()
  for question in ('¿Qué datos faltan?','¿Son necesarios bicarbonato y cetonas urinarias para cumplir los criterios?','¿Por qué está bloqueado el protocolo?','Explica los criterios cumplidos.'):
   start=time.perf_counter();r=c.post('/api/assistant',json={'evaluation_id':ev['id'],'question':question});r.raise_for_status();reply=r.json()
   if 'faltan' in question or 'bicarbonato' in question:
    assert not reply['inference_attempted'] and not reply['generated']
    assert reply['consistency_policy']=='ENGINE_DATA_REQUIREMENTS_ONLY'
    text=reply['answer'][0]['text']
    assert 'ramas indeterminadas: ninguno' in text and 'CRITERIA_MET' in text
    assert 'bicarbonato, cetonas urinarias' in text and 'seguridad del protocolo: potasio' in text
   if mode=='CRITICAL':assert not reply['inference_executed']
   row={'mode':mode,'question':question,'elapsed_ms':round((time.perf_counter()-start)*1000),'reply':reply};rows.append(row)
   print(json.dumps({'mode':mode,'question':question,'status':reply['status'],'generated':reply['generated'],'ms':row['elapsed_ms']},ensure_ascii=True),flush=True)
   (root/'docs/ai/consistency-live-checkpoint.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 c.post('/api/mode',json={'mode':'FULL'}).raise_for_status()
 assert c.post('/api/mode',json={'mode':'ADMIN'}).status_code==422
 assert c.post('/api/assistant',json={'evaluation_id':ev['id'],'question':'test'},headers={'Origin':'https://evil.example'}).status_code==403
with httpx.Client(base_url='http://127.0.0.1:8895',trust_env=False,headers={'Authorization':'Bearer '+(folder/'reader-token.txt').read_text()}) as c:
 for e in data['evaluations']:assert c.get('/clinical/evaluations/'+e['id']+'/replay').json()['matches']
 assert c.post('/clinical/evaluations',json={}).status_code==403
 assert c.get('/dashboard/subjects/other?mission_id=clinical-earth').status_code==403
 assert c.get('/clinical/evaluations/'+ev['id']+'/next-tests').json()==ev['next_tests']
 (root/'docs/ai/openapi-consistency.json').write_text(json.dumps(c.get('/openapi.json').json(),indent=2),encoding='utf-8')
assert before==snapshot()
report={'synthetic_only':True,'provider':'ollama','model':'vigile-qwen3-4b:latest','queries':rows,
        'dka_result':result,'next_tests':ev['next_tests'],'record_hash_unchanged':before,'audit_valid':True,
        'replays':len(data['evaluations']),'reader_write_denied':True,'scope_enforced':True,'csrf_enforced':True,
        'clinical_validation':False}
(root/'docs/ai/consistency-live-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert any(r['reply']['generated'] for r in rows),'No generated explanation passed checks'
print('LIVE_CONSISTENCY_VERIFIED')
