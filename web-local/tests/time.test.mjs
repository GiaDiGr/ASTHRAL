import test from 'node:test';
import assert from 'node:assert/strict';
import {utcInput} from '../src/time.js';
test('explicit UTC form timestamps do not acquire the device local timezone',()=>{
 for(const zone of ['UTC','America/Lima','Europe/Rome','Pacific/Auckland']){
  process.env.TZ=zone;
  assert.equal(utcInput('2026-10-16T12:00'),'2026-10-16T12:00:00.000Z');
  assert.equal(utcInput('2026-10-16T12:00:09'),'2026-10-16T12:00:09.000Z');
 }
});
test('invalid calendar dates, missing timestamps and implicit timezone strings are rejected',()=>{
 for(const value of ['','2026-02-30T12:00','2026-13-01T12:00','2026-01-01T25:00','2026-01-01T12:00:60','2026-01-01T12:00Z','2026-01-01T12:00-05:00'])assert.throws(()=>utcInput(value));
});
