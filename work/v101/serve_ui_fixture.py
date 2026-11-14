from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.api import create_app
from vigile.portal import create_portal
from vigile.local_protection import read_secret,protect_secret
from vigile.mission_review import ASGIReader
from fastapi.testclient import TestClient
import uvicorn
folder=R/'engine/data/mission-v101-management';codefile=R/'work/v101/ui-fixture.dpapi'
if not codefile.exists():protect_secret('VIGILE-V101-SYNTHETIC-UI-CHECK-ONLY',codefile)
class Offline:
 mode='CRITICAL'
 model='OFFLINE_UI_FIXTURE_NO_GENERATION'
 def status(self):return {'available':False,'reason':'OFFLINE_UI_TEST_ONLY','mode':'CRITICAL'}
 def set_mode(self,mode):self.mode=mode
backend=TestClient(create_app(R,folder/'vigile.sqlite3',json.loads(read_secret(folder/'server-tokens.json'))));backend.__enter__()
config=json.loads((folder/'portal-config.json').read_text());config['access_code_file']=str(codefile)
try:uvicorn.run(create_portal(config,ASGIReader(backend,read_secret(folder/'reader-token.txt')),Offline()),host='127.0.0.1',port=8903,access_log=False)
finally:backend.__exit__(None,None,None)