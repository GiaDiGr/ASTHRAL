"""Reproducible static build. Only explicitly selected code, evidence and synthetic fixtures."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import shutil
import sqlite3
import sys
import ssl
import zipfile
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
OUT=ROOT/'web-local/dist'
VENDOR=ROOT/'web-local/vendor'
VERSION='0.29.3'
BASE=f'https://cdn.jsdelivr.net/pyodide/v{VERSION}/full/'
PIN='pyodide-manifest.json'
MODULES=['__init__.py','clinical_engine.py','clinical_models.py','clinical_knowledge.py','clinical_logic.py',
         'clinical_differential.py','clinical_simulator.py','models.py','store.py','security.py',
         'management.py','knowledge_v08.py','retrieval_bm25.py','mission_context.py','algorithms.py','quality.py','monitoring_models.py']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def get_runtime():
    VENDOR.mkdir(exist_ok=True)
    with httpx.Client(verify=ssl.create_default_context(),trust_env=False,timeout=90,follow_redirects=True) as client:
        def obtain(name,expected=None):
            target=VENDOR/name
            if not target.exists():
                response=client.get(BASE+name);response.raise_for_status();raw=response.content
                if expected and sha(raw)!=expected:raise ValueError('OFFICIAL_PACKAGE_HASH_MISMATCH '+name)
                target.write_bytes(raw)
            if expected and sha(target.read_bytes())!=expected:raise ValueError('CACHED_PACKAGE_HASH_MISMATCH '+name)
        runtime_lock=json.loads((ROOT/'web-local/runtime-lock.json').read_bytes())['pyodide']
        for name,expected in runtime_lock['files'].items():
            obtain(name,expected)
        lock=json.loads((VENDOR/'pyodide-lock.json').read_bytes())
        selected=set()
        def dependency(name):
            key=name.replace('_','-')
            if key in selected:return
            selected.add(key)
            package=lock['packages'][key]
            for item in package['depends']:dependency(item)
            obtain(package['file_name'],package['sha256'])
        for name in ['pydantic','sqlite3']:dependency(name)
    return selected

def fixtures():
    from vigile.clinical_engine import ClinicalService
    from vigile.clinical_knowledge import ClinicalKnowledge
    from vigile.clinical_simulator import report_case,observation,AS_OF
    from vigile.clinical_models import ClinicalRequest
    from vigile.store import Store
    store=Store(':memory:')
    mission={'id':'clinical-earth','phase':'IN_MISSION','gravity':'EARTH','environment':'HABITABLE_CABIN','mode':'NOMINAL','synthetic':True}
    store.put('mission',mission['id'],mission)
    store.put('profile','clinical-crew',{'id':'clinical-crew','mission_id':'clinical-earth','synthetic':True})
    service=ClinicalService(SimpleNamespace(store=store))
    output=[]
    originals=json.loads((ROOT/'engine/vigile/clinical_knowledge/synthetic_cases.json').read_bytes())['cases']
    for case in originals:
        request=report_case(case)
        snapshot=service.snapshot(request)
        output.append({'id':case['id'],'snapshot':snapshot,'expected':service.compute(snapshot),'origin':'ORIGINAL_SYNTHETIC_REPORT'})
    from datetime import timedelta
    for i,value in enumerate([None,54,53.9,69.9,70,180]):
        observations=[observation('known_diabetes',True)]
        if value is not None:observations.append(observation('plasma_glucose_mg_dl',value))
        request=ClinicalRequest(subject_id='clinical-crew',mission_id='clinical-earth',condition_id='HYPOGLYCEMIA',
                                population='NONPREGNANT_ADULT',age_years=35,as_of=AS_OF,
                                window_start=AS_OF-timedelta(days=7),observations=observations)
        snapshot=service.snapshot(request)
        output.append({'id':f'HYPO-WEB-{i}','snapshot':snapshot,'expected':service.compute(snapshot),'origin':'SYNTHETIC_BOUNDARY_INPUT'})
    for row in json.loads((ROOT/'web-local/tests/fixtures/mission-inputs.json').read_bytes()):
        snapshot=row['snapshot']
        assert snapshot['profile']['synthetic'] and snapshot['mission']['synthetic']
        output.append({'id':row['id'],'snapshot':snapshot,'expected':service.compute(snapshot),
                       'origin':'FROZEN_SYNTHETIC_MISSION_INPUT'})
    store.close()
    return output

def main():
    if OUT.exists():
        if OUT.resolve()!=ROOT.resolve()/'web-local'/'dist':raise ValueError('UNSAFE_BUILD_TARGET')
        shutil.rmtree(OUT)
    OUT.mkdir(exist_ok=True)
    selected=get_runtime()
    shutil.copytree(ROOT/'web-local/src',OUT,dirs_exist_ok=True,ignore=shutil.ignore_patterns('browser_bridge.py'))
    shutil.copytree(VENDOR,OUT/'runtime',dirs_exist_ok=True)
    for name in ['WEBLLM_LICENSE.txt','TRANSFORMERS_LICENSE.txt','THIRD_PARTY_NOTICES.md']:
        shutil.copyfile(ROOT/'web-local'/name,OUT/name)
    with zipfile.ZipFile(OUT/'engine.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for module in MODULES:
            source=ROOT/'engine/vigile'/module
            archive.writestr('vigile/'+module,source.read_bytes())
        for source in sorted((ROOT/'engine/vigile/clinical_knowledge').glob('*.json')):
            archive.writestr('vigile/clinical_knowledge/'+source.name,source.read_bytes())
        archive.writestr('docs/knowledge/ASTHRAL_LOCAL_KNOWLEDGE.md',(ROOT/'docs/knowledge/ASTHRAL_LOCAL_KNOWLEDGE.md').read_bytes())
        import ast
        voice_source=(ROOT/'engine/vigile/health_voice.py').read_text(encoding='utf8')
        tree=ast.parse(voice_source)
        parser_parts=[ast.get_source_segment(voice_source,node) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('parse','number') or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('PATTERNS','DIGITS','TENS') for t in node.targets)]
        archive.writestr('health_voice_parser.py','import re\n'+'\n\n'.join(parser_parts))
        archive.writestr('browser_bridge.py',(ROOT/'web-local/src/browser_bridge.py').read_bytes())
    cases=fixtures()
    for case in cases:
        case['snapshot_json']=json.dumps(case['snapshot'],ensure_ascii=False)
        case['expected_json']=json.dumps(case['expected'],ensure_ascii=False)
    (OUT/'parity-cases.json').write_text(json.dumps(cases,ensure_ascii=False),encoding='utf8')
    statistics=[]
    from vigile.models import Measurement
    from vigile.algorithms import baseline,trends
    for record in json.loads((ROOT/'web-local/tests/fixtures/statistics-inputs.json').read_bytes()):
        request=record['request'];kind=record['kind']
        measurements=[Measurement.model_validate(row['measurement']) for row in record['snapshots']]
        if kind=='baseline':result=baseline(measurements,request['minimum_observations'])
        else:result=trends(measurements,request['ewma_lambda'],request['cusum_target'],request['cusum_allowance'],request['ewma_initial'],request['cusum_decision_limit'])
        statistics.append({**record,'expected_json':json.dumps(result)})
    (OUT/'statistics-cases.json').write_text(json.dumps(statistics),encoding='utf8')
    from vigile.knowledge_v08 import build,SOURCES
    manifest=ROOT/'work/browser-local/corpus.json'
    build(ROOT,manifest,sources=[SOURCES[0]])
    corpus=json.loads(manifest.read_bytes())
    (OUT/'corpus.json').write_text(json.dumps(corpus),encoding='utf8')
    manifest=[]
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name not in ('assets.json','sw.js','browser_bridge.py','_headers'):
            raw=path.read_bytes()
            if len(raw)>25*1024*1024:raise ValueError('PAGES_ASSET_LIMIT '+str(path))
            relative=path.relative_to(OUT).as_posix()
            optional=relative.startswith(('voice-assets/','embedding-runtime/')) or relative in ('vosk.js','webllm.js')
            manifest.append({'path':relative,'size':len(raw),'sha256':sha(raw),'optional':optional})
    (OUT/'assets.json').write_text(json.dumps({'version':'asthral-browser-1','files':manifest},indent=2))
    service_worker=(ROOT/'web-local/src/sw.js').read_text(encoding='utf8').replace('__BUILD_ID__',sha((OUT/'assets.json').read_bytes())[:16])
    (OUT/'sw.js').write_text(service_worker,encoding='utf8')
    print(json.dumps({'cases':len(cases),'packages':sorted(selected),'files':len(manifest),
                      'bytes':sum(row['size'] for row in manifest),'clinical_modules':'BYTE_IDENTICAL'}))

if __name__=='__main__':main()
