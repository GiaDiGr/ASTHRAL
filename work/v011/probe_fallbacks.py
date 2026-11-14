"""Bounded synthetic reproduction of the v0.10 sustained-load question.
Captures stages on a private adapter instance, without changing safety guards.
"""
from pathlib import Path
import sys,json,time,re,subprocess
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
import httpx
from vigile.local_protection import read_secret
from vigile.local_assistant import ReaderClient
from vigile.conversational import ConversationalInference
from vigile.longitudinal_assistant import answer_monitoring
from vigile.offline_library import OfflineLibrary

folder=ROOT/'engine/data/portal-v0100-integrated'
reader=ReaderClient('http://127.0.0.1:8895',read_secret(folder/'reader-token.txt'))
library=OfflineLibrary(ROOT/'engine/local_ai/library-v080.json')
report={'scope':'CONTROLLED_SYNTHETIC_FAILURE_DIAGNOSIS_NOT_LLM_AUDIT','question':'Explain recorded baseline values.','rows':[],'guards_modified':False}
destination=ROOT/'docs/v011/fallback-probes-v010.json'
try:
    with httpx.Client(base_url='http://127.0.0.1:8896',headers={'Origin':'http://127.0.0.1:8896'},trust_env=False,timeout=10) as portal:
        portal.post('/api/login',json={'code':read_secret(folder/'portal-access.txt')}).raise_for_status()
        try:
            status=portal.get('/api/status');status.raise_for_status()
            report['portal_status_probe']={'state':'OBSERVED','assistant_busy':status.json().get('assistant_busy')}
            if status.json().get('assistant_busy'):raise RuntimeError('EXISTING_ASSISTANT_BUSY_DO_NOT_INTERFERE')
        except httpx.HTTPError as exc:
            report['portal_status_probe']={'state':'FAILED_BEFORE_INFERENCE','error_type':type(exc).__name__,'cause':'NOT_ESTABLISHED'}
            net=subprocess.run(['netstat','-ano','-p','tcp'],capture_output=True,text=True,timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if any(':8891' in line and 'ESTABLISHED' in line for line in net.stdout.splitlines()):
                destination.write_text(json.dumps(report,indent=2),encoding='utf8')
                raise RuntimeError('RUNTIME_CONNECTION_ACTIVE_SKIP_PROBE') from None
        portal.post('/api/logout',json={}).raise_for_status()
    for mode in ('FULL','LOW_POWER'):
        model=ConversationalInference('http://127.0.0.1:8891','vigile-qwen3-4b:latest',mode,'ollama')
        original_complete=model._complete;original_explain=model.explain
        calls=[];errors=[]
        def complete(*args,**kwargs):
            stage='GENERATION' if 'sentences' in args[1].get('properties',{}) else 'VERIFICATION'
            start=time.perf_counter()
            try:
                result=original_complete(*args,**kwargs)
                calls.append({'stage':stage,'result':result[0],'metrics':result[1],'seconds':time.perf_counter()-start})
                return result
            except Exception as exc:
                code=str(exc);calls.append({'stage':stage,'error_type':type(exc).__name__,'safe_code':code if re.fullmatch(r'[A-Z0-9_]{1,120}',code) else 'NONPUBLIC_ERROR_DETAIL','seconds':time.perf_counter()-start});raise
        def explain(*args,**kwargs):
            try:return original_explain(*args,**kwargs)
            except Exception as exc:
                code=str(exc);errors.append({'type':type(exc).__name__,'safe_code':code if re.fullmatch(r'[A-Z0-9_]{1,120}',code) else 'NONPUBLIC_ERROR_DETAIL'});raise
        model._complete=complete;model.explain=explain
        for repetition in range(3):
            calls.clear();errors.clear();before=model.model_http_calls;start=time.perf_counter()
            result=answer_monitoring(reader,model,'A-cycle-14',report['question'],library=library)
            report['rows'].append({'mode':mode,'repetition':repetition,'seconds':time.perf_counter()-start,'requests_attempted':model.model_http_calls-before,'status':result['status'],'generated_count':len(result['generated']),'stages':list(calls),'errors':list(errors),'engine_result_ids':[b['id'] for b in result['answer']]})
            destination.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
            print(json.dumps({k:report['rows'][-1][k] for k in ('mode','repetition','requests_attempted','status','errors')}),flush=True)
finally:reader.close()
