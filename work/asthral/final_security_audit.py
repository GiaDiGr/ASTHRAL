from pathlib import Path
import subprocess,json,re,sys,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import read_secret
files=subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0');files=[p for p in files if p]
for p in files:
 assert not any(part in p.split('/') for part in ['data','local_ai','.venv','__pycache__','work']),p
 assert Path(p).suffix.lower() not in ['.sqlite','.db','.zip','.gguf','.mdl','.onnx','.exe','.dll','.log','.pdf','.xml'],p
 assert p!='MANIFIESTO_SHA256.json'
secret_values=[read_secret(R/'work/asthral/github-token.dpapi')]
for name in ['reader-token.txt','acquisition-token.txt','portal-access.txt','server-tokens.json']:
 p=R/'engine/data/asthral-release'/name
 if p.exists():
  value=read_secret(p)
  if name=='server-tokens.json':continue
  secret_values.append(value)
objects={}
# Audit every blob in the existing history, plus every exact staged blob.
for line in subprocess.check_output(['git','rev-list','--objects','--all'],cwd=R).decode().splitlines():
 bits=line.split(' ',1)
 if len(bits)==2 and subprocess.check_output(['git','cat-file','-t',bits[0]],cwd=R).strip()==b'blob':objects[bits[0]]=bits[1]
for line in subprocess.check_output(['git','ls-files','--stage'],cwd=R).decode().splitlines():
 before,path=line.split('\t');objects[before.split()[1]]=path
findings=[]
for sha,path in objects.items():
 raw=subprocess.check_output(['git','cat-file','blob',sha],cwd=R)
 if any(secret.encode() in raw for secret in secret_values if len(secret)>20):findings.append({'path':path,'kind':'ACTUAL_CREDENTIAL_MATCH'})
 if re.search(rb'(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|VIGILE-DPAPI-1:[A-Za-z0-9+/=]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)',raw):findings.append({'path':path,'kind':'CREDENTIAL_PATTERN'})
 if re.search(rb'[A-Za-z]:[\\/]Users[\\/]Gianni',raw):findings.append({'path':path,'kind':'MACHINE_PRIVATE_PATH'})
 assert len(raw)<3_000_000,path
manifest=[{'path':p,'sha256':hashlib.sha256(subprocess.check_output(['git','show',':'+p],cwd=R)).hexdigest()} for p in files]
report={'date':'2026-11-04','staged_files':len(files),'history_and_staged_blobs_scanned':len(objects),'findings':findings,'actual_credentials_compared_in_memory':len(secret_values),'private_assets_excluded':True,'third_party_full_text_and_binaries_excluded':True,'project_license_added':False,'manifest':manifest}
(R/'docs/asthral/publication-safety.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ('manifest',)}));assert not findings
