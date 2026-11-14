from pathlib import Path
import json
from fastapi.testclient import TestClient
from vigile.api import create_app
root=Path(r'C:\Users\Gianni\Desktop\Vigile');folder=root/'engine/data/portal-v090-release'
mapping=json.loads((folder/'server-tokens.json').read_text());report={'scope':'ARCHIVED_V09_CODE_ON_VERIFIED_RESTORED_V09_DATABASE','replays':[]}
with TestClient(create_app(root,root/'engine/data/backups/v090-restore-check/vigile.sqlite3',mapping)) as c:
 headers={'Authorization':'Bearer '+(folder/'reader-token.txt').read_text().strip()}
 report['implementation_hash']=c.app.state.engine.implementation_hash
 for subject in c.get('/dashboard/subjects',headers=headers).json():
  data=c.get('/dashboard/subjects/'+subject['id'],params={'mission_id':subject['mission_id']},headers=headers).json()
  for key,prefix in [('evaluations','/clinical/evaluations/'),('monitoring','/monitoring/cycles/')]:
   for e in data[key]:
    response=c.get(prefix+e['id']+'/replay',headers=headers);response.raise_for_status();report['replays'].append({'id':e['id'],'matches':response.json()['matches']})
 assert all(r['matches'] for r in report['replays'])
(root/'docs/v010/archived-v09-replay-check.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(len(report['replays']),'archived replays matched',report['implementation_hash'])
