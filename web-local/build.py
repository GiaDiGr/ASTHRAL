"""Reproducible static build. Only explicitly selected code, evidence and synthetic fixtures."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import base64
import re
import json
import shutil
import sqlite3
import sys
import ssl
import zipfile
import httpx
import os

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
OUT=Path(os.environ.get('ASTHRAL_BUILD_OUTPUT', str(ROOT/'web-local/build-output-unified-20261115b'))).resolve()
VENDOR=ROOT/'web-local/vendor'
VERSION='0.29.3'
BASE=f'https://cdn.jsdelivr.net/pyodide/v{VERSION}/full/'
PIN='pyodide-manifest.json'
MODULES=['__init__.py','clinical_engine.py','clinical_models.py','clinical_knowledge.py','clinical_logic.py',
         'clinical_differential.py','clinical_simulator.py','models.py','store.py','security.py',
         'management.py','knowledge_v08.py','retrieval_bm25.py','mission_context.py','algorithms.py','quality.py','monitoring_models.py']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def copy_public_source(source, destination):
    # Interpreter caches depend on the build machine and are not browser assets.
    shutil.copytree(source,destination,dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo','browser_bridge.py','browser_monitoring.py'))

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
    from copy import deepcopy
    originals=list(output[:36])
    for row in originals:
        for variant in ('EMPTY','WRONG_UNIT','INVALID_QUALITY','FUTURE','CONTRADICTORY'):
            snapshot=deepcopy(row['snapshot']);obs=snapshot['observations']
            if variant=='EMPTY':obs.clear()
            elif not obs:continue
            elif variant=='WRONG_UNIT':
                for o in obs:
                    if type(o['value']) in (int,float):o['unit']='UNSUPPORTED_UNIT';break
                else:continue
            elif variant=='INVALID_QUALITY':
                for o in obs:o['quality']='INVALID'
            elif variant=='FUTURE':
                for o in obs:o['timestamp']='2099-01-01T00:00:00Z'
            elif variant=='CONTRADICTORY':
                original=obs[0];other=deepcopy(original);other['id']='contradiction-'+other['id']
                other['value']=not original['value'] if type(original['value']) is bool else original['value']+1 if type(original['value']) in (int,float) else 'CONTRADICTORY'
                obs.append(other)
            snapshot['request']['observations']=deepcopy(obs)
            output.append({'id':row['id']+'-'+variant,'snapshot':snapshot,'expected':service.compute(snapshot),'origin':'EXPANDED_REFERENCE_ADVERSARIAL_INPUT'})
    store.close()
    return output

def main():
    voice=ROOT/'web-local/src/vosk.js'
    if not voice.exists():raise ValueError('VOICE_PREPARATION_REQUIRED: run prepare_voice.py')
    embedded=re.search(r"createBase64WorkerFactory\('([A-Za-z0-9+/=]+)'",voice.read_text(encoding='utf8'))
    if not embedded:raise ValueError('VOICE_WORKER_LAYOUT_CHANGED')
    worker=base64.b64decode(embedded[1]).decode()
    if re.search(r'new\s+Function\s*\(|new_\s*\(\s*Function|\beval\s*\(',worker):raise ValueError('STALE_UNSAFE_VOICE_ARTIFACT: rerun prepare_voice.py')
    if not all('// END '+name in worker for name in ('createNamedFunction','craftInvokerFunction','__emval_get_method_caller')):raise ValueError('VOICE_CSP_PATCH_MISSING')
    if OUT.exists() and any(OUT.iterdir()):
        raise ValueError('BUILD_OUTPUT_ALREADY_EXISTS: preserve prior output and select a new isolated build directory')
    OUT.mkdir(exist_ok=True)
    selected=get_runtime()
    copy_public_source(ROOT/'web-local/src',OUT)
    shutil.copytree(ROOT/'docs/asthral/science',OUT/'research',dirs_exist_ok=True)
    (OUT/'runtime').mkdir(exist_ok=True)
    runtime_lock=json.loads((VENDOR/'pyodide-lock.json').read_bytes())
    runtime_files=['pyodide.js','pyodide.asm.js','pyodide.asm.wasm','python_stdlib.zip','pyodide-lock.json']+[runtime_lock['packages'][key]['file_name'] for key in selected]
    for name in runtime_files:shutil.copyfile(VENDOR/name,OUT/'runtime'/name)
    for name in ['WEBLLM_LICENSE.txt','TRANSFORMERS_LICENSE.txt','THIRD_PARTY_NOTICES.md']:
        shutil.copyfile(ROOT/'web-local'/name,OUT/name)
    with zipfile.ZipFile(OUT/'engine.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for module in sorted(source.name for source in (ROOT/'engine/vigile').glob('*.py')):
            source=ROOT/'engine/vigile'/module
            archive.writestr('vigile/'+module,source.read_bytes())
        for source in sorted((ROOT/'engine/vigile/clinical_knowledge').glob('*.json')):
            archive.writestr('vigile/clinical_knowledge/'+source.name,source.read_bytes())
        from vigile.knowledge_v08 import SOURCES
        for name,authority,version in SOURCES:
            source=ROOT/name
            if source.exists():archive.writestr(name,source.read_bytes())
        import ast
        voice_source=(ROOT/'engine/vigile/health_voice.py').read_text(encoding='utf8')
        tree=ast.parse(voice_source)
        parser_parts=[ast.get_source_segment(voice_source,node) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('parse','number') or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('PATTERNS','DIGITS','TENS') for t in node.targets)]
        archive.writestr('health_voice_parser.py','import re\n'+'\n\n'.join(parser_parts))
        conversation=(ROOT/'engine/vigile/conversational.py').read_text(encoding='utf8')
        parsed=ast.parse(conversation)
        nodes=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name=='validate_generated' or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('SYSTEM','SCHEMA','UNSAFE','MODES') for t in node.targets) or isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='SYSTEM']
        parts=[ast.get_source_segment(conversation,node) for node in nodes]
        evidence=(ROOT/'engine/vigile/local_assistant.py').read_text(encoding='utf8')
        evidence_node=next(node for node in ast.parse(evidence).body if isinstance(node,ast.FunctionDef) and node.name=='evidence_blocks')
        helper='import re,json\n'+'\n\n'.join(parts)+'\n'+ast.get_source_segment(evidence,evidence_node)
        archive.writestr('browser_assistant_reference.py',helper)
        scope={};exec('import re\n'+'\n\n'.join(ast.get_source_segment(conversation,node) for node in nodes if not isinstance(node,ast.FunctionDef)),scope)
        (OUT/'assistant-config.json').write_text(json.dumps({'system':scope['SYSTEM'],'schema':scope['SCHEMA'],'max_tokens':scope['MODES']['FULL']['max_tokens']}),encoding='utf8')
        archive.writestr('browser_monitoring.py',(ROOT/'web-local/src/browser_monitoring.py').read_bytes())
        manifest=json.loads((ROOT/'ASTHRAL_CORPUS_SHA256.json').read_bytes())
        archive.writestr('ASTHRAL_CORPUS_SHA256.json',(ROOT/'ASTHRAL_CORPUS_SHA256.json').read_bytes())
        for item in manifest:archive.writestr(item['path'],(ROOT/item['path']).read_bytes())
        archive.writestr('browser_bridge.py',(ROOT/'web-local/src/browser_bridge.py').read_bytes())
        # Nutrition estimates are recomputed by the Python worker from this verified offline subset.
        for name in ('foods.json','foods.json.sha256','foods-v1.json','foods-v1.json.sha256'):
            archive.write(ROOT/'web-local/src/nutrition'/name,'web-local/src/nutrition/'+name)
    monitoring_fixture=json.loads((ROOT/'web-local/tests/fixtures/monitor-native-oracle.json').read_bytes())
    (OUT/'monitor-fixture.json').write_text(json.dumps({'steps':monitoring_fixture['steps'],'source':'FROZEN_SYNTHETIC_INPUTS_ONLY_NO_EXPECTED_OUTPUTS'}),encoding='utf8')
    cases=fixtures()
    for case in cases:
        case['snapshot_json']=json.dumps(case['snapshot'],ensure_ascii=False)
        case['expected_json']=json.dumps(case['expected'],ensure_ascii=False)
    (OUT/'demo-scenarios.json').write_text(json.dumps([{'id':row['id'],'snapshot':{key:row['snapshot'][key] for key in ('request','mission','observations')}} for row in cases[:36]],ensure_ascii=False),encoding='utf8')
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
    manifest=OUT/'.source-corpus-manifest.json'
    build(ROOT,manifest,sources=[source for source in SOURCES if (ROOT/source[0]).exists()])
    corpus=json.loads(manifest.read_bytes())
    manifest.unlink()
    (OUT/'knowledge').mkdir(exist_ok=True)
    for document in corpus['documents']:
        (OUT/'knowledge'/(document['sha256']+'.txt')).write_bytes((ROOT/document['document']).read_bytes())
    (OUT/'corpus.json').write_text(json.dumps(corpus),encoding='utf8')
    manifest=[]
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name not in ('assets.json','sw.js','browser_bridge.py','_headers'):
            raw=path.read_bytes()
            if len(raw)>25*1024*1024:raise ValueError('PAGES_ASSET_LIMIT '+str(path))
            relative=path.relative_to(OUT).as_posix()
            optional=relative.startswith(('voice-assets/','embedding-runtime/','test-audio/','motion-runtime/','test-motion/')) or relative in ('vosk.js','webllm.js','parity-cases.json')
            manifest.append({'path':relative,'size':len(raw),'sha256':sha(raw),'optional':optional})
    (OUT/'assets.json').write_text(json.dumps({'version':'asthral-browser-1','files':manifest},indent=2))
    service_worker=(ROOT/'web-local/src/sw.js').read_text(encoding='utf8').replace('__BUILD_ID__',sha((OUT/'assets.json').read_bytes())[:16]).replace('__ASSET_MANIFEST_SHA__',sha((OUT/'assets.json').read_bytes()))
    (OUT/'sw.js').write_text(service_worker,encoding='utf8')
    print(json.dumps({'cases':len(cases),'packages':sorted(selected),'files':len(manifest),
                      'bytes':sum(row['size'] for row in manifest),'clinical_modules':'BYTE_IDENTICAL'}))

if __name__=='__main__':main()
