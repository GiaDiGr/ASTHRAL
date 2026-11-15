import test from 'node:test';
import assert from 'node:assert/strict';
import {KSS_ANCHORS,TLX_DIMENSIONS,TLX_PAIRS,csvCell,neuroguardEntries,summarizeReactionTrials,weightedTlx} from '../src/neuroguard-metrics.js';

test('NeuroGuard provides nine KSS labels and all fifteen distinct TLX pairs',()=>{
  assert.equal(KSS_ANCHORS.length,9);
  assert.equal(new Set(TLX_PAIRS.map(pair=>[pair.factor_a,pair.factor_b].sort().join('|'))).size,15);
});

test('weighted NASA-TLX score uses validated pair choices and remains distinct from its unweighted mean',()=>{
  const ratings=Object.fromEntries(TLX_DIMENSIONS.map(({id})=>[id,id==='mental'?100:0]));
  const choices=TLX_PAIRS.map(({factor_a,factor_b})=>({factor_a,factor_b,selected:factor_a==='mental'||factor_b==='mental'?'mental':factor_a}));
  const result=weightedTlx(ratings,choices);
  assert.equal(result.weights.mental,5);
  assert.equal(result.weighted_score,33.33);
  assert.equal(result.unweighted_descriptive_mean,16.67);
});

test('NASA-TLX rejects duplicated, omitted and contradictory pairs or malformed rating keys',()=>{
  const ratings=Object.fromEntries(TLX_DIMENSIONS.map(({id})=>[id,50]));
  const choices=TLX_PAIRS.map(pair=>({...pair,selected:pair.factor_a}));
  assert.throws(()=>weightedTlx(ratings,[...choices.slice(0,14),choices[0]]),/Each NASA-TLX pair/);
  assert.throws(()=>weightedTlx(ratings,choices.map((pair,index)=>index===0?{...pair,selected:'frustration'}:pair)),/Invalid NASA-TLX pair/);
  assert.throws(()=>weightedTlx({...ratings,extra:0},choices),/exactly the six named dimensions/);
});

test('reaction summary keeps exact 100, 355 and 500 ms boundaries and timeout lapses',()=>{
  const result=summarizeReactionTrials([
    {response_ms:99,timed_out:false},{response_ms:100,timed_out:false},{response_ms:354,timed_out:false},
    {response_ms:355,timed_out:false},{response_ms:500,timed_out:false},{response_ms:null,timed_out:true}
  ]);
  assert.equal(result.median_rt_ms,354.5);
  assert.equal(result.lapses_355ms,3);
  assert.equal(result.lapses_500ms,2);
  assert.equal(result.anticipations,1);
  assert.equal(result.timeouts,1);
});

test('CSV output quotes cells and protects spreadsheet formula prefixes',()=>{
  assert.equal(csvCell('text, "quoted"\nnext'),'"text, ""quoted""\nnext"');
  assert.equal(csvCell(' =1+1'),"\"' =1+1\"");
  assert.equal(csvCell(null),'""');
});

test('NeuroGuard entry selector ignores legacy wellbeing records and malformed inputs',()=>{
  assert.deepEqual(neuroguardEntries(null),[]);
  assert.equal(neuroguardEntries([
    {entry_type:'WELLBEING',mood_rating_1_5:3},
    {entry_type:'WELLBEING',neuroguard:{task:'KSS'}},
    {entry_type:'SLEEP',neuroguard:{task:'KSS'}}
  ]).length,1);
});
