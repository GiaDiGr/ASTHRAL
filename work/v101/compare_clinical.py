from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];version=sys.argv[1];sys.path.insert(0,str(R/('work/v101/r2-runtime/engine' if version=='r2' else 'engine')))
from vigile.store import Store,digest
from vigile.registry import Registry
from vigile.service import Engine
from vigile.clinical_engine import ClinicalService
from vigile.clinical_simulator import report_case
from vigile.models import MissionContext,AstronautProfile
store=Store(':memory:');engine=Engine(Registry(R),store)
engine.register('mission',MissionContext(id='clinical-earth',phase='PRE_MISSION',gravity='EARTH',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=True),'researcher');engine.register('profile',AstronautProfile(id='clinical-crew',mission_id='clinical-earth',synthetic=True),'researcher')
service=ClinicalService(engine);rows=[]
for case in service.knowledge.documents['synthetic_cases']['cases']:
 out=service.evaluate(report_case(case),'researcher')
 rows.append({'case':case['id'],'results':out['results'],'differential':out['differential'],'next_tests':out['next_tests'],'urgency':out['urgency'],'treatment_status':out['treatment_status'],'presentation_protocol':out['presentation_protocol']})
store.close();(R/('docs/v101/clinical-invariance-'+version+'.json')).write_text(json.dumps({'version':version,'cases':rows,'semantic_hash':digest(rows)},indent=2),encoding='utf8');print(version,len(rows),digest(rows))