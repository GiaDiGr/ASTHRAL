from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.knowledge_v08 import build,SOURCES
if __name__=='__main__':
 result=build(ROOT,ROOT/'engine/local_ai/library-asthral.json',sources=[SOURCES[0]])
 legacy=ROOT/'engine/local_ai/library-v080.json'
 if not legacy.exists():legacy.write_bytes((ROOT/'engine/local_ai/library-asthral.json').read_bytes())
 print(json.dumps({'product':'ASTHRAL','local_knowledge_blocks':result['blocks'],'new_network_requests':0,'clinical_knowledge_modified':False}))
