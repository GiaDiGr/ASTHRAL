from pathlib import Path
import sys,json,socket
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
def forbid(*args,**kwargs):raise AssertionError('Internet/model connection forbidden in offline verification')
socket.create_connection=forbid
from vigile.mission_review import review
result=review(R/'engine/data/mission-v101-astronaut',False)
assert all(q['model_requests_attempted']==0 for q in result['questions']+result['modes']+[result['controlled_outage'],result['restored_full']])
result['external_connection_factory_blocked']=True;result['real_browser_offline_test']=False;result['no_Ollama_configuration_changes']=True
(R/'docs/v101-ux/offline-modes.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'questions':len(result['questions']),'modes':[m['mode'] for m in result['modes']],'model_requests':0,'all_mode_outputs_unchanged':all(m['clinical_output_unchanged'] for m in result['modes']),'audit_valid':result['audit_valid']}))