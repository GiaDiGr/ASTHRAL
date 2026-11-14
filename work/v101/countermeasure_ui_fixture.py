from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.management import countermeasure_documents
from vigile.registry import Registry
p=R/'engine/tests/fixtures/management-v101-report.json';v=json.loads(p.read_text(encoding='utf8'));v['countermeasure_documents']=countermeasure_documents(Registry(R));p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
p=R/'engine/tests/management_ui_unit.cjs';s=p.read_text(encoding='utf8');s=s.replace("console.log('5 simulated DOM", "{const h=harness({id:'none'});h.c.dashboard.countermeasure_documents=report.countermeasure_documents;h.c.dashboard.measurements=[{measurement:{variable:'physiology.strength'}},{measurement:{variable:'radiation.interval_effective_dose'}},{measurement:{variable:'sleep.duration'}}];h.c.dashboard.mission.phase='POST_MISSION';h.c.renderMonitoring();const text=h.text(h.nodes['space-monitoring']);assert.match(text,/C002/);assert.match(text,/C032/);assert.match(text,/C005/);assert.doesNotMatch(text,/C009/);assert.equal(h.c.originalMonitoring,1);}\nconsole.log('6 simulated DOM")
p.write_text(s,encoding='utf8')