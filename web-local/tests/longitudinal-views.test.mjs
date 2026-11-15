import test from 'node:test';
import assert from 'node:assert/strict';
import {radiationSeries} from '../src/longitudinal-views.js';
test('radiation plots never pool quantity, unit, source mode, quality or instrument',()=>{
 const row={quantity_kind:'ABSORBED_DOSE_RATE',unit:'uGy/h',value:2,timestamp:'2026-11-15T10:00:00Z',mode:'MEASURED',quality:'VALID',instrument_id:'D1',mission_segment:'EVA',location:'outside'};
 const variants=[row,{...row,mode:'SYNTHETIC'},{...row,unit:'mGy/h'},{...row,quality:'INVALID'},{...row,instrument_id:'D2'},{...row,quantity_kind:'DOSE_EQUIVALENT_RATE'}, {...row,value:3,timestamp:'2026-11-15T09:00:00Z'}];
 const groups=radiationSeries(variants);assert.equal(groups.length,6);assert.equal(groups[0].points.length,2);assert.equal(groups[0].points[0].value,3);
 assert.deepEqual(radiationSeries([{...row,value:NaN},{...row,timestamp:'unknown'}]),[]);
});
