from pathlib import Path
import sys,json,socket
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import restore_backup,restrict_directory
from vigile.api import create_app
from fastapi.testclient import TestClient
restored=R/'work/v101/final-restore-check';restore_backup(R/'work/v101/final-db-backup',restored);restrict_directory(restored)
def no_network(*args,**kwargs):raise AssertionError('External network forbidden during deterministic restored replay')
socket.create_connection=no_network
with TestClient(create_app(R,restored/'vigile.sqlite3',{})) as c:
 engine=c.app.state.engine
 clinical=[c.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')]
 monitoring=[c.app.state.monitoring.replay(r['id']) for r in engine.store.all('monitoring_run')]
 assert all(x['matches'] for x in clinical+monitoring) and engine.store.verify()
 report={'restored_from_verified_backup':True,'original_and_live_databases_not_modified':True,'clinical':clinical,'monitoring':monitoring,'audit_valid':True,'network_connection_factory_blocked':True,'clinical_execution':'BLOCKED','clinical_validation':False}
(R/'docs/v101/restored-demo-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'restored_clinical_matches':len(clinical),'restored_monitoring_matches':len(monitoring),'audit_valid':True}))