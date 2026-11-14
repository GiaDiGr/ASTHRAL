from pathlib import Path
import sys,json,ssl,httpx,hashlib,subprocess,os
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import read_secret
p=R/'work/asthral/github-token.dpapi'
if p.exists():
 with httpx.Client(trust_env=False,verify=ssl.create_default_context(),timeout=15,headers={'Authorization':'Bearer '+read_secret(p),'Accept':'application/vnd.github+json'}) as c:
  r=c.get('https://api.github.com/user');r.raise_for_status();user=r.json()['login'];assert user=='GiaDiGr';repo=c.get('https://api.github.com/repos/'+user+'/ASTHRAL')
 (R/'docs/asthral/github-identity.json').write_text(json.dumps({'login':user,'credential_source':'EXISTING_GIT_CREDENTIAL_MANAGER_EXPLICIT_USER_CHOICE','verified':True,'existing_ASTHRAL_status':repo.status_code},indent=2),encoding='utf8');print(json.dumps({'account':user,'existing_ASTHRAL_status':repo.status_code}))
from vigile.registry import CATALOGS
paths=[p for p,k in CATALOGS.values()]+[str(p.relative_to(R)).replace('\\','/') for pattern in ['02_REGLAS_ORIGINALES_15/individual/*.json','03_CATALOGO/condiciones_individuales/*.json'] for p in R.glob(pattern)]+['03_CATALOGO/matriz_cobertura_44x11.csv']
(R/'ASTHRAL_CORPUS_SHA256.json').write_text(json.dumps([{'path':p,'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest()} for p in sorted(set(paths))],indent=2),encoding='utf8')
ignore='''# Default deny: stage only reviewed, redistributable source and metadata.
/*
!/.gitignore
!/README.md
!/CONTRIBUTING.md
!/SECURITY.md
!/THIRD_PARTY_NOTICES.md
!/ASTHRAL_CORPUS_SHA256.json
!/engine/
!/docs/
!/02_REGLAS_ORIGINALES_15/
!/03_CATALOGO/
!/04_ALGORITMOS/
!/05_SENSORES/
!/06_MULTISISTEMA/
!/07_EVIDENCIAS/
!/08_DATASETS/
!/09_TESTS/
/engine/*
!/engine/vigile/
!/engine/tests/
!/engine/tools/
!/engine/pyproject.toml
!/engine/requirements-v100.lock.txt
!/engine/config.example.json
/docs/*
!/docs/asthral/
!/docs/knowledge/
/docs/asthral/*
!/docs/asthral/*.md
!/docs/asthral/*.example.json
**/__pycache__/
**/.pytest_cache/
**/*.pyc
**/*.sqlite*
**/*.db
**/*-wal
**/*-shm
**/*.dpapi
**/.env*
**/*token*.txt
**/*tokens*.json
**/*portal-config*.json
**/*.gguf
**/*.onnx
**/*.mdl
**/*.zip
**/*.log
'''
(R/'.gitignore').write_text(ignore,encoding='utf8')
if not (R/'.git').exists():
 subprocess.run(['git','init','-b','main'],cwd=R,check=True,capture_output=True)
 # Author is the owner-selected GitHub account, using its public no-reply address.
 subprocess.run(['git','config','user.name','GiaDiGr'],cwd=R,check=True);subprocess.run(['git','config','user.email','GiaDiGr@users.noreply.github.com'],cwd=R,check=True)
 selected=['.gitignore','ASTHRAL_CORPUS_SHA256.json']+paths+[str(p.relative_to(R)).replace('\\','/') for directory in ['engine/vigile','engine/tests','engine/tools'] for p in (R/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.js','.cjs','.html','.css','.json','.ps1')]+['engine/pyproject.toml','engine/requirements-v100.lock.txt']
 subprocess.run(['git','add','--']+selected,cwd=R,check=True,capture_output=True)
 # Baseline stays local until the complete staged/history audit before any push.
 subprocess.run(['git','commit','-m','Preserve v1.0.1 source baseline; historical evidence remains local'],cwd=R,check=True,capture_output=True)
 subprocess.run(['git','switch','-c','feature/asthral-hybrid'],cwd=R,check=True,capture_output=True)
 print('Local baseline committed; feature/asthral-hybrid created. Nothing pushed.')