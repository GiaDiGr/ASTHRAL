from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'work/v101/r2-runtime/engine'))
from vigile.api import create_app
from fastapi.testclient import TestClient
with TestClient(create_app(R,R/'work/v101/r2-db-copy/vigile.sqlite3',{})) as c:
 engine=c.app.state.engine
 assert engine.implementation_hash=='f01f897bfd3e07328d25817ae6a9062d47cc9e12b66783ad6340286df70e09bf'
 rows=[c.app.state.monitoring.replay(r['id']) for r in engine.store.all('monitoring_run')]+[c.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')]
 assert all(r['matches'] for r in rows) and engine.store.verify()
 report={'archived_code':True,'original_r2_database_opened_by_this_check':False,'isolated_copy_only':True,'implementation_hash':engine.implementation_hash,'replays':rows,'audit_valid':True}
(R/'docs/v101/r2-replay-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(len(rows),'R2 replays match using archived runtime and isolated DB copy')