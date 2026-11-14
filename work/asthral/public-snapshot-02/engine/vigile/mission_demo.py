"""Seeded integrated mission using the existing API, monitoring and clinical engines.

Synthetic software demonstration, never clinical, operational or flight validation.
Default run is entirely offline and makes zero inference requests.
"""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import argparse,hashlib,json,random,secrets,time,os,subprocess,sys
from fastapi.testclient import TestClient
from .api import create_app
from .models import MissionContext,AstronautProfile,Device,Measurement,BaselineRequest
from .monitoring_models import MonitoringRequest
from .clinical_simulator import observation
from .mission_frames import capture_frame,read_frame
from .store import digest

START=datetime(2026,8,1,12,tzinfo=timezone.utc)
POLICY='V011_SYNTHETIC_TECHNICAL_FIXTURE_NOT_A_CLINICAL_PROTOCOL'
SUBJECTS=('mission-crew-A','mission-crew-B')
MID='mission-v011'

def execute(client,writer,acquisition,seed=42,verify_replays=True):
    rng=random.Random(seed);engine=client.app.state.engine;outputs=[];requests=[];frames=[];timings=[]
    headers={'Authorization':'Bearer '+writer};acq={'Authorization':'Bearer '+acquisition}
    def post(path,body,h=headers):
        response=client.post(path,json=body.model_dump(mode='json') if hasattr(body,'model_dump') else body,headers=h)
        if response.status_code not in (200,201): raise RuntimeError('MISSION_REQUEST_FAILED '+path+' '+response.text)
        return response.json()
    def context(phase,gravity):return MissionContext(id=MID,phase=phase,gravity=gravity,environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=True)
    post('/missions',context('PRE_MISSION','EARTH'))
    for sid in SUBJECTS:post('/profiles',AstronautProfile(id=sid,mission_id=MID,synthetic=True))
    devices={};previous={s:None for s in SUBJECTS};baselines={s:[] for s in SUBJECTS}
    base={SUBJECTS[0]:{'physiology.vo2max':50,'physiology.strength':500,'sleep.duration':8},
          SUBJECTS[1]:{'physiology.vo2max':45,'physiology.strength':430,'sleep.duration':7.5}}
    unit={'physiology.vo2max':'mL/min/kg','physiology.strength':'N','sleep.duration':'h','physiology.heart_rate':'bpm',
          'physiology.spo2':'%','environment.ppo2':'mmHg','potassium_mmol_l':'mmol/L','plasma_glucose_mg_dl':'mg/dL',
          'beta_hydroxybutyrate_mmol_l':'mmol/L','venous_pH':'pH'}
    pre={s:{v:[] for v in base[s]} for s in SUBJECTS}
    counter=0
    def measure(sid,var,value,day,phase,quality='ACCEPTABLE',suffix='',when=None):
        nonlocal counter
        key=(sid,var,suffix=='second-device')
        if key not in devices:
            did='mission-device-'+str(len(devices));devices[key]=did
            post('/devices',Device(id=did,variable=var,unit=unit[var],calibration_id='cal-'+did,
                 calibrated_at=START-timedelta(days=30),valid_until=START+timedelta(days=90),technical_min=0,
                 technical_max=100000,max_age_seconds=86400*2,policy_reference=POLICY,synthetic=True,conflict_tolerance=0,alignment_seconds=1))
        did=devices[key];counter+=1
        method='VENOUS_PLASMA' if var=='plasma_glucose_mg_dl' else 'VENOUS_BLOOD_GAS' if var=='venous_pH' else 'DIRECT'
        return Measurement(id='mission-sample-'+str(counter),subject_id=sid,mission_id=MID,variable=var,value=value,unit=unit[var],
                  timestamp=START+timedelta(days=day if when is None else when),device_id=did,calibration_id='cal-'+did,
                  method=method,protocol=POLICY,phase=phase,reported_quality=quality,synthetic=True,provenance='SEEDED_SYNTHETIC_MISSION_NOT_CLINICAL_DATA')
    def cycle(sid,day,ms,obs=(),acute=False):
        # Exercise the operator acquisition boundary, then researcher orchestration.
        for m in ms:post('/measurements',m,acq)
        rid=sid+'-cycle-'+str(day).replace('.','p');at=START+timedelta(days=day)
        req=MonitoringRequest(id=rid,subject_id=sid,mission_id=MID,previous_run_id=previous[sid],as_of=at,
             history_start=START-timedelta(days=7),clinical_window_start=START+timedelta(days=18) if acute else at,
             clinical_context_id=sid+('-acute' if acute else '-context-'+str(day).replace('.','p')),policy_reference=POLICY,
             population='NONPREGNANT_ADULT',age_years=35 if sid==SUBJECTS[0] else 42,measurements=ms,observations=list(obs),
             baseline_ids=baselines[sid],followup_at=at+timedelta(days=1),ewma_lambda=.5,cusum_allowance=0)
        t=time.perf_counter();out=post('/monitoring/cycles',req);timings.append((time.perf_counter()-t)*1000)
        previous[sid]=rid;outputs.append(out);requests.append(req.model_dump(mode='json'))
        frames.append(capture_frame(client.app,'frame-'+rid,rid));return out
    for day in (-7,-5,-3):
        for sid in SUBJECTS:
            ms=[measure(sid,v,value+(-.5 if day==-7 else .5 if day==-3 else 0),day,'PRE_MISSION') for v,value in base[sid].items()]
            for m in ms:pre[sid][m.variable].append(m.id)
            cycle(sid,day,ms)
    for sid in SUBJECTS:
        for i,(var,ids) in enumerate(pre[sid].items()):
            bid=sid+'-baseline-'+str(i);post('/baselines',BaselineRequest(id=bid,measurement_ids=ids,as_of=START-timedelta(days=2),minimum_observations=3,protocol_reference=POLICY));baselines[sid].append(bid)
    post('/missions/'+MID+'/contexts',{'id':'mission-launch','mission_id':MID,'effective_at':START.isoformat(),'context':context('IN_MISSION','MICROGRAVITY').model_dump(mode='json')})
    for day in (0,7,14,18,18.1,21,28,35,42,47):
        phase='POST_MISSION' if day>=42 else 'IN_MISSION'
        if day==42:
            post('/missions/'+MID+'/contexts',{'id':'mission-return','mission_id':MID,'effective_at':(START+timedelta(days=42)).isoformat(),'context':context('POST_MISSION','EARTH').model_dump(mode='json')})
        for sid in SUBJECTS:
            a=sid==SUBJECTS[0];decline=min(day,35) if day<42 else 20-(day-42)
            ms=[measure(sid,'physiology.vo2max',round(base[sid]['physiology.vo2max']-(decline*.42 if a else decline*.04)+rng.uniform(-.05,.05),3),day,phase),
                measure(sid,'physiology.strength',base[sid]['physiology.strength']-(decline*3 if a else decline*.3),day,phase),
                measure(sid,'sleep.duration',round(base[sid]['sleep.duration']-(decline*.04 if a else 0),3),day,phase),
                measure(sid,'physiology.heart_rate',68+(day*.4 if a else 0),day,phase),
                measure(sid,'environment.ppo2',155+day%3,day,phase)]
            if day==0:ms.append(measure(sid,'physiology.spo2',97,day,phase))
            if a and day==14:
                ms=[m for m in ms if m.variable!='sleep.duration']+[measure(sid,'sleep.duration',None,day,phase,'NOT_MEASURED')]
            if a and day==21:
                ms=[m for m in ms if m.variable not in ('physiology.strength','sleep.duration','physiology.heart_rate')]
                ms += [measure(sid,'physiology.strength',-5,day,phase,'INVALID'),measure(sid,'sleep.duration',7,day,'POST_MISSION'),
                       measure(sid,'physiology.heart_rate',88,day,phase),measure(sid,'physiology.heart_rate',120,day,phase,suffix='second-device'),
                       measure(sid,'physiology.vo2max',47,day,phase,when=11)]
            obs=[];acute=not a and day in (18,18.1)
            if acute:
                ms += [measure(sid,'plasma_glucose_mg_dl',180 if day==18 else 160,day,phase),
                       measure(sid,'beta_hydroxybutyrate_mmol_l',4.2 if day==18 else 3.8,day,phase),measure(sid,'venous_pH',7.22 if day==18 else 7.28,day,phase)]
                obs=[observation('known_diabetes',True,timestamp=START+timedelta(days=day),sample='acute-'+str(day))]
                if day==18.1:ms.append(measure(sid,'potassium_mmol_l',4,day,phase))
            cycle(sid,day,ms,obs,acute)
    replays=[client.app.state.monitoring.replay(o['id']) for o in outputs] if verify_replays else []
    clinical_replays=[client.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')] if verify_replays else []
    byid={o['id']:o for o in outputs}
    acute=byid[SUBJECTS[1]+'-cycle-18']['clinical_evaluations']['DKA']['results']['DKA']
    repeat=byid[SUBJECTS[1]+'-cycle-18p1']['clinical_evaluations']['DKA']['results']['DKA']
    assert acute['diagnostic_status']==repeat['diagnostic_status']=='CRITERIA_MET'
    assert not acute['missing_required'] and {'bicarbonate_mmol_l','urine_ketones_plus'}<=set(acute['optional_not_measured'])
    assert 'potassium_mmol_l' in acute['required_for_protocol_safety'] and 'potassium_mmol_l' not in repeat['required_for_protocol_safety']
    assert acute['protocol_status'].startswith('BLOCKED') and repeat['protocol_status'].startswith('BLOCKED')
    assert all(r['matches'] for r in replays+clinical_replays) and engine.store.verify()
    # Stable clinical/monitoring semantics, excluding random storage IDs and audit wall clock.
    semantics=[{'id':o['id'],'as_of':o['as_of'],'domains':[{**d,'indicators':[{k:v for k,v in i.items() if k!='normative_finding_id'} for i in d['indicators']]} for d in o['domains']],
                'clinical':{k:v['results'] for k,v in o['clinical_evaluations'].items()},'events':o['events'],'episode_ids':o['episode_ids']} for o in outputs]
    return {'format':'VIGILE_INTEGRATED_MISSION_1','seed':seed,'synthetic':True,'clinical_validation':False,'clinical_execution':'BLOCKED',
            'start':START.isoformat(),'subjects':list(SUBJECTS),'mission_id':MID,'cycles':len(outputs),'frames':frames,
            'requests':requests,'outputs':outputs,'replays':replays,'clinical_replays':clinical_replays,'semantic_hash':digest(semantics),
            'request_hash':digest(requests),'implementation_hash':engine.implementation_hash,'knowledge_hash':client.app.state.clinical.knowledge.hash,
            'audit_integrity':True,'performance':{'cycle_latency_ms':timings,'maximum_ms':max(timings),'mean_ms':sum(timings)/len(timings),
             'scope':'Local ASGI TestClient including SQLite, excludes network and LLM; not flight performance'},
            'assistant':{'generation_attempts':0,'generation_accepted':0,'mode':'OFFLINE_NOT_REQUESTED'}}

def prepare(folder,seed=42,model_config=None,verify_replays=True):
    folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=False)
    writer,acquisition,reader,access=[secrets.token_urlsafe(32) for _ in range(4)]
    scope={'subject_ids':list(SUBJECTS),'mission_ids':[MID]}
    mapping={writer:{'id':'mission-researcher','role':'researcher',**scope},acquisition:{'id':'mission-acquisition','role':'operator',**scope},reader:{'id':'mission-reader','role':'reader',**scope}}
    # Initial mission and devices require researcher with wildcard registration scope.
    mapping[writer].update(subject_ids=['*'],mission_ids=['*'])
    root=Path(__file__).resolve().parents[2];start=time.perf_counter();cpu_start=time.process_time()
    with TestClient(create_app(root,folder/'vigile.sqlite3',mapping)) as client:
        report=execute(client,writer,acquisition,seed,verify_replays)
        rh={'Authorization':'Bearer '+reader}
        for frame in report['frames']:
            sid=next(s for s in SUBJECTS if frame['monitoring_id'].startswith(s))
            response=client.get('/dashboard/subjects/'+sid+'?mission_id='+MID+'&frame_id='+frame['id'],headers=rh);response.raise_for_status()
            assert response.json()==read_frame(client.app.state.engine,frame['id'],sid,MID)
        assert client.post('/monitoring/cycles',json=report['requests'][0],headers=rh).status_code==403
        report['reader_contract']='PASS_SCOPED_READ_WRITE_DENIED'
        (folder/'openapi.json').write_text(json.dumps(client.app.openapi(),indent=2),encoding='utf8')
    # Store new credentials only; never reuse or copy historical credentials.
    from .local_protection import protect_secret,restrict_directory
    mapping={'sha256:'+hashlib.sha256(t.encode()).hexdigest():p for t,p in mapping.items() if p['role']!='researcher'}
    protect_secret(json.dumps(mapping),folder/'server-tokens.json');protect_secret(reader,folder/'reader-token.txt');protect_secret(access,folder/'portal-access.txt');protect_secret(acquisition,folder/'acquisition-token.txt')
    config={'backend_url':'http://127.0.0.1:8897','reader_token_file':str(folder/'reader-token.txt'),'access_code_file':str(folder/'portal-access.txt'),
            'mode':'FULL','model_url':'http://127.0.0.1:8891','model':'vigile-qwen3-4b:latest','inference_provider':'ollama','library_manifest':str(root/'engine/local_ai/library-v080.json')}
    if model_config:
        previous=json.loads(Path(model_config).read_text(encoding='utf8'))
        for key in ('model_url','model','inference_provider','library_manifest'):
            if key in previous:config[key]=previous[key]
    (folder/'portal-config.json').write_text(json.dumps(config,indent=2),encoding='utf8')
    report['security']=restrict_directory(folder)
    from .space_compute import process_resources,available_memory_bytes
    report['total_seconds']=time.perf_counter()-start;report['database_bytes']=(folder/'vigile.sqlite3').stat().st_size
    report['performance'].update(cpu_seconds=time.process_time()-cpu_start,process=process_resources(os.getpid()),available_memory_bytes=available_memory_bytes(),energy='NOT_MEASURED',gpu='NOT_USED_BY_OFFLINE_MISSION')
    (folder/'mission-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    summary={k:v for k,v in report.items() if k not in ('outputs','requests')}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8');return summary

