export const PRIVATE_SENTINEL='ASTHRAL_SYNTHETIC_PRIVATE_SENTINEL_20261114';
export function auditedFetch(nativeFetch,report){
 return (input,options={})=>{
  const raw=typeof input==='string'||input instanceof URL?String(input):input.url;
  const method=String(options.method??input?.method??'GET').toUpperCase();
  const contains_sentinel=raw.includes(PRIVATE_SENTINEL)||String(options.body??'').includes(PRIVATE_SENTINEL);
  const url=new URL(raw,globalThis.location?.href??'https://asthral.invalid/');
  report({method,origin:url.origin,path:contains_sentinel?'[redacted]':url.pathname,contains_sentinel,blocked:contains_sentinel||method!=='GET'||!!options.body});
  if(contains_sentinel||method!=='GET'||options.body)return Promise.reject(Error('Private sentinel or network write blocked. Personal data belong in local storage.'));
  return nativeFetch(input,options);
 };
}
