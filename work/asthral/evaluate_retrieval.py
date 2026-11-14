from pathlib import Path
import json,hashlib,time,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));D=R/'docs/asthral'
from vigile.offline_library import OfflineLibrary
from vigile.hybrid_retrieval import HybridRetrieval,TOPICS
# Development and held-out scenarios are new; no previous reserved/blind bank is used.
dev=[{'id':'dev-001','question':'Explain spaceflight cardiovascular deconditioning literature.','topic':'cardiovascular'},{'id':'dev-002','question':'Show public research on sleep and fatigue.','topic':'sleep_fatigue'}]
held=[{'id':'held-001','question':'Which public references discuss heart performance during space missions?','topic':'cardiovascular','term':'cardiovascular'}, {'id':'held-002','question':'Find reference metadata about muscle and skeletal countermeasures.','topic':'muscle_bone','term':'muscle'}, {'id':'held-003','question':'What literature covers fatigue and sleep during spaceflight?','topic':'sleep_fatigue','term':'sleep'}, {'id':'held-004','question':'Show scientific reference metadata for space radiation research.','topic':'radiation','term':'radiation'}, {'id':'held-005','question':'Find the 2024 consensus bibliography on hyperglycemic crises.','topic':'hyperglycemic_consensus','term':'hyperglycemic'}]
(D/'retrieval-development.example.json').write_text(json.dumps({'synthetic':True,'split':'DEVELOPMENT','cases':dev},indent=2),encoding='utf8')
(D/'retrieval-heldout.example.json').write_text(json.dumps({'synthetic':True,'split':'NEW_FIXED_HELDOUT_NOT_PREVIOUS_RESERVED_BANK','cases':held},indent=2),encoding='utf8')
class Fixture:
 def __init__(self,topic):self.topic=topic;self.calls=0
 def get(self,utility,params,deadline,maximum):
  self.calls+=1
  if utility=='esearch.fcgi':return {'esearchresult':{'idlist':['99990001']}}
  return {'result':{'99990001':{'uid':'99990001','title':'Synthetic fixture only: '+TOPICS[self.topic]['query'],'fulljournalname':'Synthetic provider fixture, not an actual publication','pubdate':'2020','articleids':[]}}}
local=OfflineLibrary(R/'engine/local_ai/library-asthral.json');rows=[]
for case in held:
 start=time.perf_counter();blocks,issues=local.search(case['question'],2);local_ms=(time.perf_counter()-start)*1000
 fixture=Fixture(case['topic']);hybrid=HybridRetrieval({'enabled':True,'retries':0},lambda:'FULL',R/'work/asthral/benchmark-cache'/case['topic'],fixture);start=time.perf_counter();remote=hybrid.retrieve(case['topic']);hybrid_ms=(time.perf_counter()-start)*1000;cache=hybrid.retrieve(case['topic'])
 term=case['term'];local_hit=any(term in b['text'].lower() for b in blocks);remote_hit=any(term in b['title'].lower() for b in remote['documents'])
 rows.append({'id':case['id'],'local_blocks':len(blocks),'local_lexical_topic_hit':local_hit,'hybrid_lexical_topic_hit':local_hit or remote_hit,'remote_metadata_schema_and_canonical_citation_valid':all(d['url']=='https://pubmed.ncbi.nlm.nih.gov/'+d['pmid']+'/' and d['content_hash'] for d in remote['documents']),'local_latency_ms':local_ms,'mocked_online_latency_ms':hybrid_ms,'cache_delivery':cache['delivery'],'provider_requests':fixture.calls,'remote_review_status_preserved':all(d['review_status']=='NOT_CLINICALLY_REVIEWED' for d in remote['documents']),'model_invocations':0,'generated_clinical_claims':0})
report={'new_heldout_cases':5,'previous_reserved_bank_reused':False,'cases':rows,'local_hit_rate':sum(r['local_lexical_topic_hit'] for r in rows)/len(rows),'hybrid_hit_rate':sum(r['hybrid_lexical_topic_hit'] for r in rows)/len(rows),'scope':'Software lexical topic/citation evaluation using explicitly synthetic provider fixtures. Not independent clinical relevance review, real publication relevance, or free-generation validation. Live PubMed smoke is separate.','unsupported_claim_metric':'Zero generated clinical claims by construction; not proof of source truth.','energy_measured':False,'resources':'No model loaded by this evaluation; no claim of reduced electrical power.'}
(D/'retrieval-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'cases':5,'local_lexical_topic_hit_rate':report['local_hit_rate'],'hybrid_lexical_topic_hit_rate':report['hybrid_hit_rate'],'cache_hits':sum(r['cache_delivery']=='CACHE_NOT_LIVE' for r in rows),'model_calls':0}))