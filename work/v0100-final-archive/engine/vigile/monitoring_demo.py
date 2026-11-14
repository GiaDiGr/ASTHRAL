"""Deterministic synthetic longitudinal fixtures; never clinical validation.

python -m vigile.monitoring_demo --output data/v070-demo
Creates a NEW output directory; refuses to overwrite previous evidence.
"""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import argparse,json,secrets,time
from .models import MissionContext,AstronautProfile,Device,Measurement,BaselineRequest
from .monitoring_models import MonitoringRequest
from .monitoring import MonitoringService
from .clinical_simulator import observation

START=datetime(2026,9,1,12,tzinfo=timezone.utc)
POLICY='V07_SYNTHETIC_SOFTWARE_POLICY_NOT_A_CLINICAL_PROTOCOL'

def scenarios(engine,submit=None):
    service=MonitoringService(engine);submit=submit or (lambda req:service.run(req,'researcher'))
    outputs=[];requests=[]
    for scenario in ('A','B','C'):
        subject='v07-crew-'+scenario;mission='v07-mission-'+scenario;devices={};baseline_ids=[];previous=None
        engine.register('mission',MissionContext(id=mission,phase='IN_MISSION',gravity='EARTH' if scenario=='B' else 'MICROGRAVITY',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=True),'researcher')
        engine.register('profile',AstronautProfile(id=subject,mission_id=mission,synthetic=True),'researcher')
        def measure(var,value,unit,day,*,suffix='',quality='ACCEPTABLE',phase='IN_MISSION',method='DIRECT',interval_end=None,site=None):
            if var not in devices:
                identifier='dev-'+scenario+'-'+str(len(devices));devices[var]=identifier
                engine.register('device',Device(id=identifier,variable=var,unit=unit,calibration_id='cal-'+identifier,calibrated_at=START-timedelta(days=30),valid_until=START+timedelta(days=90),technical_min=0,technical_max=100000,max_age_seconds=86400*8,policy_reference=POLICY,synthetic=True,conflict_tolerance=0,alignment_seconds=1),'researcher')
            return Measurement(id=scenario+'-'+var.replace('.','-')+'-'+str(day)+suffix,subject_id=subject,mission_id=mission,variable=var,value=value,unit=unit,timestamp=START+timedelta(days=day),device_id=devices[var],calibration_id='cal-'+devices[var],method=method,protocol=POLICY,phase=phase,synthetic=True,provenance='DETERMINISTIC_SYNTHETIC_NOT_CLINICAL',reported_quality=quality,interval_end=interval_end,site=site)
        def cycle(day,measurements=(),observations=(),label=None):
            nonlocal previous
            identifier=scenario+'-cycle-'+(label or str(day))
            req=MonitoringRequest(id=identifier,previous_run_id=previous,subject_id=subject,mission_id=mission,as_of=START+timedelta(days=day),history_start=START,clinical_window_start=START+timedelta(days=max(0,day-1)),clinical_context_id=scenario+'-context',policy_reference=POLICY,population='NONPREGNANT_ADULT',age_years=35,measurements=list(measurements),observations=list(observations),baseline_ids=baseline_ids,followup_at=START+timedelta(days=day+1),ewma_lambda=.5,cusum_allowance=0)
            out=submit(req);outputs.append(out);requests.append(req.model_dump(mode='json'));previous=identifier
            return out
        def personal(var,value,unit,site=None):
            measurements=[measure(var,value+delta,unit,day,phase='PRE_MISSION',site=site) for day,delta in ((-3,-1),(-2,0),(-1,1))]
            for m in measurements:engine.ingest(m,'researcher')
            bid=scenario+'-baseline-'+str(len(baseline_ids))
            engine.build_baseline(BaselineRequest(id=bid,measurement_ids=[m.id for m in measurements],as_of=START,minimum_observations=3,protocol_reference=POLICY),'researcher');baseline_ids.append(bid)
        if scenario=='A':
            personal('physiology.vo2max',50,'mL/min/kg')
            for day,value in ((0,48),(7,44),(14,39)):
                cycle(day,[measure('physiology.vo2max',value,'mL/min/kg',day),measure('physiology.heart_rate',65+day,'bpm',day)])
            cycle(15,[measure('physiology.vo2max',90,'mL/min/kg',15,quality='INVALID')])
            cycle(16,[measure('physiology.vo2max',42,'mL/min/kg',10,suffix='-late')])
        elif scenario=='B':
            def observation_set(day,values):return [observation(k,v,timestamp=START+timedelta(days=day),sample='B-'+str(day)) for k,v in values.items()]
            cycle(0,[measure('plasma_glucose_mg_dl',50,'mg/dL',0,method='VENOUS_PLASMA')],observation_set(0,{'known_diabetes':True,'recent_reduced_intake':True}))
            cycle(0,label='repeat')
            cycle(.01,[measure('plasma_glucose_mg_dl',49,'mg/dL',.01,method='VENOUS_PLASMA')])
            cycle(.02,[measure('plasma_glucose_mg_dl',None,'mg/dL',.02,method='VENOUS_PLASMA',quality='NOT_MEASURED')])
            cycle(.03,[measure('plasma_glucose_mg_dl',55,'mg/dL',.03,method='VENOUS_PLASMA'),measure('plasma_glucose_mg_dl',100,'mg/dL',.03,method='VENOUS_PLASMA',suffix='-contradiction')])
        else:
            personal('physiology.strength',500,'N')
            personal('sleep.duration',8,'h')
            for day in (0,7,14,21,28):
                ms=[measure('physiology.strength',500-day*4,'N',day),measure('sleep.duration',8-day/14,'h',day),measure('cognition.reaction_time',220+day*2,'ms',day),measure('immune.viral_load',100+day*10,'copies/mL',day,site='SYNTHETIC_EBV_SALIVA'),measure('physiology.spo2',97,'%',day),measure('potassium_mmol_l',4,'mmol/L',day)]
                if day:ms.append(measure('radiation.interval_effective_dose',.7,'mSv',day-7,method='INTERVAL_TOTAL',interval_end=START+timedelta(days=day)))
                if day==21:ms.append(measure('sleep.duration',None,'h',day+.001,quality='NOT_MEASURED')) # future arrival is explicitly invalid at this cycle
                cycle(day,ms)
    # Expected properties are stated independently of output values.
    byid={r['id']:r for r in outputs}
    a=byid['A-cycle-14']['domains'][0]['indicators'][0]
    assert a['baseline_comparison']['retention_percent']==78
    assert a['trend']['slope_per_day']<0
    assert byid['A-cycle-15']['domains'][0]['indicators'][0]['value'] is None
    assert byid['A-cycle-14']['clinical_evaluations']['ORTHOSTATIC_HYPOTENSION']['results']['ORTHOSTATIC_HYPOTENSION']['diagnostic_status']=='NOT_APPLICABLE'
    b=byid['B-cycle-0']['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']
    assert b['diagnostic_status']=='CRITERIA_MET' and b['urgency']=='URGENT'
    assert b['metadata']['hypoglycemia_level_minimum_supported']==2 and b['protocol_status'].startswith('BLOCKED')
    hypo=lambda r:next(e for e in r['events'] if e['key']=='clinical:HYPOGLYCEMIA')
    assert not hypo(byid['B-cycle-repeat'])['notify'] and hypo(byid['B-cycle-0.01'])['notify']
    assert byid['B-cycle-0.03']['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']['diagnostic_status']!='CRITERIA_MET'
    assert byid['C-cycle-28']['domains'][2]['accumulated_dose']['effective_dose_mSv']==2.8
    replays=[service.replay(r['id']) for r in outputs]
    assert all(r['matches'] for r in replays) and engine.store.verify()
    return {'mode':'SYNTHETIC_SOFTWARE_DEMONSTRATION_NOT_CLINICAL_VALIDATION','cycles':len(outputs),'outputs':outputs,'requests':requests,'replays':replays,'audit_integrity':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    from fastapi.testclient import TestClient
    from .api import create_app
    token=secrets.token_urlsafe(32);reader=secrets.token_urlsafe(32)
    tokens={token:'researcher',reader:{'id':'synthetic-reader','role':'reader','subject_ids':['v07-crew-'+s for s in 'ABC'],'mission_ids':['v07-mission-'+s for s in 'ABC']}}
    start=time.perf_counter()
    with TestClient(create_app(db_path=args.output/'vigile.sqlite3',tokens=tokens)) as client:
        timings=[]
        def submit(req):
            t=time.perf_counter();response=client.post('/monitoring/cycles',headers={'Authorization':'Bearer '+token},json=req.model_dump(mode='json'));timings.append((time.perf_counter()-t)*1000)
            response.raise_for_status();return response.json()
        report=scenarios(client.app.state.engine,submit)
        for out in report['outputs']:
            r=client.get('/monitoring/cycles/'+out['id'],headers={'Authorization':'Bearer '+reader});r.raise_for_status();assert r.json()==out
        assert client.post('/monitoring/cycles',headers={'Authorization':'Bearer '+reader},json=report['requests'][0]).status_code==403
        report['reader_integration']='PASS_READ_ALLOWED_WRITE_DENIED'
        report['performance']={'cycle_latency_ms':timings,'total_seconds':time.perf_counter()-start,'note':'Local TestClient includes SQLite and snapshot serialization; synthetic workload, not flight benchmark'}
        (args.output/'openapi.json').write_text(json.dumps(client.app.openapi(),indent=2),encoding='utf-8')
    (args.output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    summary={k:v for k,v in report.items() if k not in ('requests','outputs')};summary['database_bytes']=(args.output/'vigile.sqlite3').stat().st_size
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
