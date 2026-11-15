import test from 'node:test';
import assert from 'node:assert/strict';
import {EXERCISE_PLANS,sessionElapsed,pauseSession,resumeSession,sleepInterval,dailySeries,dailySumSeries,exerciseSummary,dailyMealTotals,validatePerceivedExertion,sleepClockSummary} from '../src/exercise.js';

test('exercise catalog covers resistance, aerobic, mobility and coordination with useful safe instructions',()=>{
 assert.deepEqual(new Set(EXERCISE_PLANS.map(p=>p.workout_type)),new Set(['RESISTANCE','AEROBIC','MOBILITY','BALANCE']));
 for(const plan of EXERCISE_PLANS){assert.ok(plan.objective);assert.ok(plan.precautions);assert.ok(plan.activities.length>=2);for(const activity of plan.activities){assert.ok(activity.setup);assert.ok(activity.instructions);assert.ok(activity.phases.length>=2);assert.ok(activity.tracking);}}
});

test('exercise session timer accumulates only active segments and pause/resume does not rewrite elapsed history',()=>{
 const started={status:'IN_PROGRESS',elapsed_seconds:25,segment_started_at:'2026-11-15T10:00:00.000Z'};
 assert.equal(sessionElapsed(started,Date.parse('2026-11-15T10:00:35Z')),60);
 const paused=pauseSession(started,'2026-11-15T10:00:35Z');assert.equal(paused.status,'PAUSED');assert.equal(paused.elapsed_seconds,60);
 const resumed=resumeSession(paused,'2026-11-15T10:10:00Z');assert.equal(sessionElapsed(resumed,Date.parse('2026-11-15T10:10:15Z')),75);
 assert.throws(()=>resumeSession({...paused,status:'COMPLETED'}),/Only paused or in-progress/);
});

test('sleep interval validates timezone-aware ordering and maximum duration',()=>{
 assert.equal(sleepInterval('2026-11-15T22:30:00-05:00','2026-11-16T06:00:00-05:00'),450);
 assert.throws(()=>sleepInterval('2026-11-15T10:00:00','2026-11-15T11:00:00'),/timezone-qualified/);
 assert.throws(()=>sleepInterval('2026-11-15T11:00:00Z','2026-11-15T10:00:00Z'),/ordered/);
 assert.throws(()=>sleepInterval('2026-11-15T00:00:00Z','2026-11-16T01:00:00Z'),/24 hours/);
});

test('longitudinal summaries deduplicate session checkpoints and label data provenance',()=>{
 const rows=[
  {id:'a',occurred_at:'2026-11-15T10:00:00Z',entry_type:'EXERCISE_SESSION',training_session:{session_id:'s1',status:'PAUSED',elapsed_seconds:30}},
  {id:'b',occurred_at:'2026-11-15T10:02:00Z',entry_type:'EXERCISE_SESSION',training_session:{session_id:'s1',status:'COMPLETED',elapsed_seconds:120}},
  {id:'c',occurred_at:'2026-11-15T11:00:00Z',entry_type:'EXERCISE_SESSION',training_session:{session_id:'s2',status:'STOPPED',elapsed_seconds:20}}
 ];
 const summary=exerciseSummary(rows);assert.equal(summary.started,2);assert.equal(summary.completed,1);assert.equal(summary.completed_seconds,120);assert.equal(summary.completion_rate,.5);
 const points=dailySeries([{entry_type:'SLEEP',occurred_at:'2026-11-15T06:00:00Z',duration_minutes:450,synthetic_data:true}], 'SLEEP', row=>row.duration_minutes);
 assert.equal(points[0].source,'SYNTHETIC_FIXTURE');
});

test('daily nutrition estimates preserve missing nutrients instead of summing them as zero',()=>{
 const rows=[
  {entry_type:'MEAL_NOTE',occurred_at:'2026-11-15T08:00:00Z',food_id:'a',source:'SELF_REPORTED',nutrient_estimate:{energy_kcal:100,protein_g:5,carbohydrate_g:10,fat_g:2,water_g:50}},
  {entry_type:'MEAL_NOTE',occurred_at:'2026-11-15T12:00:00Z',food_id:'b',source:'SELF_REPORTED',nutrient_estimate:{energy_kcal:null,protein_g:3,carbohydrate_g:4,fat_g:1,water_g:25}},
  {entry_type:'MEAL_NOTE',occurred_at:'2026-11-16T08:00:00Z',food_id:'c',source:'SELF_REPORTED',nutrient_estimate:{energy_kcal:200,protein_g:8,carbohydrate_g:20,fat_g:4,water_g:75}}
 ];
 const days=dailyMealTotals(rows);assert.equal(days[0].nutrients.energy_kcal.complete_estimated_total,null);assert.equal(days[0].nutrients.energy_kcal.missing_entries,1);assert.equal(days[0].nutrients.protein_g.complete_estimated_total,8);assert.equal(days[1].nutrients.energy_kcal.complete_estimated_total,200);
});

