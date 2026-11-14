from pathlib import Path
import json,sys,httpx,hashlib,zipfile,ast,shutil
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));D=R/'docs/v101';F=R/'engine/data/mission-v101-final'
from vigile.local_protection import read_secret
from vigile.store import digest
report=json.loads((F/'management-report.json').read_text(encoding='utf8'))
dka=report['scenarios'][0]['evaluation'];ana=report['scenarios'][-1]['evaluation'];at=report['scenarios'][3]['evaluation']['management']['DKA']['resource_snapshot']['as_of']
responses={}
with httpx.Client(base_url='http://127.0.0.1:8901',trust_env=False,timeout=30,headers={'Authorization':'Bearer '+read_secret(F/'reader-token.txt')}) as c:
 for name,path,params in [('inventory','/missions/clinical-earth/medical-inventory',{'as_of':at}),('dka','/clinical/evaluations/'+dka['id']+'/management',{}),('anaphylaxis','/clinical/evaluations/'+ana['id']+'/management',{}),('followup','/clinical/evaluations/'+report['monitoring']['clinical_evaluations']['DKA']['id']+'/management-records',{'as_of':report['management_records'][0]['recorded_at']})]:
  response=c.get(path,params=params);response.raise_for_status();responses[name]={'method':'GET','path':path,'params':params,'http_status':response.status_code,'response':response.json()}
 denied=c.post('/clinical/management-records',json=report['management_records'][0]);assert denied.status_code==403
 schema=c.get('/openapi.json');schema.raise_for_status();(D/'openapi.json').write_text(json.dumps(schema.json(),indent=2),encoding='utf8')
responses['reader_write_denied']={'method':'POST','path':'/clinical/management-records','http_status':denied.status_code,'response':denied.json()}
(D/'examples.json').write_text(json.dumps({'synthetic':True,'credentials_omitted':True,'actual_loopback_http':responses,'inventory_input':{k:responses['inventory']['response'][k] for k in ('mission_id','resources')},'scenarios':[{'label':s['label'],'evaluation_id':s['evaluation']['id'],'diagnostic_status':next(iter(s['evaluation']['results'].values()))['diagnostic_status'],'urgency':s['evaluation']['urgency'],'treatment_status':s['evaluation']['treatment_status'],'management':s['evaluation']['management']} for s in report['scenarios']]},ensure_ascii=False,indent=2),encoding='utf8')
shutil.copy2(F/'management-report.json',D/'demo-report.json')
z=zipfile.ZipFile(R/'docs/v100/candidate-code-r2.zip');changed=[];unchanged=[];clinical=[]
for name in z.namelist():
 path=R/name
 if not path.is_file():changed.append({'path':name,'status':'MISSING'});continue
 old=hashlib.sha256(z.read(name)).hexdigest();new=hashlib.sha256(path.read_bytes()).hexdigest()
 (unchanged if old==new else changed).append({'path':name,'r2_sha256':old,'v101_sha256':new})
 if '/clinical_knowledge/' in name:clinical.append({'path':name,'unchanged':old==new,'sha256':new})
assert clinical and all(x['unchanged'] for x in clinical)
newpaths=['engine/vigile/management.py','engine/vigile/web/management.js','engine/tools/demo_management_v101.py','engine/tests/test_management_v101.py','engine/tests/management_ui_unit.cjs','engine/tests/fixtures/management-v101-report.json']
new=[{'path':p,'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest()} for p in newpaths]
(D/'change-manifest.json').write_text(json.dumps({'relative_to':'docs/v100/candidate-code-r2.zip','modified':changed,'added_implementation':new,'unchanged_archived_files':unchanged},indent=2),encoding='utf8')
oldtree=ast.parse(z.read('engine/vigile/clinical_engine.py'));newtree=ast.parse((R/'engine/vigile/clinical_engine.py').read_text(encoding='utf8'))
names=['normalize','dm_confirmation','protocol_eligibility','evaluate_condition'];functions=[]
for name in names:
 old=[ast.dump(n,include_attributes=False) for n in ast.walk(oldtree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 newfunc=[ast.dump(n,include_attributes=False) for n in ast.walk(newtree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 assert old and old==newfunc,name
 functions.append({'function':name,'ast_unchanged':True})
archive_hash=hashlib.sha256((R/'docs/v100/candidate-code-r2.zip').read_bytes()).hexdigest();assert archive_hash==json.loads((D/'checkpoint.json').read_text())['r2_code_archive_sha256']
(D/'preservation.json').write_text(json.dumps({'r2_archive_sha256':archive_hash,'r2_archive_unchanged':True,'clinical_knowledge_files':clinical,'diagnostic_functions':functions,'clinical_knowledge_hash':dka['knowledge_hash'],'clinical_semantic_hash':json.loads((D/'clinical-invariance-v101.json').read_text())['semantic_hash'],'r2_semantic_hash':json.loads((D/'clinical-invariance-r2.json').read_text())['semantic_hash']},indent=2),encoding='utf8')
print(json.dumps({'real_reader_gets':4,'reader_write':403,'modified_files':len(changed),'added_implementation_files':len(new),'clinical_knowledge_files_unchanged':len(clinical),'diagnostic_function_AST_unchanged':len(functions),'implementation_hash':dka['implementation_hash']}))