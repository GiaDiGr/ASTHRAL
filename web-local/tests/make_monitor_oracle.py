import json,sys,zipfile,tempfile,importlib.util,os
from pathlib import Path
from types import SimpleNamespace
r=Path(__file__).resolve().parents[2];sys.path.insert(0,str(r/'engine'))
from vigile.store import Store
from vigile.models import MissionContext,AstronautProfile
dist=Path(os.environ.get('ASTHRAL_TEST_DIST',r/'web-local/dist')).resolve()
samples=json.loads((r/'web-local/tests/fixtures/statistics-inputs.json').read_bytes());case=json.loads((dist/'parity-cases.json').read_bytes())
inputs=[]
for row in samples[0]['snapshots']:
 inputs.append({'action':'ingest','data':{'device':row['device'],'measurement':{**row['measurement'],'subject_id':'profile-monitor-test','mission_id':'browser-mission'}}})
inputs.append({'action':'baseline','data':{**samples[0]['request'],'id':'baseline-web-native','as_of':'2026-07-30T12:00:00Z'}})
for i,time in enumerate(['2026-10-15T12:00:00Z','2026-10-16T12:00:00Z']):
 m={**samples[0]['snapshots'][0]['measurement'],'id':'current-'+str(i),'timestamp':time,'phase':'IN_MISSION','value':45.-i,'subject_id':'profile-monitor-test','mission_id':'browser-mission'}
 inputs.append({'action':'ingest','data':{'device':samples[0]['snapshots'][0]['device'],'measurement':m}})
observations=next(x for x in case if x['id']=='DM-05')['snapshot']['request']['observations']
inputs.append({'action':'monitor','data':{'id':'cycle-native-web','subject_id':'profile-monitor-test','mission_id':'browser-mission','as_of':'2026-10-16T12:00:00Z','history_start':'2026-07-25T12:00:00Z','clinical_window_start':'2026-10-09T12:00:00Z','clinical_context_id':'dka-context','policy_reference':'SYNTHETIC_PARITY_NOT_CLINICAL_VALIDATION','population':'NONPREGNANT_ADULT','age_years':35,'observations':observations,'baseline_ids':['baseline-web-native'],'followup_at':'2026-10-17T12:00:00Z'}})
with tempfile.TemporaryDirectory() as temporary:
 with zipfile.ZipFile(dist/'engine.zip') as z:z.extractall(temporary)
 spec=importlib.util.spec_from_file_location('browser_monitoring',Path(temporary)/'browser_monitoring.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 store=Store(':memory:');mission=MissionContext(id='browser-mission',phase='IN_MISSION',gravity='EARTH',environment='HABITABLE_CABIN',mode='NOMINAL',synthetic=True)
 store.put('mission',mission.id,mission.model_dump(mode='json'));store.put('profile','profile-monitor-test',AstronautProfile(id='profile-monitor-test',mission_id=mission.id,synthetic=True).model_dump(mode='json'))
 engine=module.LocalBiomedical(store,'profile-monitor-test')
 for step in inputs:result=engine.dispatch(step['action'],step['data'])
 fixture={'steps':inputs,'expected':result,'replay':engine.dispatch('replay_monitor',{'id':result['id']})}
 (r/'web-local/tests/fixtures/monitor-native-oracle.json').write_text(json.dumps(fixture,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print({'monitor_output_hash':result['output_hash'],'episodes':result['episode_ids'],'followups':len(result['followup_ids']),'replay':fixture['replay']})
