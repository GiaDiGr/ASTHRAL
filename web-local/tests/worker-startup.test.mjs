import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../src/worker.js',import.meta.url),'utf8');
async function run(failures){
 let attempts=0,unpacked=0;const messages=[];
 const runtime={loadPackage:async()=>{attempts++},runPython:(code)=>{if(code.includes('import pydantic')&&attempts<=failures)throw Error('missing package');return 'synthetic runtime';},unpackArchive:()=>{unpacked++},runPythonAsync:async()=>{}};
 vm.runInNewContext(source,{importScripts:()=>{},loadPyodide:async()=>runtime,URL,performance:{now:()=>0},self:{location:{href:'http://localhost/worker.js'},postMessage:m=>messages.push(m)},fetch:async()=>({arrayBuffer:async()=>new ArrayBuffer(0)}),Uint8Array,Error,Promise,String,JSON});
 for(let n=0;n<30;n++)await Promise.resolve();return {attempts,unpacked,messages};
}
test('worker verifies actual imports when package loader silently resolves and retries bounded failures',async()=>{const r=await run(1);assert.equal(r.attempts,2);assert.equal(r.unpacked,1);assert.ok(r.messages.some(m=>m.type==='ready'));});
test('incomplete dependencies never expose a ready clinical engine or unpack app after retry budget',async()=>{const r=await run(3);assert.equal(r.attempts,3);assert.equal(r.unpacked,0);assert.ok(r.messages.some(m=>m.type==='failed'&&m.error.includes('LOCAL_DEPENDENCY_LOAD_FAILED')));assert.ok(!r.messages.some(m=>m.type==='ready'));});
