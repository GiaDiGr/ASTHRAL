import test from 'node:test';
import assert from 'node:assert/strict';
import {waitForInstall,installOffline} from '../src/offline-install.js';
class Installer extends EventTarget{state='installing';move(state){this.state=state;this.dispatchEvent(new Event('statechange'));}}
test('offline installation follows actual worker state transitions and reports failures',async()=>{
 const success=new Installer();const done=waitForInstall(success,1000);success.move('installed');await done;
 const failed=new Installer();const rejected=waitForInstall(failed,1000);failed.move('redundant');await assert.rejects(rejected,/failed/);
 await assert.rejects(waitForInstall(new Installer(),5),/timed out/);
});
test('offline success requires an active worker cache-verification acknowledgment',async()=>{
 const report=[];let registered=false,verified=false;
 const active={postMessage(message,ports){assert.equal(message.action,'ENSURE_OFFLINE');verified=true;ports[0].postMessage({ok:true,result:{files:17,bytes:12345}});ports[0].close();}};
 const registration={installing:null,waiting:null,active};
 const serviceWorker={controller:null,register:async(url,options)=>{assert.match(url,/sw.js\?build=[a-f0-9]{64}$/);assert.equal(options.updateViaCache,'none');registered=true;return registration;},ready:Promise.resolve(registration)};
 const result=await installOffline({serviceWorker,fetcher:async()=>Response.json({files:[{optional:false,size:12345}]}),storage:{persist:async()=>false},report:text=>report.push(text)});
 assert.equal(registered,true);assert.equal(verified,true);assert.equal(result.files,17);assert.equal(result.persistent,false);assert.ok(report.length>=3);
});
test('existing active worker plus waiting update never produces a false ready result',async()=>{
 const registration={installing:null,waiting:{state:'installed'},active:{}};
 const serviceWorker={controller:null,register:async()=>registration,ready:new Promise(()=>{})};
 const result=await installOffline({serviceWorker,fetcher:async()=>Response.json({files:[]}),storage:{}});
 assert.equal(result.update_waiting,true);
});

test('storage permission failure does not discard a verified offline installation',async()=>{
 const active={postMessage(message,ports){ports[0].postMessage({ok:true,result:{files:49}});ports[0].close();}};
 const registration={active};
 const result=await installOffline({serviceWorker:{register:async()=>registration,ready:Promise.resolve(registration)},fetcher:async()=>Response.json({files:[]}),storage:{persist:async()=>{throw Error('Permission denied');}}});
 assert.equal(result.files,49);assert.equal(result.persistent,false);
});
test('cache verification failure cannot be reported as offline readiness',async()=>{
 const active={postMessage(message,ports){ports[0].postMessage({ok:false,error:'SHA-256 mismatch'});ports[0].close();}};
 const registration={active};
 await assert.rejects(installOffline({serviceWorker:{register:async()=>registration,ready:Promise.resolve(registration)},fetcher:async()=>Response.json({files:[]}),storage:{}}),/SHA-256 mismatch/);
});
