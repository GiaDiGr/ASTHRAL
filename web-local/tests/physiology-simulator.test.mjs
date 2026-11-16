import test from 'node:test';
import assert from 'node:assert/strict';
import {PARAMETERS,initialSimulation,evaluateTraining,oxygenPartialPressure,evaluateAtmosphereTraining,ATMOSPHERE_TRAINING_BOUNDS,TRAINING_PRESETS} from '../src/physiology-simulator.js';

test('synthetic controls start inside their declared bounds and reset independently',()=>{
 const first=initialSimulation(),second=initialSimulation();first.heart_rate=130;
 assert.equal(second.heart_rate,72);
 for(const p of PARAMETERS)assert.ok(second[p.id]>=p.min&&second[p.id]<=p.max);
});
test('presets are valid and only configured training rules issue warnings',()=>{
 for(const changes of Object.values(TRAINING_PRESETS))for(const [id,value] of Object.entries({...initialSimulation(),...changes}))assert.equal(evaluateTraining(id,value).synthetic,true);
 assert.equal(evaluateTraining('spo2',TRAINING_PRESETS['Combined training scenario'].spo2).category,'TRAINING_WARNING');
 assert.equal(evaluateTraining('temperature',TRAINING_PRESETS['Temperature scenario'].temperature).category,'NO_CONFIGURED_WARNING');
});
test('dry gas oxygen partial pressure uses fraction and rejects unavailable inputs',()=>{
 assert.ok(Math.abs(oxygenPartialPressure(101.3,21)-21.273)<1e-9);
 assert.equal(oxygenPartialPressure(29.6,100),29.6);
 assert.throws(()=>oxygenPartialPressure(-1,21));
 assert.throws(()=>oxygenPartialPressure(100,101));
 assert.throws(()=>oxygenPartialPressure(NaN,21));
});
test('illustrative warning rules are deterministic and carry no clinical authority',()=>{
 assert.equal(evaluateTraining('spo2',90).category,'NO_CONFIGURED_WARNING');
 assert.equal(evaluateTraining('spo2',89).category,'TRAINING_WARNING');
 assert.equal(evaluateTraining('heart_rate',121).category,'TRAINING_WARNING');
 assert.equal(evaluateTraining('heart_rate',120).category,'NO_CONFIGURED_WARNING');
 assert.equal(evaluateTraining('spo2',89).clinical_authority,false);
 assert.throws(()=>evaluateTraining('spo2',NaN));
 assert.throws(()=>evaluateTraining('spo2',101));
 assert.throws(()=>evaluateTraining('unknown',1));
});
test('cabin and spacesuit oxygen assessments use independent pressure-fraction inputs',()=>{
 const cabin=evaluateAtmosphereTraining('cabin',101.3,21),suit=evaluateAtmosphereTraining('spacesuit',29.6,100);
 assert.equal(cabin.value,21.27);assert.equal(cabin.category,'NO_CONFIGURED_WARNING');
 assert.equal(suit.value,29.6);assert.equal(suit.category,'NO_CONFIGURED_WARNING');
 assert.equal(initialSimulation().spo2,98);
 assert.notEqual(evaluateAtmosphereTraining('spacesuit',29.6,50).value,suit.value);
 assert.equal(evaluateAtmosphereTraining('spacesuit',29.6,50).parameter,'spacesuit_oxygen_partial_pressure');
});
test('atmosphere training bounds are explicit, illustrative and strict at equality',()=>{
 assert.deepEqual(ATMOSPHERE_TRAINING_BOUNDS,{low_kpa:10,high_kpa:40});
 assert.equal(evaluateAtmosphereTraining('cabin',100,10).category,'NO_CONFIGURED_WARNING');
 assert.equal(evaluateAtmosphereTraining('cabin',100,40).category,'NO_CONFIGURED_WARNING');
 assert.equal(evaluateAtmosphereTraining('cabin',100,9.9).category,'TRAINING_WARNING');
 assert.equal(evaluateAtmosphereTraining('spacesuit',100,40.1).category,'TRAINING_WARNING');
 for(const result of [evaluateAtmosphereTraining('cabin',100,9),evaluateAtmosphereTraining('spacesuit',100,50)]){
  assert.equal(result.synthetic,true);assert.equal(result.clinical_authority,false);
  assert.match(result.version,/illustrative|training-fixture/);
 }
});
test('missing atmospheric inputs stay insufficient and invalid values stay invalid',()=>{
 assert.equal(evaluateAtmosphereTraining('cabin',null,21).category,'TRAINING_DATA_INSUFFICIENT');
 assert.equal(evaluateAtmosphereTraining('spacesuit',29.6,null).category,'TRAINING_DATA_INSUFFICIENT');
 assert.equal(evaluateAtmosphereTraining('cabin',201,21).category,'TRAINING_INPUT_INVALID');
 assert.equal(evaluateAtmosphereTraining('spacesuit',29.6,101).category,'TRAINING_INPUT_INVALID');
 assert.throws(()=>evaluateAtmosphereTraining('eva',10,10));
});
