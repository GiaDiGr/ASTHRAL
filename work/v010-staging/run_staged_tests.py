import sys,importlib.util,pytest
from pathlib import Path
import vigile
root=Path(__file__).parent
for name in ('portal_sessions','local_protection','portal_documents','local_assistant','dashboard_api','api','portal'):
 spec=importlib.util.spec_from_file_location('vigile.'+name,root/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;setattr(vigile,name,m);spec.loader.exec_module(m)
raise SystemExit(pytest.main(['tests/test_portal.py',str(root/'test_security_staged.py'),str(root/'test_portal_v010.py'),'-q']))
