import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import assert from 'node:assert/strict';

const require=createRequire(import.meta.url);
const {loadPyodide}=require('../dist/runtime/pyodide.js');
const runtime=await loadPyodide({indexURL:fileURLToPath(new URL('../dist/runtime/',import.meta.url))});
await runtime.loadPackage(['pydantic','sqlite3']);
runtime.unpackArchive(new Uint8Array(await readFile(new URL('../dist/engine.zip',import.meta.url))),'zip',{extractDir:'/app'});
await runtime.runPythonAsync("import sys,json\nsys.path.insert(0,'/app')\nimport browser_bridge");
async function call(action,data={}) {
  runtime.globals.set('_action',action);
  runtime.globals.set('_input',JSON.stringify(data));
  return JSON.parse(await runtime.runPythonAsync("json.dumps(browser_bridge.dispatch(_action,json.loads(_input)))"));
}
const cases=JSON.parse(await readFile(new URL('../dist/parity-cases.json',import.meta.url),'utf8'));
let parity;
test('all browser WASM clinical outputs match CPython reference fixtures exactly',async()=>{
  parity=await call('parity',{cases});
  assert.equal(parity.matched,cases.length);
  assert.deepEqual(parity.failures,[]);
});
test('SQLite serialization preserves audits and blocks foreign profile recovery',async()=>{
  await call('init_profile',{id:'profile-wasm-test'});
  const evaluated=await call('evaluate',{snapshot:cases.find(row=>row.id==='DM-05').snapshot});
  assert.equal(evaluated.output.results.DKA.diagnostic_status,'CRITERIA_MET');
  assert.ok(evaluated.output.results.DKA.required_for_protocol_safety.includes('potassium_mmol_l'));
  const database=await call('serialize');
  await assert.rejects(call('init_profile',{id:'profile-foreign',database}));
  await call('init_profile',{id:'profile-wasm-test',database});
  const restored=await call('history');
  assert.equal(restored.evaluations.length,1);
  assert.ok(restored.audit_valid);
  await call('init_profile',{id:'profile-second'});
  assert.equal((await call('history')).evaluations.length,0);
});
test('reference baseline and trend calculations run in real WASM',async()=>{
  const samples=JSON.parse(await readFile(new URL('../dist/statistics-cases.json',import.meta.url),'utf8'));
  assert.ok(samples.length);
  for(const sample of samples) {
    const result=await call('statistics',{sample});
    assert.equal(result.reference_matches,true);
    assert.equal(result.diagnosis,null);
  }
  const invalid=structuredClone(samples[0]);
  invalid.snapshots[0].measurement.reported_quality='INVALID';
  await assert.rejects(call('statistics',{sample:invalid}),/INCONCLUSIVE/);
});
test('original voice parser extracts measurements without inventing missing units',async()=>{
  const valid=await call('parse_observation',{text:'my heart rate is eighty two beats per minute'});
  assert.deepEqual(valid.observation.values,[82]);
  assert.equal((await call('parse_observation',{text:'Do I need to record my glucose?'})).observation,null);
  const missing=await call('parse_observation',{text:'record my heart rate as 82'});
  assert.equal(missing.observation.structured,false);
});
test.after(async()=>{
  await writeFile(new URL('../../work/browser-local/wasm-parity-report.json',import.meta.url),JSON.stringify(parity,null,2));
});
