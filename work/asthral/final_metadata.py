from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2];p=R/'docs/asthral/publication-safety.json';r=json.loads(p.read_text(encoding='utf8'))
for row in r['manifest']:
 if row['path']=='README.md':row['sha256']=hashlib.sha256((R/'README.md').read_bytes()).hexdigest()
r['post_test_documentation_change']='Only README model-import relative path clarified; no code, criteria or configuration changed.'
p.write_text(json.dumps(r,indent=2),encoding='utf8')
p=R/'work/asthral/verify_remote.py';s=p.read_text(encoding='utf8').replace('asthral-1.1.0.bundle','asthral-1.1.0-final.bundle');(R/'work/asthral/verify_remote_final.py').write_text(s,encoding='utf8')