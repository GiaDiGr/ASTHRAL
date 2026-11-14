"""Example dashboard API consumer, no UI and no modifications."""
import argparse,json,sys
from pathlib import Path
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vigile.adapters import LocalClient
parser=argparse.ArgumentParser(); parser.add_argument('--token-file',type=Path,required=True)
parser.add_argument('--url',default='http://127.0.0.1:8765'); args=parser.parse_args()
client=LocalClient(args.url,args.token_file.read_text(encoding='utf-8').strip())
query=urlencode({'subject_id':'sim-crew','mission_id':'sim-mission'})
try:
    profiles=client.call('GET','/profiles?mission_id=sim-mission')
    measurements=client.call('GET','/measurements?'+query)
    baselines=client.call('GET','/baselines?'+query); trends=client.call('GET','/trends?'+query)
    episodes=client.call('GET','/episodes?'+query)
    findings=client.call('GET','/findings?'+query)
    first=next(f for f in findings if f['result']=='INCONCLUSIVE')
    assert client.call('GET','/findings/'+first['id']+'/explanation')['verified']
    print(json.dumps({'profiles':len(profiles),'measurements':len(measurements),'baselines':len(baselines),
        'trends':len(trends),'episodes':len(episodes),'findings':len(findings),'replay_after_http_restart':True},indent=2))
finally: client.close()
