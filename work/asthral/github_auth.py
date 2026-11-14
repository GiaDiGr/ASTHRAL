from pathlib import Path
import subprocess,os,json,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'}
p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\nusername=GiaDiGr\n\n',text=True,capture_output=True,env=env,timeout=30)
v=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
if v.get('password'):
 from vigile.local_protection import protect_secret,restrict_directory
 protect_secret(v['password'],R/'work/asthral/github-token.dpapi');restrict_directory(R/'work/asthral')
 import httpx
 with httpx.Client(trust_env=False,timeout=15,headers={'Authorization':'Bearer '+v['password'],'Accept':'application/vnd.github+json'}) as c:
  r=c.get('https://api.github.com/user');r.raise_for_status();user=r.json()['login']
 (R/'docs/asthral/github-identity.json').write_text(json.dumps({'login':user,'credential_source':'EXISTING_GIT_CREDENTIAL_MANAGER_DEFAULT','verified':True},indent=2),encoding='utf8');print(json.dumps({'authenticated_GitHub_account':user}))
else:print(json.dumps({'credential_available':False,'exit_code':p.returncode,'ambiguous': 'multiple' in p.stderr.lower() or 'ambig' in p.stderr.lower()}))