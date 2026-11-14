from pathlib import Path
import sys,json,hashlib,shutil,platform,importlib.metadata,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'));OUT=ROOT/'docs/v011';folder=ROOT/'engine/data/mission-v011-final'
from vigile.store import Store,digest
from vigile.local_protection import read_secret,verify_anchor
from vigile.local_assistant import ReaderClient
import httpx
xml=ET.parse(OUT/'release-tests.xml');suites=list(xml.getroot().iter('testsuite'));tests=sum(int(s.get('tests',0)) for s in suites);failures=sum(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites)
assert tests==582 and failures==0
summary=json.loads((folder/'summary.json').read_text(encoding='utf8'))
real=json.loads((OUT/'assistant-final-real.json').read_text(encoding='utf8'));offline=json.loads((OUT/'assistant-final-offline.json').read_text(encoding='utf8'))
implementation=digest({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'engine/vigile').glob('*.py')})
assert implementation==summary['implementation_hash']==real['implementation_hash']==offline['implementation_hash']
report={'release':'0.11.0','clinical_validation':False,'operational_validation':False,'space_validation':False,'tests':{'passed':tests,'failures':failures,'seconds':float(suites[0].get('time')),'warning':'Starlette/httpx deprecation'},'implementation_hash':implementation,'knowledge_hash':summary['knowledge_hash'],'request_hash':summary['request_hash'],'semantic_hash':summary['semantic_hash'],'cycles':summary['cycles'],'clinical_replays':len(real['clinical_replays']),'monitoring_replays':len(real['monitoring_replays']),'all_replays_match':all(x['matches'] for x in real['clinical_replays']+real['monitoring_replays']),'performance':summary['performance'],'mission_wall_seconds':summary['total_seconds'],'database_bytes':summary['database_bytes'],'assistant_questions':[],'modes':[],'dependencies':{'python':platform.python_version(),**{n:importlib.metadata.version(n) for n in ('fastapi','pydantic','uvicorn','httpx','pytest')}}}
for q in real['questions']:
 report['assistant_questions'].append({'kind':q['kind'],'status':q['response']['status'],'requests':q['model_requests_attempted'],'accepted':q['generation_accepted'],'seconds':q['elapsed_seconds'],'failure_trace':q['response'].get('failure_trace')})
for q in real['modes']+[real['controlled_outage'],real['restored_full']]:
 report['modes'].append({'kind':q['kind'],'mode':q.get('mode',q['response']['mode']),'status':q['response']['status'],'requests':q['model_requests_attempted'],'accepted':q['generation_accepted'],'clinical_output_unchanged':q.get('clinical_output_unchanged',True)})
assert sum(q['model_requests_attempted'] for q in offline['questions']+offline['modes']+[offline['controlled_outage'],offline['restored_full']])==0
report['offline_requests']=0
with httpx.Client(trust_env=False,timeout=10) as c:report['health']={str(port):c.get('http://127.0.0.1:'+str(port)+('/health' if port in (8895,8897) else '/')).status_code for port in (8895,8896,8897,8898)}
bridge=ReaderClient('http://127.0.0.1:8897',read_secret(folder/'reader-token.txt'))
try:
 report['http_subjects']=bridge.get('/dashboard/subjects');idx=bridge.get('/dashboard/frames/mission-crew-B?mission_id=mission-v011')
 path='/dashboard/subjects/mission-crew-B?mission_id=mission-v011&frame_id=frame-mission-crew-B-cycle-18';data=bridge.get(path)
 examples={'authorization':'SERVER_READER_ONLY_VALUE_OMITTED','frames':{'request':'GET /dashboard/frames/mission-crew-B?mission_id=mission-v011','response':idx},'acute_frame':{'request':'GET '+path,'response':data}}
 (OUT/'api-examples.json').write_text(json.dumps(examples,indent=2),encoding='utf8')
finally:bridge.close()
old=ROOT/'engine/data/portal-v0100-integrated';legacy=ReaderClient('http://127.0.0.1:8895',read_secret(old/'reader-token.txt'));old_replays=[]
try:
 for subject in legacy.get('/dashboard/subjects'):
  d=legacy.get('/dashboard/subjects/'+subject['id']+'?mission_id='+subject['mission_id'])
  for key,prefix in [('evaluations','/clinical/evaluations/'),('monitoring','/monitoring/cycles/')]:
   for row in d[key]:old_replays.append(legacy.get(prefix+row['id']+'/replay'))
finally:legacy.close()
assert len(old_replays)==39 and all(x['matches'] for x in old_replays)
report['legacy_http_replays']={'count':len(old_replays),'all_match':True}
(OUT/'legacy-http-replays.json').write_text(json.dumps(old_replays,indent=2),encoding='utf8')
external=Path.home()/'AppData/Local/Vigile/integrity';report['anchor']=verify_anchor(folder/'vigile.sqlite3',external/'mission-v011-final.anchor.json',external/'audit-key.dpapi')
pin=json.loads((ROOT/'docs/v010/reserved-bank-pin.json').read_text());assert hashlib.sha256((ROOT/pin['path']).read_bytes()).hexdigest()==pin['sha256'];report['reserved_bank']={**pin,'unchanged':True}
store=Store(folder/'vigile.sqlite3')
try:
 report['records']={k:len(store.all(k)) for k in ('measurement','baseline','device','mission_context','mission_frame','episode','followup')};assert store.verify();report['audit_valid']=True
finally:store.close()
for name in ('desktop','narrow','monitoring'):
 shutil.copyfile(Path('C:/Users/Gianni/Documents/Codex')/('vigile-v011-'+name+'.png'),OUT/'screenshots'/('mission-'+name+'.png'))
shutil.copyfile(folder/'openapi.json',OUT/'backend-openapi.json')
(OUT/'mission-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
(OUT/'RESULTS.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:report[k] for k in ('tests','implementation_hash','clinical_replays','monitoring_replays','health','legacy_http_replays','records','mission_wall_seconds','database_bytes')},indent=2))
print(json.dumps(report['assistant_questions'],indent=2));print(json.dumps(report['modes'],indent=2));print(json.dumps(report['performance'],indent=2))