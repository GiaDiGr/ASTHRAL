from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import protect_secret
from vigile.portal import create_portal
from vigile.api import create_app
from vigile.mission_review import ASGIReader
from fastapi.testclient import TestClient
import uvicorn
folder=R/'engine/data/v100-development';codefile=R/'work/v100/ui-test-access.dpapi'
if not codefile.exists():protect_secret('VIGILE-V100-SYNTHETIC-UI-TEST-ONLY',codefile)
from vigile.local_protection import read_secret
mapping=json.loads(read_secret(folder/'server-tokens.json'));backend=TestClient(create_app(R,folder/'vigile.sqlite3',mapping));backend.__enter__()
cfg=json.loads((folder/'portal-config.json').read_text());cfg['access_code_file']=str(codefile)
try:uvicorn.run(create_portal(cfg,ASGIReader(backend,read_secret(folder/'reader-token.txt'))),host='127.0.0.1',port=8900,access_log=False)
finally:backend.__exit__(None,None,None)