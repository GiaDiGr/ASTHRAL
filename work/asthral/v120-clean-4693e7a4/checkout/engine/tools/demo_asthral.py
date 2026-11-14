"""Fresh synthetic mission; optional public retrieval requires explicit local enablement."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
def personal(folder, config, password_pair):
 from hashlib import sha256
 from secrets import token_urlsafe
 from vigile.local_protection import protect_secret
 from vigile.personal_accounts import Accounts
 from vigile.mission_demo import SUBJECTS,MID
 database=folder/'personal.sqlite3'
 accounts=Accounts(database)
 mapping={}
 for index,(subject,password) in enumerate(zip(SUBJECTS,password_pair)):
  username=('crew-alpha','crew-bravo')[index]
  token=token_urlsafe(32)
  accounts.create(username,password,subject,MID,token)
  mapping['sha256:'+sha256(token.encode()).hexdigest()]={
      'id':username+'-reader','role':'reader','subject_ids':[subject],'mission_ids':[MID]}
 protect_secret(json.dumps(mapping),folder/'personal-server-tokens.json')
 # Replace only the new demo's broad credential map.
 (folder/'personal-server-tokens.json').replace(folder/'server-tokens.json')
 config['accounts_db']=str(database)
 for name in ('access_code_file','reader_token_file'):
  Path(config.pop(name)).unlink()
 (folder/'acquisition-token.txt').unlink()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','serve','verify']);p.add_argument('--output',required=True,type=Path);p.add_argument('--enable-online',action='store_true');p.add_argument('--report',type=Path);p.add_argument('--personal',action='store_true');p.add_argument('--backend-port',type=int,default=8921);p.add_argument('--portal-port',type=int,default=8922);p.add_argument('--vector-digest');p.add_argument('--enable-hybrid',action='store_true');a=p.parse_args();folder=a.output.resolve()
 if a.command=='prepare':
  passwords=[]
  if a.personal:
   from getpass import getpass
   for name in ('crew-alpha','crew-bravo'):
    password=getpass(f'Synthetic demo password for {name}: ')
    if not 14<=len(password)<=256 or password!=getpass('Repeat password: '):
     p.error('Passwords must match and contain 14 to 256 characters.')
    passwords.append(password)
  from vigile.knowledge_v08 import build,SOURCES
  from vigile.mission_demo import prepare
  manifest=folder/'library.json' if a.personal else ROOT/'engine/local_ai/library-asthral.json'
  summary=prepare(folder,seed=42)
  build(ROOT,manifest,sources=[SOURCES[0]])
  config=json.loads((folder/'portal-config.json').read_text(encoding='utf8'));config.update(backend_url=f'http://127.0.0.1:{a.backend_port}',structured_explanations=True,voice_enabled=True,library_manifest=str(manifest),online_retrieval={'enabled':a.enable_online,'providers':['pubmed'],'timeout_seconds':4,'queries_per_minute':2,'retries':1},public_science_cache=str(folder/'public-science-cache'))
  if a.personal:personal(folder,config,passwords)
  if a.vector_digest:
   from vigile.vector_library import MiniLM,build as build_index
   url=config['model_url'];index=folder/'vectors.db'
   build_index(manifest,index,MiniLM(url,a.vector_digest))
   config['vector_retrieval']={'url':url,'index':str(index),'digest':a.vector_digest,'hybrid_enabled':a.enable_hybrid}
  (folder/'portal-config.json').write_text(json.dumps(config,indent=2),encoding='utf8')
  print(json.dumps({'product':'ASTHRAL','cycles':summary['cycles'],'synthetic':True,'semantic_hash':summary['semantic_hash'],'online_enabled_by_explicit_setup':a.enable_online,'clinical_execution':'BLOCKED'}))
 elif a.command=='serve':
  from demo_management_v101 import serve
  print('ASTHRAL: Offline-First Astronaut Health Monitoring and Medical Decision Support',flush=True);serve(folder,a.backend_port,a.portal_port)
 else:
  from demo_astronaut_v101 import verify
  if not a.report:p.error('--report must name a new verification report')
  verify(folder,a.report)
if __name__=='__main__':main()
