import test from 'node:test';
import assert from 'node:assert/strict';
import {createSyntheticMissionSummary} from '../src/mission-summary.js';

test('summary counts only marked synthetic data and omits record content', () => {
  const result=createSyntheticMissionSummary({
    measurement:[
      {measurement:{id:'s-1',synthetic:true,value:999,subject_id:'private'}},
      {measurement:{id:'real-1',synthetic:false,value:12,subject_id:'private'}},
    ],
    baseline:[
      {id:'b-1',measurement_ids:['s-1'],value:999,subject_id:'private'},
      {id:'b-2',measurement_ids:['real-1'],value:12},
    ],
    monitoring_run:[
      {id:'r-1',policy_reference:'SYNTHETIC_RESEARCH',baseline_ids:['b-1'],episode_ids:{DKA:'ep-synthetic-1'},followup_ids:['f-1'],events:[{value:999}]},
      {id:'r-2',policy_reference:'CLINICAL',baseline_ids:['b-2']},
    ],
    followup:[{id:'f-1',episode_id:'ep-synthetic-1',protocol_reference:'SYNTHETIC_RESEARCH',goal_description:'private'}],
  },{
    prevention_entries:[{synthetic_data:true,note:'private'},{synthetic_data:false}],
    radiation_records:[{synthetic_data:true,value:99},{synthetic_data:false,value:2}],
  },'2026-11-15T12:00:00Z');
  assert.deepEqual(result.counts,{
    synthetic_measurements:1,synthetic_baselines:1,synthetic_monitoring_cycles:1,
    synthetic_followup_plans:1,synthetic_prevention_entries:1,synthetic_radiation_records:1,
  });
  const serialized=JSON.stringify(result);
  for(const secret of ['private','999','real-1','s-1','b-1','r-1'])assert.equal(serialized.includes(secret),false);
  assert.equal(result.synthetic_data_only,true);
  assert.equal(result.clinical_validation,false);
  assert.equal(result.authority.treatment_execution_enabled,false);
});

test('summary fails closed for absent, malformed, unmarked and unlinked rows', () => {
  const result=createSyntheticMissionSummary({
    measurement:[{measurement:{id:'m-1',synthetic:false}},{measurement:{id:'m-2'}}],
    baseline:[{id:'b-1',input_ids:['m-1']},{id:'b-2',input_ids:[]}],
    monitoring_run:[{policy_reference:'SYNTHETIC',baseline_ids:['b-1']}],
    followup:[{id:'unlinked',episode_id:'unknown',protocol_reference:'SYNTHETIC'}],
  },{prevention_entries:[{synthetic_data:false}],radiation_records:[{}]});
  assert.deepEqual(result.counts,{synthetic_measurements:0,synthetic_baselines:0,synthetic_monitoring_cycles:0,
    synthetic_followup_plans:0,synthetic_prevention_entries:0,synthetic_radiation_records:0});
  assert.equal(createSyntheticMissionSummary(null).counts.synthetic_measurements,0);
});
