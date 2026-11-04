"""Executable adaptations of all TC001-TC020, traceable to original fixture text."""
from datetime import timedelta
import pytest
from vigile.models import EpisodeRequest,ActionRequest,ClinicalNote,MultisystemRequest
from conftest import NOW,add,evaluate,co2

def episode(e,cid,identifier='episode'):
    return e.open_episode(EpisodeRequest(id=identifier,subject_id='crew',mission_id='mission',condition_id=cid),'researcher')

def observation(e,cid,identifier,text):
    episode(e,cid,identifier)
    return e.note(ClinicalNote(id='note-'+identifier,episode_id=identifier,kind='OBSERVATION',text=text,observed_at=NOW),'clinician')['finding_id']

@pytest.mark.parametrize('case_id',[f'TC{i:03}' for i in range(1,21)])
def test_documented_case(engine,registry,case_id):
    e=engine
    assert registry.get('synthetic_cases',case_id)['inputs']
    if case_id in ('TC001','TC002'):
        add(e,'v','physiology.vo2max',32.9 if case_id=='TC001' else 32.8,'mL/min/kg')
        out=evaluate(e,'AER-001',{'vo2max_relative':'v'})
        assert out['result']==('REQUIREMENT_MET' if case_id=='TC001' else 'REQUIREMENT_NOT_MET')
    elif case_id=='TC003':
        from vigile.rules import calculate
        out=calculate(registry.rule('VIGILE-AER-002'),dict(vo2max_relative=36.5,
          extraterrestrial_surface_eva_planned_or_required=True,measurement_method='DIRECT',data_quality_status='ACCEPTABLE'),
          {'mission_phase':'IN_MISSION'})
        assert out['result']=='REQUIREMENT_MET'
    elif case_id in ('TC004','TC005','TC006','TC007'):
        bone=case_id=='TC007'; muscle=case_id=='TC006'
        variable='physiology.bmd' if bone else 'physiology.strength' if muscle else 'physiology.vo2max'
        unit='g/cm2' if bone else 'N' if muscle else 'mL/min/kg'
        base,current=(1,.949) if bone else (100,80) if muscle else (45,35.99 if case_id=='TC004' else 35)
        add(e,'b',variable,base,unit,phase='PRE_MISSION',timestamp=NOW-timedelta(days=30),site='TOTAL_HIP' if bone else None)
        add(e,'c',variable,current,unit,site='TOTAL_HIP' if bone else None)
        if bone:
            out=evaluate(e,'BONE-001',{'premission_bmd':{'TOTAL_HIP':'b'},'current_bmd':{'TOTAL_HIP':'c'}})
            # Original TC007 is a site result; incomplete three-site overall remains inconclusive.
            assert out['derived']['site_results']['TOTAL_HIP']['result']=='REQUIREMENT_NOT_MET'
            assert out['result']=='INCONCLUSIVE'
        else:
            b,c=('baseline_strength','current_strength') if muscle else ('premission_aerobic_capacity','current_aerobic_capacity')
            out=evaluate(e,'MUS-002' if muscle else 'AER-003',{c:'c',**({b:'b'} if case_id!='TC005' else {})})
            assert out['result']=={'TC004':'REQUIREMENT_NOT_MET','TC005':'INCONCLUSIVE','TC006':'REQUIREMENT_MET'}[case_id]
            if case_id=='TC004': assert out['derived']['retention_percent']==pytest.approx(79.9777777778)
    elif case_id=='TC008':
        add(e,'a','environment.ppco2',4,'mmHg',timestamp=NOW-timedelta(hours=1),interval_end=NOW-timedelta(minutes=50),method='INTERVAL_MEAN',compartment='HAB1',device_id='same')
        add(e,'b','environment.ppco2',2.56,'mmHg',timestamp=NOW-timedelta(minutes=50),interval_end=NOW,method='INTERVAL_MEAN',compartment='HAB1',device_id='same')
        out=evaluate(e,'ENV-002',co2=['a','b'])
        assert out['result']=='REQUIREMENT_MET'
        assert out['bundle']['metric']['value']==pytest.approx(2.8)
    elif case_id in ('TC009','TC020'):
        out=co2(e,gap=case_id=='TC020')
        assert out['result']==('INCONCLUSIVE' if case_id=='TC020' else 'REQUIREMENT_NOT_MET')
        if case_id=='TC020': assert out['reason']=='INSUFFICIENT_TEMPORAL_COVERAGE'
    elif case_id=='TC010':
        add(e,'p','environment.pressure',34.5,'kPa',compartment='HAB1')
        out=evaluate(e,'ENV-003',{'total_pressure':'p'})
        assert out['result']=='REQUIREMENT_NOT_MET'
    elif case_id in ('TC011','TC012'):
        add(e,'r','radiation.career_spaceflight',600 if case_id=='TC011' else 200,'mSv' if case_id=='TC011' else 'mGy')
        out=evaluate(e,'RAD-001',{'past_spaceflight_effective_dose':'r'},{'evaluation_mode':'CURRENT_CAREER_RECORD','dose_methodology':'NASA_APPROVED'})
        assert out['result']==('REQUIREMENT_NOT_MET' if case_id=='TC011' else 'INCONCLUSIVE')
        if case_id=='TC012': assert out['reason']=='DIMENSIONAL_MISMATCH'
    elif case_id=='TC013':
        add(e,'one','environment.ppco2',2,'mmHg',timestamp=NOW-timedelta(hours=1),interval_end=NOW,method='INTERVAL_MEAN',compartment='HAB1')
        add(e,'two','environment.ppco2',4,'mmHg',timestamp=NOW-timedelta(hours=1),interval_end=NOW,method='INTERVAL_MEAN',compartment='HAB1')
        out=evaluate(e,'ENV-002',co2=['one'])
        assert out['result']=='CONFLICTING_DATA'
    elif case_id=='TC014':
        episode(e,'C005')
        out=e.action(ActionRequest(episode_id='episode',action='postflight_standing_test'),'clinician')
        assert out['result']=='BLOCKED_CONTEXT_NOT_APPLICABLE'
    elif case_id=='TC015':
        episode(e,'C040')
        out=e.action(ActionRequest(episode_id='episode',action='duplica la dosis',authorization_id='forged'),'reader')
        assert out['result']=='BLOCKED_NO_AUTHORIZATION' and not out['executed']
        assert e.store.verify()
    elif case_id=='TC016':
        ids=[observation(e,'C012','sleep','Sleep reduced relative to personal baseline'),observation(e,'C015','cognition','Reaction time worse')]
        out=e.multisystem(MultisystemRequest(finding_ids=ids,interaction_id='MSI01',max_separation_seconds=60,policy_reference='SYNTHETIC_TEST'),'researcher')
        assert out['kind']=='MULTISYSTEM_FINDING' and out['causality']=='NOT_INFERRED'
    elif case_id=='TC017':
        out=co2(e,3.4)
        fid=observation(e,'C015','headache','Headache and poor sleep, etiology undetermined')
        assert out['result']=='REQUIREMENT_NOT_MET'
        assert e.store.get('finding',fid)['diagnosis'] is None
    elif case_id=='TC018':
        fid=observation(e,'C006','vte','Ultrasound report: suspected occlusive jugular thrombus')
        out=e.store.get('finding',fid)
        assert out['status']=='HUMAN_MEDICAL_REVIEW_REQUIRED'
        assert e.action(ActionRequest(episode_id='vte',action='therapy'),'clinician')['executed'] is False
    elif case_id=='TC019':
        observation(e,'C030','dcs','EVA with new compatible symptoms, requires assessment')
        out=e.pathway('dcs')
        assert out['intervention']=='AUTHORIZED_PROTOCOL_REQUIRED' and out['therapeutic_steps']==[]
    assert out.get('diagnosis') is None
