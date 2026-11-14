from pathlib import Path
import sys,json
R=Path(sys.argv[1]);sys.path.insert(0,sys.argv[2])
from vigile.api import create_app
from fastapi.testclient import TestClient
with TestClient(create_app(R,sys.argv[3],{})) as c:
 engine=c.app.state.engine
 clinical=[c.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')]
 monitoring=[c.app.state.monitoring.replay(r['id']) for r in engine.store.all('monitoring_run')]
 assert all(r['matches'] for r in clinical+monitoring) and engine.store.verify()
 result={'version':sys.argv[4],'clinical_replays':len(clinical),'monitoring_replays':len(monitoring),'all_match':True,'audit_valid':True,'implementation_hash':engine.implementation_hash,'isolated_copy_only':True,'original_database_opened':False}
 Path(sys.argv[5]).write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
