import sys,importlib.util,pytest
from pathlib import Path
import vigile
root=Path(__file__).parent
for name in ('portal_sessions','local_protection','portal_documents','local_assistant','dashboard_api','api','portal'):
 spec=importlib.util.spec_from_file_location('vigile.'+name,root/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;setattr(vigile,name,m);spec.loader.exec_module(m)
import uvicorn,json
config=json.loads((root.parents[1]/'engine/data/portal-v090-release/portal-config.json').read_text())
uvicorn.run(sys.modules['vigile.portal'].create_portal(config),host='127.0.0.1',port=8897,access_log=False)
