"""Reproducible synthetic HTTP demonstration using the actual FastAPI application."""
from pathlib import Path
from datetime import timedelta
import json,secrets,time,tracemalloc
from .clinical_simulator import AS_OF,observation
from .clinical_models import ClinicalRequest
from .api import create_app
from .store import digest

def run(root,output=None):
    from fastapi.testclient import TestClient
    root=Path(root)
    if output is None:
        import tempfile
        folder=Path(tempfile.mkdtemp(prefix='vigile-clinical-'))
    else:
        folder=Path(output);folder.mkdir(parents=True,exist_ok=False)
    writer=secrets.token_urlsafe(32);reader=secrets.token_urlsafe(32)
    tokens={writer:{'id':'clinical-demo-researcher','role':'researcher','subject_ids':['*'],'mission_ids':['*']},
            reader:{'id':'clinical-demo-rag','role':'reader','subject_ids':['clinical-crew'],'mission_ids':['clinical-earth']}}
    transcript=[]; durations=[];tracemalloc.start()
    with TestClient(create_app(root,folder/'vigile.sqlite3',tokens)) as client:
        def call(method,path,body=None,read=False):
            start=time.perf_counter()
            response=client.request(method,path,json=body,headers={'Authorization':'Bearer '+(reader if read else writer)})
            durations.append((time.perf_counter()-start)*1000)
            if response.status_code not in (200,201): raise RuntimeError(f'{method} {path}: {response.status_code}: {response.text}')
            result=response.json();transcript.append({'method':method,'path':path,'credential_role':'reader' if read else 'researcher','request':body,'response':result})
            return result
        call('POST','/missions',{'id':'clinical-earth','phase':'PRE_MISSION','gravity':'EARTH','environment':'HABITABLE_VOLUME','mode':'NOMINAL','synthetic':True})
        call('POST','/profiles',{'id':'clinical-crew','mission_id':'clinical-earth','synthetic':True})
        # Numeric observations go through the pre-existing device/measurement endpoints.
        bindings=[]
        for concept,value,unit,method in [('plasma_glucose_mg_dl',180,'mg/dL','VENOUS_PLASMA'),('beta_hydroxybutyrate_mmol_l',4.2,'mmol/L','SYNTHETIC_LAB'),('venous_pH',7.22,'pH','VENOUS_BLOOD_GAS')]:
            identifier='demo-'+concept
            call('POST','/devices',{'id':identifier,'variable':concept,'unit':unit,'calibration_id':'cal-'+identifier,
             'calibrated_at':(AS_OF-timedelta(days=1)).isoformat(),'valid_until':(AS_OF+timedelta(days=1)).isoformat(),
             'technical_min':0,'technical_max':1000,'max_age_seconds':86400,'policy_reference':'SYNTHETIC_TECHNICAL_RANGE_NOT_CLINICAL','synthetic':True})
            call('POST','/measurements',{'id':identifier,'subject_id':'clinical-crew','mission_id':'clinical-earth','variable':concept,
             'value':value,'unit':unit,'timestamp':AS_OF.isoformat(),'device_id':identifier,'calibration_id':'cal-'+identifier,
             'method':method,'protocol':'SYNTHETIC_DEMO','phase':'PRE_MISSION','reported_quality':'ACCEPTABLE','synthetic':True,'provenance':'SYNTHETIC_ONLY'})
            bindings.append({'measurement_id':identifier,'concept':concept,'sample_id':'demo-sample'})
        def request(condition,values,presentation=None):
            return ClinicalRequest(subject_id='clinical-crew',mission_id='clinical-earth',condition_id=condition,presentation_id=presentation,
              population='NONPREGNANT_ADULT',as_of=AS_OF,window_start=AS_OF-timedelta(hours=1),observations=[observation(k,v) for k,v in values.items()]).model_dump(mode='json')
        dka_request=request('DKA',{'known_diabetes':True});dka_request['measurement_bindings']=bindings
        dka=call('POST','/clinical/evaluations',dka_request)
        assert dka['results']['DKA']['diagnostic_status']=='CRITERIA_MET' and dka['urgency']=='EMERGENCY'
        anaph_request=request('ANAPHYLAXIS',{'acute_onset_minutes_to_hours':True,'known_or_highly_probable_allergen':True,'laryngeal_involvement':True,'skin_or_mucosal_involvement':False})
        anaph=call('POST','/clinical/evaluations',anaph_request)
        assert anaph['results']['ANAPHYLAXIS']['diagnostic_status']=='CRITERIA_MET'
        dizziness_request=request(None,{'dizziness':True,'tachycardia':True,'postural_trigger':False,'irregular_pulse':True},'PRES-DIZZINESS-TACHYCARDIA')
        dizziness=call('POST','/clinical/presentations/evaluate',dizziness_request)
        assert dizziness['differential'][0]['condition_id']=='EXTERNAL_ARRHYTHMIA_PATHWAY'
        assert [t['test_id'] for t in dizziness['next_tests']]==['TEST-ECG']
        for out in (dka,anaph,dizziness):
            identifier=out['id']
            call('GET','/clinical/evaluations/'+identifier,read=True)
            call('GET','/clinical/evaluations/'+identifier+'/differential',read=True)
            call('GET','/clinical/evaluations/'+identifier+'/next-tests',read=True)
            assert call('GET','/clinical/evaluations/'+identifier+'/replay',read=True)['matches']
        call('POST','/clinical/protocols/PROT-DKA-ADULT-2024/eligibility',{'evaluation_id':dka['id']})
        updated=dict(dka_request);updated['observations']=updated['observations']+[observation('potassium_mmol_l',3.2).model_dump(mode='json')]
        followup=call('POST','/clinical/evaluations/'+dka['id']+'/reassess',updated)
        assert followup['results']['DKA']['protocol_status']=='BLOCKED_CONTRAINDICATION'
        assert call('GET','/clinical/evaluations/'+dka['id'],read=True)['results']['DKA']['protocol_status']=='BLOCKED_MISSING_DATA'
        denied=client.post('/clinical/evaluations',json=dka_request,headers={'Authorization':'Bearer '+reader})
        assert denied.status_code==403
        assert call('GET','/audit/verify')['valid']
        knowledge=call('GET','/clinical/knowledge/version',read=True)
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    report={'clinical_validation':False,'transport':'FastAPI ASGI HTTP TestClient; no external network calls',
      'request_count':len(durations),'latency_ms_median':sorted(durations)[len(durations)//2],
      'latency_ms_max':max(durations),'python_peak_tracemalloc_bytes':peak,'sqlite_bytes':(folder/'vigile.sqlite3').stat().st_size,
      'knowledge_hash':knowledge['knowledge_hash'],'all_replays_match':True,'reader_write_denied':True,
      'request_hashes':{'dka':digest(dka_request),'anaphylaxis':digest(anaph_request),'dizziness':digest(dizziness_request)},
      'outputs':str(folder.resolve())}
    for name,obj in [('demo-report',report),('synthetic-http-transcript',transcript),('request-dka',dka_request),('request-anaphylaxis',anaph_request),('request-dizziness',dizziness_request)]:
        (folder/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    print(json.dumps(run(Path(__file__).resolve().parents[2],args.output),indent=2))
