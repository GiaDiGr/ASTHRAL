from pathlib import Path
import json, os, re, ssl, subprocess, sys
import httpx
R = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import read_secret
env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
def git(*args, **opts):
    return subprocess.check_output(['git', *args], cwd=R, env=env, **opts)
credential = git('credential', 'fill', input=b'protocol=https\nhost=github.com\nusername=GiaDiGr\n\n')
items = dict(line.split(b'=',1) for line in credential.splitlines() if b'=' in line)
assert items[b'username'].lower()==b'giadigr'
secret = items[b'password']
client = httpx.Client(verify=ssl.create_default_context(), trust_env=False, timeout=20,
                      headers={'Authorization':'Bearer '+secret.decode(),'Accept':'application/vnd.github+json'})
with client:
    repo=client.get('https://api.github.com/repos/GiaDiGr/ASTHRAL').raise_for_status().json()
    assert repo['private'] and repo['owner']['login']=='GiaDiGr'
    assert client.get('https://api.github.com/user').raise_for_status().json()['login']=='GiaDiGr'
    if '--verify' in sys.argv:
        branch=client.get('https://api.github.com/repos/GiaDiGr/ASTHRAL/git/ref/heads/feature/cloudflare-mobile-demo').raise_for_status().json()
        sha=git('rev-parse','HEAD').decode().strip()
        assert branch['object']['sha']==sha
        main=client.get('https://api.github.com/repos/GiaDiGr/ASTHRAL/git/ref/heads/main').raise_for_status().json()
        print(json.dumps({'repository_private':True,'account':'GiaDiGr','branch_sha':sha,'main_sha':main['object']['sha']}))
        raise SystemExit
    else:
        print('Private GitHub repository and GiaDiGr account verified.')
objects={}
for line in git('rev-list','--objects','--all').decode().splitlines():
    pair=line.split(' ',1)
    if len(pair)==2:objects[pair[0]]=pair[1]
for line in git('ls-files','--stage','-z').decode().strip('\0').split('\0'):
    detail,path=line.split('\t',1)
    objects[detail.split()[1]]=path
from vigile.local_protection import _crypt
import sqlite3
new_secrets=[]
for path in (R/'engine/data/cloudflare-public-demo/demo-credentials.dpapi',):
    if path.exists():new_secrets.extend(value.encode() for value in json.loads(read_secret(path)).values())
with sqlite3.connect(R/'engine/data/cloudflare-public-demo/personal.sqlite3') as db:
    new_secrets.extend(_crypt(row[0],True) for row in db.execute('SELECT reader FROM accounts'))
p=subprocess.Popen(['git','cat-file','--batch'],cwd=R,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
secrets=[secret,*new_secrets]
for name in ['reader-token.txt','acquisition-token.txt','portal-access.txt']:
    f=R/'engine/data/asthral-release'/name
    if f.exists():secrets.append(read_secret(f).encode())
bad=[]
count=0
for sha,path in objects.items():
    p.stdin.write(sha.encode()+b'\n');p.stdin.flush()
    _,kind,length=p.stdout.readline().split()
    raw=p.stdout.read(int(length))
    assert p.stdout.read(1)==b'\n'
    if kind!=b'blob':continue
    count+=1
    if any(part in ('data','local_ai','.venv','__pycache__','work') for part in path.split('/')):
        bad.append((path,'private path'))
    if Path(path).suffix.lower() in ('.sqlite','.sqlite3','.db','.zip','.gguf','.mdl','.onnx','.exe','.dll','.log','.pdf','.wav','.dpapi'):
        bad.append((path,'excluded asset'))
    if any(len(s)>20 and s in raw for s in secrets):
        bad.append((path,'actual secret'))
    if re.search(rb'(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|VIGILE-DPAPI-1:[A-Za-z0-9+/=]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|[A-Za-z]:[\\/]Users[\\/]Gianni)',raw):
        bad.append((path,'credential or machine-specific path pattern'))
p.stdin.close();assert p.wait()==0
print(json.dumps({'blobs_scanned':count,'findings':bad}))
assert not bad
