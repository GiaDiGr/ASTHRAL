import test from 'node:test';import assert from 'node:assert/strict';import {projectedAngle,CycleCounter} from '../src/motion.js';
test('projected angles respect rectangular pixel geometry and abstain for absent/outside/invisible points',()=>{
 const points=[{x:.1,y:.1,visibility:.9},{x:.5,y:.5,visibility:.9},{x:.9,y:.1,visibility:.9}];const angle=projectedAngle(points,[0,1,2],200,100);assert.ok(Math.abs(angle-126.869897645844)<1e-8);assert.equal(projectedAngle([], [0,1,2],200,100),null);assert.equal(projectedAngle([{...points[0],visibility:.1},...points.slice(1)],[0,1,2],200,100),null);assert.equal(projectedAngle([{...points[0],x:-.1},...points.slice(1)],[0,1,2],200,100),null);assert.equal(projectedAngle(points,[0,1,2],0,100),null);assert.equal(projectedAngle(points,[0,1,2],200,100,NaN),null);
});
test('cycle counts require full technical hysteresis cycles and never bridge tracking loss',()=>{const c=new CycleCounter(70,150);for(const angle of [50,160,100,60,100,160])c.update(angle);assert.equal(c.count,1);for(const angle of [60,null,160])c.update(angle);assert.equal(c.count,1);for(const angle of [65,160])c.update(angle);assert.equal(c.count,2);assert.throws(()=>new CycleCounter(100,90));assert.throws(()=>new CycleCounter(NaN,150));});

test('pose worker shutdown rejects queued and future calls without leaving a hanging task',async()=>{
 const {PoseClient}=await import('../src/motion.js');const original=globalThis.Worker;
 globalThis.Worker=class{postMessage(){}terminate(){this.terminated=true;}};
 try{const client=new PoseClient();const pending=client.call('frame');client.close();await assert.rejects(pending,/POSE_WORKER_STOPPED/);await assert.rejects(client.call('install'),/POSE_WORKER_STOPPED/);assert.equal(client.pending.size,0);client.close();}finally{globalThis.Worker=original;}
});

test('pose worker permits only fixed public local assets and rejects external requests, query payloads and writes',async()=>{
 const vm=await import('node:vm'),{readFileSync}=await import('node:fs');const called=[];const self={location:{href:'http://localhost/motion-worker.js'},fetch:async(input,options)=>{called.push({input,options});return {ok:true};},postMessage(){}};
 vm.runInNewContext(readFileSync(new URL('../src/motion-worker.js',import.meta.url),'utf8'),{self,URL,Set,Promise,Error,performance:{now:()=>0}});
 await self.fetch(new URL('http://localhost/motion-runtime/manifest.json'),{headers:{'X-Synthetic-Private':'discard'}});assert.equal(called.length,1);assert.equal(called[0].options.credentials,'omit');assert.equal(Object.keys(called[0].options.headers).length,0);
 for(const [url,options] of [['https://example.com/upload',{}],['./motion-runtime/manifest.json?private=synthetic',{}],['./motion-runtime/manifest.json',{method:'POST',body:'synthetic-private'}],['./engine.zip',{}]])await assert.rejects(()=>self.fetch(url,options),/POSE_NETWORK_REQUEST_BLOCKED/);
 assert.equal(called.length,1);
});
