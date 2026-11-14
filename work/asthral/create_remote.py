from pathlib import Path
import sys,json,ssl,httpx
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import read_secret
with httpx.Client(verify=ssl.create_default_context(),trust_env=False,timeout=20,headers={'Authorization':'Bearer '+read_secret(R/'work/asthral/github-token.dpapi'),'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}) as c:
 account=c.get('https://api.github.com/user');account.raise_for_status();assert account.json()['login']=='GiaDiGr'
 existing=c.get('https://api.github.com/repos/GiaDiGr/ASTHRAL')
 if existing.status_code==404:
  response=c.post('https://api.github.com/user/repos',json={'name':'ASTHRAL','description':'Offline-first astronaut health monitoring and medical decision-support research prototype for NASA Space Apps Challenge 2026.','private':True,'auto_init':False});response.raise_for_status();repo=response.json();created=True
 else:
  existing.raise_for_status();repo=existing.json();created=False
  commits=c.get('https://api.github.com/repos/GiaDiGr/ASTHRAL/commits',params={'per_page':1})
  if commits.status_code!=409:raise RuntimeError('EXISTING_REMOTE_HAS_HISTORY_REVIEW_REQUIRED')
 assert repo['private'] is True and repo['owner']['login']=='GiaDiGr'
 record={'account':'GiaDiGr','repo_url':repo['html_url'],'visibility':'PRIVATE','created':created,'source_pushed':False}
(R/'docs/asthral/github-repository.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps(record))