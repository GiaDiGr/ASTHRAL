import test from 'node:test';
import assert from 'node:assert/strict';
import {PREVENTION_FIXTURES,RADIATION_FIXTURES} from '../src/synthetic-mission.js';

test('synthetic mission walkthrough has separate prevention types and explicit fixture provenance',()=>{
 assert.deepEqual(new Set(PREVENTION_FIXTURES.map(row=>row.entry_type)),new Set(['EXERCISE_SESSION','HYDRATION','MEAL_NOTE','SLEEP','WELLBEING']));
 assert.ok(PREVENTION_FIXTURES.every(row=>row.occurred_at.endsWith('Z')&&row.label.startsWith('Synthetic')));
 assert.equal(PREVENTION_FIXTURES.some(row=>'clinical_execution' in row),false);
});

test('synthetic radiation timeline is arbitrary software data across EVA/location tags',()=>{
 assert.deepEqual(RADIATION_FIXTURES.map(row=>row[2]),['habitat','EVA','habitat']);
 assert.deepEqual(RADIATION_FIXTURES.map(row=>row[0]),[0,30,60]);
 assert.ok(RADIATION_FIXTURES.every(row=>Number.isFinite(row[1])));
});
