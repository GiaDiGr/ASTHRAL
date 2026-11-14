export function bounded(promise,milliseconds,message){let timer;return Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(message)),milliseconds);})]).finally(()=>clearTimeout(timer));}
export async function waitForInstall(worker,milliseconds=120000){
 if(!worker)return;
 if(['installed','activated'].includes(worker.state))return;
 if(worker.state==='redundant')throw Error('Offline installation was rejected. Check network and available browser storage.');
 await bounded(new Promise((resolve,reject)=>{const changed=()=>{if(['installed','activated'].includes(worker.state)){worker.removeEventListener('statechange',changed);resolve();}if(worker.state==='redundant'){worker.removeEventListener('statechange',changed);reject(Error('Offline installation failed integrity, network or storage checks.'));}};worker.addEventListener('statechange',changed);changed();}),milliseconds,'Offline installation timed out. Keep this page online and retry; encrypted profiles remain untouched.');
}
export async function installOffline({serviceWorker=navigator.serviceWorker,fetcher=fetch,report=()=>{},storage=navigator.storage}={}){
 if(!serviceWorker)throw Error('This browser does not expose service workers. Open the HTTPS site directly in Chrome or Safari.');
 report('Checking approved offline resources…');
 const response=await bounded(fetcher('./assets.json',{cache:'no-store'}),20000,'Could not read the application manifest. Check connectivity and retry.');if(!response.ok)throw Error('Manifest HTTP '+response.status);
 const raw=await bounded(response.arrayBuffer(),20000,'The manifest download stalled. Check connectivity and retry.'),manifest=JSON.parse(new TextDecoder().decode(raw));const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(x=>x.toString(16).padStart(2,'0')).join('');
 report('Preparing '+(manifest.files.filter(f=>!f.optional).reduce((n,f)=>n+f.size,0)/1048576).toFixed(1)+' MiB of verified application resources…');
 const registration=await bounded(serviceWorker.register('./sw.js?build='+hash,{scope:'./',updateViaCache:'none'}),20000,'Service-worker registration timed out. Open this site directly in your browser and retry.');
 await waitForInstall(registration.installing);
 if(registration.waiting&&(registration.active||serviceWorker.controller))return {update_waiting:true};
 const ready=await bounded(serviceWorker.ready,20000,'The offline worker did not activate. Reload while online, then retry.');const active=ready.active??registration.active;if(!active)throw Error('No active offline worker is available.');
 report('Verifying the installed offline cache…');
 const channel=new MessageChannel();
 const checked=await bounded(new Promise((resolve,reject)=>{channel.port1.onmessage=event=>event.data?.ok?resolve(event.data.result):reject(Error(event.data?.error??'Offline cache verification failed.'));active.postMessage({action:'ENSURE_OFFLINE'},[channel.port2]);}),120000,'Offline cache verification timed out. Retry while online; no personal records were deleted.').finally(()=>channel.port1.close());
 const persistent=await bounded(Promise.resolve().then(()=>storage?.persist?.()),3000,'Persistent storage permission timed out.').catch(()=>false);
 return {...checked,persistent:!!persistent,update_waiting:false};
}
