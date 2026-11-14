"""Disposable UI test portal: synthetic read scope, its own non-production test code.
Never decrypts/copies the release portal access code or any historical credential.
The existing reader credential is consumed privately by the normal BFF adapter.
"""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from vigile.local_protection import protect_secret,restrict_directory
from vigile.portal import create_portal
import uvicorn
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'work/v011/ui-fixture'
folder.mkdir(exist_ok=True)
if not (folder/'test-access.dpapi').exists():protect_secret('VIGILE-SYNTHETIC-UI-TEST-ONLY-42',folder/'test-access.dpapi')
restrict_directory(folder)
cfg=json.loads((ROOT/'engine/data/v011-development-03/portal-config.json').read_text(encoding='utf8'))
cfg['access_code_file']=str(folder/'test-access.dpapi');cfg['session_absolute_seconds']=600;cfg['session_idle_seconds']=600
class Offline:
    mode='CRITICAL'
    def status(self):return {'available':False,'reason':'UI_FIXTURE_OFFLINE_NO_GENERATION'}
app=create_portal(cfg,inference=Offline())
uvicorn.run(app,host='127.0.0.1',port=8900,access_log=False)
