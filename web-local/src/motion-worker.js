/* Pose-only browser adaptation. Original native Holistic code remains unchanged. */
const originalFetch=self.fetch.bind(self);
const publicRoot=new URL('./motion-runtime/',self.location.href);
const publicAssets=new Set(['manifest.json','pose_landmarker_lite.task','vision_bundle.mjs','wasm/vision_wasm_internal.js','wasm/vision_wasm_internal.wasm','wasm/vision_wasm_nosimd_internal.js','wasm/vision_wasm_nosimd_internal.wasm']);
self.fetch=(input,options={})=>{const target=new URL(typeof input==='string'||input instanceof URL?String(input):input.url,self.location.href);const method=options.method??input.method??'GET';const relative=target.pathname.slice(publicRoot.pathname.length);if(method!=='GET'||options.body!=null||target.origin!==publicRoot.origin||!target.pathname.startsWith(publicRoot.pathname)||!publicAssets.has(relative)||target.search||target.hash) return Promise.reject(Error('POSE_NETWORK_REQUEST_BLOCKED'));return originalFetch(target.href,{...options,method:'GET',headers:{},credentials:'omit',redirect:'error',referrer:'',referrerPolicy:'no-referrer',mode:'same-origin'});};
const MODEL_SHA='59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a';
let detector=null,lastTimestamp=-1;
const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
async function install(){
 const manifestResponse=await fetch('./motion-runtime/manifest.json');if(!manifestResponse.ok)throw Error('POSE_OPTIONAL_ASSETS_NOT_INSTALLED');const manifest=await manifestResponse.json();
 if(manifest.version!=='0.10.21'||manifest.model_sha256!==MODEL_SHA)throw Error('POSE_MANIFEST_UNSUPPORTED');
 let model;
 for(const asset of manifest.files){if(!/^[a-zA-Z0-9_./-]+$/.test(asset.path)||asset.path.includes('..'))throw Error('POSE_ASSET_PATH_INVALID');const response=await fetch('./motion-runtime/'+asset.path);if(!response.ok)throw Error('POSE_ASSET_MISSING');const bytes=await response.arrayBuffer();if(bytes.byteLength!==asset.size||await digest(bytes)!==asset.sha256)throw Error('POSE_ASSET_INTEGRITY_FAILED');if(asset.path==='pose_landmarker_lite.task')model=new Uint8Array(bytes);}
 if(!model||await digest(model)!==MODEL_SHA)throw Error('POSE_MODEL_INTEGRITY_FAILED');
 const {FilesetResolver,PoseLandmarker}=await import('./motion-runtime/vision_bundle.mjs');
 const vision=await FilesetResolver.forVisionTasks(new URL('./motion-runtime/wasm',self.location.href).href);
 detector?.close();detector=await PoseLandmarker.createFromOptions(vision,{baseOptions:{modelAssetBuffer:model,delegate:'CPU'},runningMode:'VIDEO',numPoses:1});lastTimestamp=-1;
 return {model:'MediaPipe Pose Landmarker Lite',runtime:'0.10.21',model_sha256:MODEL_SHA,delegate:'CPU',clinical_validation:false};
}
let queue=Promise.resolve();self.onmessage=({data})=>{queue=queue.then(async()=>{const {id,action,bitmap,timestamp}=data;try{let result;if(action==='install')result=await install();else if(action==='frame'){if(!detector)throw Error('POSE_MODEL_NOT_READY');if(!Number.isFinite(timestamp)||timestamp<=lastTimestamp)throw Error('POSE_FRAME_TIME_NOT_INCREASING');lastTimestamp=timestamp;const start=performance.now();const prediction=detector.detectForVideo(bitmap,timestamp);result={landmarks:prediction.landmarks,inference_ms:performance.now()-start,timestamp};}else throw Error('POSE_ACTION_UNSUPPORTED');self.postMessage({id,result});}catch(error){self.postMessage({id,error:String(error).slice(0,800)});}finally{bitmap?.close();}});};
