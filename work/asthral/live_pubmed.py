from pathlib import Path
import sys,json,time
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.hybrid_retrieval import HybridRetrieval
h=HybridRetrieval({'enabled':True,'timeout_seconds':10,'retries':0},lambda:'FULL',R/'work/asthral/live-public-cache')
a=h.retrieve('hyperglycemic_consensus');b=h.retrieve('hyperglycemic_consensus');report={'live_public_request':True,'private_context_supplied':False,'first':a,'second':b,'transport_calls':h.transport.calls,'energy_measured':False}
(R/'docs/asthral/pubmed-live.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'status':a['status'],'reason':a['reason'],'documents':len(a['documents']),'delivery':a['delivery'],'calls':h.transport.calls,'cache_second':b['delivery']}))