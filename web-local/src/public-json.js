/** Bounded retries for idempotent same-origin public build assets only. */
export async function loadPublicJson(path,fetcher=globalThis.fetch){
 if(!/^\.\/[a-z0-9-]+\.json$/i.test(path))throw Error('PUBLIC_ASSET_PATH_REQUIRED');
 let lastError;
 for(let attempt=0;attempt<3;attempt++){
  try{const response=await fetcher(path,{credentials:'omit',redirect:'error',signal:AbortSignal.timeout(20000)});if(!response.ok)throw Error(`PUBLIC_ASSET_HTTP_${response.status}`);return await response.json();}
  catch(error){lastError=error;}
 }
 throw Error(`Public offline asset unavailable: ${path}. ${lastError.message}`);
}
