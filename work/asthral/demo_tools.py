from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'engine/vigile/knowledge_v08.py';s=p.read_text(encoding='utf8').replace('def build(root,output):','def build(root,output,sources=None):').replace('for name,authority,version in SOURCES:\n        p=root/name','for name,authority,version in (SOURCES if sources is None else sources):\n        p=root/name');p.write_text(s,encoding='utf8')
# Portable setup regenerates public local knowledge, never clinical records or credentials.
(R/'engine/tools/setup_asthral.py').write_text('''from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.knowledge_v08 import build,SOURCES
if __name__=='__main__':
 result=build(ROOT,ROOT/'engine/local_ai/library-asthral.json',sources=[SOURCES[0]])
 print(json.dumps({'product':'ASTHRAL','local_knowledge_blocks':result['blocks'],'new_network_requests':0,'clinical_knowledge_modified':False}))
''',encoding='utf8')
(R/'engine/tools/demo_asthral.py').write_text('''"""Fresh synthetic mission; optional public retrieval requires explicit local enablement."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','serve','verify']);p.add_argument('--output',required=True,type=Path);p.add_argument('--enable-online',action='store_true');p.add_argument('--report',type=Path);a=p.parse_args();folder=a.output.resolve()
 if a.command=='prepare':
  from vigile.knowledge_v08 import build,SOURCES
  from vigile.mission_demo import prepare
  build(ROOT,ROOT/'engine/local_ai/library-asthral.json',sources=[SOURCES[0]])
  summary=prepare(folder,seed=42)
  config=json.loads((folder/'portal-config.json').read_text(encoding='utf8'));config.update(backend_url='http://127.0.0.1:8921',structured_explanations=True,voice_enabled=True,library_manifest=str(ROOT/'engine/local_ai/library-asthral.json'),online_retrieval={'enabled':a.enable_online,'providers':['pubmed'],'timeout_seconds':4,'queries_per_minute':2,'retries':1},public_science_cache=str(folder/'public-science-cache'))
  (folder/'portal-config.json').write_text(json.dumps(config,indent=2),encoding='utf8')
  print(json.dumps({'product':'ASTHRAL','cycles':summary['cycles'],'synthetic':True,'semantic_hash':summary['semantic_hash'],'online_enabled_by_explicit_setup':a.enable_online,'clinical_execution':'BLOCKED'}))
 elif a.command=='serve':
  from demo_management_v101 import serve
  print('ASTHRAL: Offline-First Astronaut Health Monitoring and Medical Decision Support',flush=True);serve(folder,8921,8922)
 else:
  from demo_astronaut_v101 import verify
  if not a.report:p.error('--report must name a new verification report')
  verify(folder,a.report)
if __name__=='__main__':main()
''',encoding='utf8')
# Shared supervisor label is current; old scripts/interfaces stay compatible.
p=R/'engine/tools/demo_management_v101.py';s=p.read_text(encoding='utf8').replace('VIGILE v1.0.1 synthetic demo:','ASTHRAL synthetic demo:');p.write_text(s,encoding='utf8')
print('Portable English knowledge setup and ASTHRAL mission commands ready')