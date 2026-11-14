"""Prepare isolated, reproducible frontend data using existing clinical/API simulators."""
from pathlib import Path
import json,secrets,hashlib
from datetime import timedelta
from .clinical_demo import run as clinical_demo
from .clinical_simulator import AS_OF

def prepare(root,folder):
    from .api import create_app
    from fastapi.testclient import TestClient
    folder=Path(folder).resolve();report=clinical_demo(root,folder)
    temporary=secrets.token_urlsafe(32)
    with TestClient(create_app(root,folder/'vigile.sqlite3',{temporary:'researcher'})) as client:
        def post(path,body):
            r=client.post(path,json=body,headers={'Authorization':'Bearer '+temporary})
            if r.status_code not in (200,201):raise RuntimeError('DEMO_IMPORT_FAILED '+path+' '+r.text)
            return r.json()
        mids=[]
        for variable,unit,values in [('physiology.heart_rate','bpm',[68,69,70,71,69,72,92,104,118]),('environment.ppco2','mmHg',[2.0,2.1,2.0,2.2,2.1,2.0,2.3,2.4,2.5])]:
            device='portal-'+variable
            post('/devices',{'id':device,'variable':variable,'unit':unit,'calibration_id':'cal-'+device,'calibrated_at':(AS_OF-timedelta(days=30)).isoformat(),'valid_until':(AS_OF+timedelta(days=30)).isoformat(),'technical_min':0,'technical_max':1000,'max_age_seconds':864000,'policy_reference':'SYNTHETIC_ONLY_NOT_CLINICAL','synthetic':True})
            ids=[]
            for index,value in enumerate(values):
                mid=device+'-'+str(index);ids.append(mid)
                post('/measurements',{'id':mid,'subject_id':'clinical-crew','mission_id':'clinical-earth','variable':variable,'value':value,'unit':unit,'timestamp':(AS_OF-timedelta(hours=8-index)).isoformat(),'device_id':device,'calibration_id':'cal-'+device,'method':'DIRECT','protocol':'SYNTHETIC_MONITORING','phase':'PRE_MISSION','reported_quality':'ACCEPTABLE','synthetic':True,'provenance':'SYNTHETIC_DISPLAY_SERIES_NOT_DIAGNOSTIC','compartment':'HAB1'})
            if variable=='physiology.heart_rate':
                post('/baselines',{'id':'portal-heart-baseline','measurement_ids':ids[:6],'minimum_observations':5,'protocol_reference':'SYNTHETIC_BASELINE_TEST','as_of':AS_OF.isoformat(),'valid_until':(AS_OF+timedelta(days=1)).isoformat()})
        audit=client.get('/audit/verify',headers={'Authorization':'Bearer '+temporary}).json()
        if not audit['valid']:raise RuntimeError('AUDIT_FAILED')
    reader=secrets.token_urlsafe(32);access=secrets.token_urlsafe(32)
    mapping={'sha256:'+hashlib.sha256(reader.encode()).hexdigest():{'id':'portal-reader','role':'reader','subject_ids':['clinical-crew'],'mission_ids':['clinical-earth']}}
    (folder/'server-tokens.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
    (folder/'reader-token.txt').write_text(reader,encoding='utf-8')
    (folder/'portal-access.txt').write_text(access,encoding='utf-8')
    config={'backend_url':'http://127.0.0.1:8765','reader_token_file':str(folder/'reader-token.txt'),'access_code_file':str(folder/'portal-access.txt'),'model_url':'http://127.0.0.1:11434','model':None}
    (folder/'portal-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    return {'folder':str(folder),'config':str(folder/'portal-config.json'),'access_code_file':str(folder/'portal-access.txt'),'scenarios':['DKA','ANAPHYLAXIS','PRES-DIZZINESS-TACHYCARDIA'],'synthetic':True,'model_downloaded':False}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(prepare(Path(__file__).resolve().parents[2],args.output),indent=2))
