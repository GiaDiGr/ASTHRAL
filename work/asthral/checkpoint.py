from pathlib import Path
import sys,json,hashlib,subprocess,os
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
f=json.loads((R/'docs/v101-ux/CODE_FREEZE_UX.json').read_text(encoding='utf8'));assert all(hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in f['files'])
for path,key in [('docs/v101-ux/candidate-code-v101-ux.zip',f['sha256']),('docs/v101/candidate-code-v101.zip',json.loads((R/'docs/v101/CODE_FREEZE.json').read_text())['sha256']),('docs/v100/candidate-code-r2.zip',json.loads((R/'docs/v101/checkpoint.json').read_text())['r2_code_archive_sha256'])]:assert hashlib.sha256((R/path).read_bytes()).hexdigest()==key
from vigile.local_protection import verified_backup,restrict_directory
backup=verified_backup(R/'engine/data/mission-v101-astronaut/vigile.sqlite3',R/'work/asthral/baseline-db');restrict_directory(R/'work/asthral/baseline-db')
(R/'docs/asthral/checkpoint.json').write_text(json.dumps({'previous_archives_verified':True,'previous_sources_verified':True,'originals_unchanged':True,'backup':backup,'date':'2026-11-04'},indent=2),encoding='utf8')
env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'}
try:
 p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=env,timeout=30)
 values=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
 authenticated=bool(values.get('password'))
 if authenticated:
  from vigile.local_protection import protect_secret
  protect_secret(values['password'],R/'work/asthral/github-token.dpapi');restrict_directory(R/'work/asthral')
 print(json.dumps({'git_credential_available':authenticated,'credential_helper':'manager','interactive_login_attempted':False}))
except subprocess.TimeoutExpired:print(json.dumps({'git_credential_available':False,'reason':'NONINTERACTIVE_CREDENTIAL_HELPER_TIMEOUT'}))