/* Reference clinical computation runs only inside this worker. */
importScripts('./runtime/pyodide.js');
let runtime;
const started=performance.now();
const ready=(async()=>{
 runtime=await loadPyodide({indexURL:new URL('./runtime/',self.location.href).href});
 // loadPackage may resolve even when a package download failed. Confirm imports
 // and retry transient transport failures twice before blocking the engine.
 let dependenciesReady=false,lastDependencyError;
 for(let attempt=0;attempt<3;attempt++){
  try{await runtime.loadPackage(['pydantic','sqlite3']);runtime.runPython('import pydantic, sqlite3');dependenciesReady=true;break;}
  catch(error){lastDependencyError=error;}
 }
 if(!dependenciesReady)throw Error('LOCAL_DEPENDENCY_LOAD_FAILED: '+String(lastDependencyError));
 const data=await (await fetch('./engine.zip')).arrayBuffer();
 runtime.unpackArchive(new Uint8Array(data),'zip',{extractDir:'/app'});
 await runtime.runPythonAsync("import sys\nsys.path.insert(0,'/app')\nimport browser_bridge, json");
 self.postMessage({type:'ready',seconds:(performance.now()-started)/1000,python:runtime.runPython('sys.version')});
})();
let queue=Promise.resolve();
self.onmessage=event=>{
 const {id,action,data}=event.data;
 queue=queue.then(async()=>{
  try{
   await ready;
   runtime.globals.set('_action',action);
   runtime.globals.set('_input',JSON.stringify(data??{}));
   const start=performance.now();
   const raw=await runtime.runPythonAsync("__import__('json').dumps(browser_bridge.dispatch(_action,__import__('json').loads(_input)),ensure_ascii=False)");
   self.postMessage({id,result:JSON.parse(raw),seconds:(performance.now()-start)/1000});
  }catch(error){self.postMessage({id,error:String(error).slice(-2500)});}
 });
};
ready.catch(error=>self.postMessage({type:'failed',error:String(error)}));
