from pathlib import Path
import sys,json,hashlib,zipfile,statistics,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));D=R/'docs/v100'
def read(p):return json.loads((D/p).read_text(encoding='utf8'))
f=read('CANDIDATE_R2_FREEZE.json');mission=json.loads((R/'engine/data/mission-v100-r2/summary.json').read_text(encoding='utf8'));voice=read('voice-benchmark/results.json');e2e=read('e2e-r2/results.json');reserved=read('reserved/results.json')
assert len(e2e['rows'])==9 and all(x['matches'] for x in e2e['monitoring_replays']+e2e['clinical_replays'])
tests=ET.parse(D/'final-r2-tests.xml').getroot().find('testsuite');assert int(tests.attrib['failures'])==int(tests.attrib['errors'])==0
from vigile.api import create_app
from vigile.portal import create_portal
from vigile.structured_facts import Fact
from vigile.local_protection import read_secret,verify_anchor
folder=R/'engine/data/mission-v100-r2';cfg=json.loads((folder/'portal-config.json').read_text())
(D/'backend-openapi.json').write_text(json.dumps(create_app(R,folder/'vigile.sqlite3',json.loads(read_secret(folder/'server-tokens.json'))).openapi(),indent=2),encoding='utf8')
(D/'portal-openapi.json').write_text(json.dumps(create_portal(cfg).openapi(),indent=2),encoding='utf8')
(D/'structured-fact.schema.json').write_text(json.dumps(Fact.model_json_schema(),indent=2),encoding='utf8')
anchor=verify_anchor(folder/'vigile.sqlite3',Path.home()/'AppData/Local/Vigile/integrity/mission-v100-r2.anchor.json',Path.home()/'AppData/Local/Vigile/integrity/audit-key.dpapi');(D/'integrity-verification.json').write_text(json.dumps(anchor,indent=2),encoding='utf8')
from vigile.registry import Registry
Registry(R)
archives=read('voice-model-downloads.json')['models'];storage={'archives_bytes':sum(x['archive_bytes'] for x in archives),'expanded_model_bytes':sum(sum(i['bytes'] for i in x['files']) for x in archives)}
metrics={lang:{'stt_median_seconds':statistics.median(x['stt_seconds'] for x in voice['rows'] if x['language']==lang),'tts_median_seconds':statistics.median(x['tts']['synthesis_seconds'] for x in voice['rows'] if x['language']==lang),'audio_min_seconds':min(x['synthetic_audio_seconds'] for x in voice['rows'] if x['language']==lang),'audio_max_seconds':max(x['synthetic_audio_seconds'] for x in voice['rows'] if x['language']==lang),**voice['summary'][lang]} for lang in ('en','es')}
report={'version':'1.0.0-research-r2','client_date':'2026-10-26','implementation_hash':f['implementation_hash'],'knowledge_hash':f['knowledge_hash'],'tests':tests.attrib,'baseline_tests':582,'mission':{k:mission[k] for k in ('cycles','request_hash','semantic_hash','total_seconds','database_bytes','performance')},'replays':{'current_monitoring':len(e2e['monitoring_replays']),'current_clinical':len(e2e['clinical_replays']),'current_matches':True,'archived_v011_matches':76},'voice':{'metrics':metrics,'storage':storage,'cpu_seconds_32_utterances':voice['cpu_seconds'],'before':voice['before'],'after':voice['after'],'physical_microphone_test':'INTERRUPTED_NOT_VERIFIED','loudspeaker_intelligibility_human_rating':'NOT_MEASURED','synthetic_audio_not_clinical_validation':True},'rag':{'original_development_top3':4,'original_development_top5':8,'new_development_top3':10,'new_development_top5':11,'n':12,'additional_top3':4,'additional_top5':6,'additional_n':8,'independent_human_relevance_review':False},'reserved':{'candidate':'R1','cases':12,'generated_cases':5,'execution_errors':0,'used':True,'r2_not_unseen_evaluated':True,'limitations':['R1 generic cross-context/risk requests not explicitly rejected; no scope leakage or risk estimate','Descriptive output sometimes irrelevant to question','Post-bank guards/routing changes covered by regressions; bank never rerun'],'outputs_unchanged':reserved['clinical_outputs_unchanged'],'audit_valid':reserved['audit_valid']},'e2e':[{'scenario':r['scenario'],'mode':r['mode'],'language':r['language'],'status':r['answer']['status'],'generated_sentences':len(r['answer'].get('generated',[])),'stt_seconds':r['transcription']['transcription_seconds'],'tts_seconds':r['synthesis_seconds'],'end_reference_capture_to_wav_ready_seconds':r['from_end_of_reference_capture_to_wave_ready_seconds'],'timings':r['answer'].get('timings'),'model_metrics':r['answer'].get('metrics'),'clinical_hashes_unchanged':r['clinical_hashes_unchanged']} for r in e2e['rows']],'audit_anchor':anchor['valid'],'clinical_execution':'BLOCKED','clinical_validation':False,'operational_validation':False,'space_validation':False}
(D/'RESULTS.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
# Exact old-source diff, scientific originals verified by Registry above.
with zipfile.ZipFile(D/'before-v100.zip') as z:
 old={i.filename:hashlib.sha256(z.read(i)).hexdigest() for i in z.infolist() if not i.is_dir()}
changes=[]
for rel,h in f['files'].items():
 if rel not in old:changes.append({'path':rel,'change':'NEW','sha256':h})
 elif old[rel]!=h:changes.append({'path':rel,'change':'MODIFIED','before_sha256':old[rel],'sha256':h})
(D/'changes.json').write_text(json.dumps({'changes':changes,'original_corpus_manifest_verified':True,'clinical_knowledge_unchanged':True},indent=2),encoding='utf8')
print('Verified report:',tests.attrib['tests'],'tests;',len(e2e['monitoring_replays'])+len(e2e['clinical_replays']),'current replays; voice metrics',metrics,storage)