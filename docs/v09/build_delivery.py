from pathlib import Path
import sys,json,hashlib,zipfile,xml.etree.ElementTree as ET,csv,collections,importlib.metadata as md
ROOT=Path(r'C:\Users\Gianni\Desktop\Vigile');sys.path.insert(0,str(ROOT/'engine'));docs=ROOT/'docs/v09'
from vigile.registry import Registry
from vigile.clinical_knowledge import ClinicalKnowledge
from vigile.service import Engine
from vigile.store import Store
original=json.loads((ROOT/'MANIFIESTO_SHA256.json').read_text(encoding='utf-8-sig'));assert all(hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in original)
clinical=json.loads((ROOT/'engine/vigile/clinical_knowledge/manifest.json').read_text());assert all(hashlib.sha256((ROOT/'engine/vigile/clinical_knowledge'/n).read_bytes()).hexdigest()==h for n,h in clinical['files'].items())
reserved=(docs/'reserved-bank.json').read_bytes();assert hashlib.sha256(reserved).hexdigest()==(docs/'reserved-bank.sha256').read_text().strip()
suite=ET.parse(docs/'tests-release.xml').getroot().find('testsuite');summary={k:int(suite.attrib[k]) for k in ('tests','failures','errors','skipped')};summary.update(seconds=float(suite.attrib['time']),added=23,warning='Starlette/httpx deprecation',clinical_validation=False);assert summary['failures']==summary['errors']==0
(docs/'test-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
s=Store(':memory:')
try:implementation=Engine(Registry(ROOT),s).implementation_hash
finally:s.close()
assert implementation==json.loads((ROOT/'engine/data/portal-v090-release/monitoring-report.json').read_text())['implementation_hash']
with zipfile.ZipFile(docs/'before-v09.zip') as z:prior={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
files=[]
for folder in ('engine/vigile','engine/tests'):
 for f in (ROOT/folder).rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:
   n=f.relative_to(ROOT).as_posix();h=hashlib.sha256(f.read_bytes()).hexdigest();files.append({'path':n,'sha256':h,'change':'ADDED' if n not in prior else 'UNCHANGED' if h==prior[n] else 'MODIFIED'})
f=ROOT/'engine/pyproject.toml';files.append({'path':'engine/pyproject.toml','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'change':'MODIFIED'})
manifest={'version':'0.9.0','implementation_hash':implementation,'knowledge_hash':ClinicalKnowledge().hash,'original_scientific_files_verified':len(original),'original_clinical_files_verified':len(clinical['files']),'reserved_cases_not_executed':12,'reserved_sha256':hashlib.sha256(reserved).hexdigest(),'files':files,'dependencies':{p:md.version(p) for p in ('fastapi','pydantic','uvicorn','httpx','pytest')},'clinical_validation':False}
(docs/'change-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
before=json.loads((docs/'audit-before.json').read_text(encoding='utf8'));after=json.loads((docs/'audit-final-full.json').read_text(encoding='utf8'))
ids=['audit-01','audit-03','audit-07','audit-08','audit-13','audit-14','audit-16','audit-23','audit-25','audit-30','audit-33','audit-36'];review=[]
for id in ids:review.append({'case_id':id,'before':next(r for r in before['records'] if r['case']['id']==id),'after':next(r for r in after['records'] if r['case']['id']==id),'review_status':'NOT_REVIEWED_BY_INDEPENDENT_HUMAN'})
(docs/'human-review-sample.json').write_text(json.dumps({'selection':'Purposive 12-case sample covering known failure modes; not random, not prevalence estimate','cases':review},indent=2,ensure_ascii=False),encoding='utf8')
with (docs/'human-review-rubric.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['case_id','reviewer','date','claim_supported','citation_entails_claim','negation_correct','conditions_omitted','subject_mission_correct','diagnosis_vs_authorization_separate','harmful_claim','comments'])
 for id in ids:w.writerow([id]+['']*10)
metrics={}
for n in ['audit-before.json','audit-final-full.json','audit-after-low.json','audit-after-critical.json']:
 d=json.loads((docs/n).read_text(encoding='utf8'));metrics[n]={'summary':d['summary'],'statuses':dict(collections.Counter(r.get('response',{}).get('status',r.get('error_type')) for r in d['records'])),'reader_retries':d.get('reader_transport_retries','NOT_INSTRUMENTED')}
(docs/'audit-summary.json').write_text(json.dumps(metrics,indent=2),encoding='utf8')
print(json.dumps({'suite':summary,'implementation_hash':implementation,'original_science':len(original),'original_clinical':len(clinical['files']),'changed':[r['path'] for r in files if r['change']!='UNCHANGED']},indent=2))
