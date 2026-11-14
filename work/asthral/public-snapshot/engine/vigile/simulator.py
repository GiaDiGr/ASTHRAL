"""Seeded software fixtures, NOT physiological models or clinical validation."""
from datetime import datetime,timedelta,timezone
from random import Random
from typing import Literal
from pydantic import Field, model_validator
from .models import Model,MissionContext,AstronautProfile,Device,Measurement

class SyntheticDataset(Model):
    schema_version: Literal['vigile.synthetic.v1']='vigile.synthetic.v1'
    seed: int
    purpose: Literal['SOFTWARE_TEST_ONLY']='SOFTWARE_TEST_ONLY'
    mission: MissionContext
    profile: AstronautProfile
    devices: list[Device]
    measurements: list[Measurement] = Field(max_length=10000)
    groups: dict[str,list[str]]
    scenarios: dict[str,str]

    @model_validator(mode='after')
    def coherent(self):
        if not self.mission.synthetic or not self.profile.synthetic or self.profile.mission_id!=self.mission.id:
            raise ValueError('SYNTHETIC_SCOPE_REQUIRED')
        devices={d.id:d for d in self.devices}; ids={m.id for m in self.measurements}
        if len(devices)!=len(self.devices) or len(ids)!=len(self.measurements): raise ValueError('DUPLICATE_FIXTURE_ID')
        if any(not d.synthetic for d in self.devices): raise ValueError('SYNTHETIC_DEVICE_REQUIRED')
        for m in self.measurements:
            if not m.synthetic or m.device_id not in devices or (m.subject_id,m.mission_id)!=(self.profile.id,self.mission.id):
                raise ValueError('INVALID_FIXTURE_REFERENCE')
        if any(i not in ids for group in self.groups.values() for i in group): raise ValueError('INVALID_GROUP_REFERENCE')
        return self

def generate(seed=42):
    rng=Random(seed); origin=datetime(2025,1,1,12,tzinfo=timezone.utc)
    mission=MissionContext(id='sim-mission',phase='IN_MISSION',gravity='MICROGRAVITY',environment='HABITABLE_VOLUME',
        mode='NOMINAL',synthetic=True,microgravity_eva_planned_or_required=True,exposure_context='INDEFINITE_CABIN')
    profile=AstronautProfile(id='sim-crew',mission_id=mission.id,synthetic=True)
    variables={'vo2':('physiology.vo2max','mL/min/kg',100),'strength':('physiology.strength','N',2000),
        'co2':('environment.ppco2','mmHg',20),'pressure':('environment.pressure','kPa',200)}
    devices=[]
    for name,(variable,unit,maximum) in variables.items():
        devices.append(Device(id='sim-'+name,variable=variable,unit=unit,calibration_id='cal-'+name,
            calibrated_at=origin-timedelta(days=90),valid_until=origin+timedelta(days=400),technical_min=0,
            technical_max=maximum,max_age_seconds=86400,policy_reference='SYNTHETIC_TECHNICAL_FIXTURE_NOT_MEDICAL',
            conflict_tolerance=.01,alignment_seconds=0,synthetic=True))
    defective=devices[0].model_copy(update={'id':'sim-defective','valid_until':origin-timedelta(days=1)})
    devices.append(defective); measurements=[]; groups={}
    def sample(identifier,name,value,day,phase='IN_MISSION',**kw):
        variable,unit,_=variables[name]
        raw=dict(id=identifier,subject_id=profile.id,mission_id=mission.id,variable=variable,value=value,unit=unit,
            timestamp=origin+timedelta(days=day),device_id='sim-'+name,calibration_id='cal-'+name,method='DIRECT',
            protocol='synthetic-'+name,phase=phase,reported_quality='ACCEPTABLE',synthetic=True,
            provenance='VIGILE_SYNTHETIC_V1_SEED_'+str(seed))
        raw.update(kw); m=Measurement(**raw); measurements.append(m); return m.id
    for phase,label,days,vo2s,strengths in [
        ('PRE_MISSION','preflight',[-3,-2,-1],[45,45,45],[600,600,600]),
        ('IN_MISSION','adaptation',[1,2,3],[43,42,41],[590,575,560]),
        ('IN_MISSION','longitudinal',[30,60,90],[40,37,32],[540,500,450]),
        ('POST_MISSION','recovery',[100,110,120],[34,39,43],[470,530,580])]:
        for name,values in [('vo2',vo2s),('strength',strengths)]:
            groups[label+'_'+name]=[sample(label+'-'+name+'-'+str(i),name,round(v+rng.uniform(-.2,.2),4),day,phase) for i,(day,v) in enumerate(zip(days,values))]
    groups['environment']=[]
    for i,day in enumerate([1,30,60,90]):
        end=origin+timedelta(days=day)
        groups['environment'].append(sample('co2-'+str(i),'co2',1.5+i*.7,day,
            timestamp=end-timedelta(hours=1),interval_end=end,method='INTERVAL_MEAN',compartment='SIM_HAB'))
        sample('pressure-'+str(i),'pressure',101.3-i,day,compartment='SIM_HAB')
    groups['co2_full']=['co2-3']
    end=origin+timedelta(days=91)
    groups['co2_gap']=[sample('co2-gap','co2',3.6,91,timestamp=end-timedelta(minutes=30),interval_end=end,method='INTERVAL_MEAN',compartment='SIM_HAB')]
    groups['faults']=[sample('missing','vo2',None,91,reported_quality='NOT_MEASURED'),
        sample('invalid','vo2',35,92,reported_quality='INVALID'),
        sample('defective','vo2',35,93,device_id='sim-defective'),
        sample('wrong-unit','vo2',35,94,unit='mSv'),
        sample('outside-range','vo2',500,95)]
    return SyntheticDataset(seed=seed,mission=mission,profile=profile,devices=devices,measurements=measurements,groups=groups,
        scenarios={'preflight':'Arbitrary repeated values for software baseline tests',
        'adaptation':'Fictional early trajectory, not a physiological model',
        'longitudinal':'Simultaneous VO2/strength decline and environmental variation',
        'recovery':'Postflight descriptive records, no inferred recovery or mission-context mutation',
        'faults':'Missing, invalid, expired calibration, incompatible unit and technical range',
        'co2_gap':'Explicit incomplete interval, must stay inconclusive'})
