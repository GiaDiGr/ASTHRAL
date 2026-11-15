import test from 'node:test';
import assert from 'node:assert/strict';
import {parseRadiationCsv,RADIATION_CSV_COLUMNS} from '../src/radiation-csv.js';

const header=RADIATION_CSV_COLUMNS.join(',');
const row='ABSORBED_DOSE_RATE,1.25,uGy/h,2026-11-15T10:00:00Z,SYNTHETIC,UNKNOWN,demo-eva,fixture-site,synthetic-fixture,fixture-device,,,"test, note"';

test('radiation CSV parses fixed schema, optional device and quoted note',()=>{
 const result=parseRadiationCsv(header+'\n'+row+'\n');assert.equal(result.length,1);assert.equal(result[0].value,'1.25');assert.equal(result[0].instrument_id,'fixture-device');assert.equal(result[0].note,'test, note');assert.equal(result[0].mode,'SYNTHETIC');
});

test('radiation CSV rejects unknown columns, inconsistent rows, duplicate headers and malformed quotes',()=>{
 assert.throws(()=>parseRadiationCsv('value,unit\n1,uGy/h'),/header/);
 assert.throws(()=>parseRadiationCsv(header+'\n1,2'),/fields/);
 assert.throws(()=>parseRadiationCsv(header.replace('unit','value')+'\n'+row),/duplicate column/);
 assert.throws(()=>parseRadiationCsv(header+'\n'+row.replace('"test, note"','"unterminated')),/unterminated/);
});

test('radiation CSV bounds input size and rejects empty files',()=>{
 assert.throws(()=>parseRadiationCsv(''),/empty/);
 assert.throws(()=>parseRadiationCsv('x'.repeat(5_000_001)),/5 MB/);
});
