"""Example RAG consumer: only its reader token file, never write credentials."""
import argparse,json,sys
from pathlib import Path
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vigile.adapters import LocalClient
parser=argparse.ArgumentParser()
parser.add_argument('--token-file',type=Path,required=True)
parser.add_argument('--url',default='http://127.0.0.1:8765')
parser.add_argument('--subject',default='sim-crew'); parser.add_argument('--mission',default='sim-mission')
args=parser.parse_args()
client=LocalClient(args.url,args.token_file.read_text(encoding='utf-8').strip())
try:
    findings=client.call('GET','/rag/findings?'+urlencode({'subject_id':args.subject,'mission_id':args.mission}))
    blocked=[f for f in findings if f['result']=='INCONCLUSIVE']
    evidence=client.call('GET','/evidence/rules/VIGILE-ENV-002')
    assert evidence['clinical_activation']=='BLOCKED'
    assert all('bundle' not in f and 'subject_id' not in f for f in findings)
    print(json.dumps({'authorized_findings':len(findings),'inconclusive':len(blocked),
        'existing_reasons':[f['reason'] for f in blocked],'clinical_activation':evidence['clinical_activation']},indent=2))
finally: client.close()