test('daily hydration totals aggregate entries and keep mixed data provenance visible',()=>{
 const rows=[
  {entry_type:'HYDRATION',occurred_at:'2026-11-15T08:00:00Z',amount_ml:250,synthetic_data:true},
  {entry_type:'HYDRATION',occurred_at:'2026-11-15T12:00:00Z',amount_ml:400,synthetic_data:false},
  {entry_type:'HYDRATION',occurred_at:'2026-11-16T12:00:00Z',amount_ml:100,synthetic_data:false}
 ];
 const totals=dailySumSeries(rows,'HYDRATION',r=>r.amount_ml);assert.equal(totals[0].value,650);assert.equal(totals[0].entries,2);assert.equal(totals[0].source,'MIXED_PROVENANCE');assert.equal(totals[1].value,100);
});

test('perceived exertion is optional and bounded as a user self-report',()=>{assert.equal(validatePerceivedExertion(''),null);assert.equal(validatePerceivedExertion('0'),0);assert.equal(validatePerceivedExertion('10'),10);assert.throws(()=>validatePerceivedExertion('-1'));assert.throws(()=>validatePerceivedExertion('11'));assert.throws(()=>validatePerceivedExertion('2.5'));});



test('daily history uses UTC calendar days across explicit offsets and never accepts invalid or naive times',()=>{
 const rows=[{entry_type:'HYDRATION',occurred_at:'2026-11-16T00:30:00+14:00',amount_ml:100},{entry_type:'HYDRATION',occurred_at:'2026-11-15T12:00:00Z',amount_ml:200},{entry_type:'HYDRATION',occurred_at:'2026-11-15T12:00:00',amount_ml:999},{entry_type:'HYDRATION',occurred_at:'2026-02-31T12:00:00Z',amount_ml:999}];
 const totals=dailySumSeries(rows,'HYDRATION',r=>r.amount_ml);assert.equal(totals.length,1);assert.equal(totals[0].date,'2026-11-15');assert.equal(totals[0].value,300);assert.equal(totals[0].entries,2);
});
test('UTC sleep clock spread handles midnight wrapping and undefined or insufficient samples',()=>{
 const rows=[{entry_type:'SLEEP',sleep_start:'2026-11-14T23:55:00Z'},{entry_type:'SLEEP',sleep_start:'2026-11-16T00:05:00Z'},{entry_type:'SLEEP',sleep_start:null}];const result=sleepClockSummary(rows);assert.equal(result.eligible_start_times,2);assert.equal(result.missing_or_invalid_start_times,1);assert.ok(Math.abs(result.circular_std_minutes-5)<.01);assert.ok(result.mean_start_utc_minutes<.01||result.mean_start_utc_minutes>1439.99);assert.equal(result.medical_interpretation,'NOT_PROVIDED');
 assert.equal(sleepClockSummary(rows.slice(0,1)).circular_std_minutes,null);assert.equal(sleepClockSummary([{entry_type:'SLEEP',sleep_start:'2026-11-15T00:00:00Z'},{entry_type:'SLEEP',sleep_start:'2026-11-15T12:00:00Z'}]).status,'NO_DEFINED_CIRCULAR_MEAN');
});


test('exercise checkpoint ordering compares instants across timezone offsets',()=>{
 const row=(occurred_at,status)=>({occurred_at,training_session:{session_id:'offset-test',status,elapsed_seconds:60}});
 const result=exerciseSummary([row('2026-11-15T11:00:00+03:00','IN_PROGRESS'),row('2026-11-15T08:30:00Z','COMPLETED'),row('2026-11-15T12:00:00','STOPPED')]);
 assert.equal(result.completed,1);assert.equal(result.started,1);
 assert.throws(()=>sleepInterval('2026-02-30T00:00:00Z','2026-03-02T01:00:00Z'));
});
