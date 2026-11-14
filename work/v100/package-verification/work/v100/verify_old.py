from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'work/v100/v011-runtime/engine'))
from vigile.api import create_app
from fastapi.testclient import TestClient
from vigile.local_protection import read_secret
folder=R/'engine/data/mission-v011-final';mapping=json.loads(read_secret(folder/'server-tokens.json'))
with TestClient(create_app(R,R/'engine/data/backups/v011-before-v100/vigile.sqlite3',mapping)) as c:
 rows=[c.app.state.monitoring.replay(r['id']) for r in c.app.state.engine.store.all('monitoring_run')]+[c.app.state.clinical.replay(r['id']) for r in c.app.state.engine.store.all('clinical_evaluation')]
 report={'archived_implementation_hash':c.app.state.engine.implementation_hash,'replays':rows,'audit_valid':c.app.state.engine.store.verify(),'original_database_modified':False}
 assert all(r['matches'] for r in rows) and report['audit_valid']
(R/'docs/v100/archived-v011-replays.json').write_text(json.dumps(report,indent=2));print(len(rows),'archived replay matches')