def serve(folder):
    """Foreground supervisor; only its own children are terminated on Ctrl+C."""
    folder=Path(folder).resolve();env=os.environ.copy();env.pop('VIGILE_TOKENS',None)
    env.update(VIGILE_DB=str(folder/'vigile.sqlite3'),VIGILE_TOKEN_FILE=str(folder/'server-tokens.json'))
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    commands=[[sys.executable,'-m','uvicorn','vigile.api:create_app','--factory','--host','127.0.0.1','--port','8897','--no-access-log'],
              [sys.executable,'-m','vigile.portal','--config',str(folder/'portal-config.json'),'--port','8898']]
    # Refuse occupied ports; never kill or reuse another process.
    import socket
    for port in (8897,8898):
        with socket.socket() as s:s.bind(('127.0.0.1',port))
    children=[]
    try:
        for index,cmd in enumerate(commands):
            child_env=dict(env)
            if index:
                for key in list(child_env):
                    if key.startswith('VIGILE_'):child_env.pop(key)
            children.append(subprocess.Popen(cmd,env=child_env,creationflags=flags))
        print('VIGILE mission: backend http://127.0.0.1:8897 portal http://127.0.0.1:8898; Ctrl+C stops only these children.',flush=True)
        while all(p.poll() is None for p in children):time.sleep(.5)
    finally:
        for p in children:
            if p.poll() is None:p.terminate()
        for p in children:p.wait(timeout=10)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['run','serve']);p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=42);p.add_argument('--model-config',type=Path);args=p.parse_args()
    if args.command=='serve':serve(args.output)
    else:
        result=prepare(args.output,args.seed,args.model_config)
        print(json.dumps({k:result[k] for k in ('cycles','semantic_hash','request_hash','audit_integrity','database_bytes','total_seconds','assistant')},indent=2))
if __name__=='__main__':main()
