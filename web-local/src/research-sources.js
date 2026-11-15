const text=(value,max)=>typeof value==='string'&&value.trim()&&value.length<=max?value.trim():null;
const EXACT_HOSTS=new Set(['doi.org','thesai.org','cris.utec.edu.pe','proceedings.com','www.proceedings.com','ieeexplore.ieee.org','analog.com','www.analog.com']);
const MODULES=new Set(['prevention','radiation','space-weather','eva','agriculture','clinical']);
const allowedHost=host=>host==='nasa.gov'||host.endsWith('.nasa.gov')||host==='usda.gov'||host.endsWith('.usda.gov')||EXACT_HOSTS.has(host);
const trustedUrl=value=>{try{const url=new URL(value);return url.protocol==='https:'&&allowedHost(url.hostname.toLowerCase())&&url.username===''&&url.password===''?url.href:null;}catch{return null;}};
const textList=(value,{maxItems=24,maxLength=240}={})=>Array.isArray(value)?value.slice(0,maxItems).map(item=>text(item,maxLength)).filter(Boolean):[];
const doiValue=value=>typeof value==='string'&&/^10\.\d{4,9}\/[A-Z0-9._;()/:+-]+$/i.test(value.trim())&&value.length<=180?value.trim():null;

export function normalizeSourceRegistry(raw){
 if(!raw||typeof raw!=='object'||raw.schema_version!=='1.0.0'||!Array.isArray(raw.sources)||raw.sources.length>100)throw Error('Invalid local source registry.');
 const seen=new Set(),sources=[];
 for(const item of raw.sources){
  if(!item||typeof item!=='object')continue;
  const source_id=text(item.source_id,100),institution=text(item.institution,200),title=text(item.title,500),publication_date=text(item.publication_date,180),url=trustedUrl(item.url),evidence_category=text(item.evidence_category,160),reuse_status=text(item.reuse_status,160);
  if(!source_id||seen.has(source_id)||!institution||!title||!publication_date||!url||!evidence_category||!reuse_status)continue;
  seen.add(source_id);
  const modules=textList(item.modules,{maxItems:8,maxLength:32}).filter(value=>MODULES.has(value));
  const metadata_source_url=trustedUrl(item.metadata_source_url);
  const access_url=trustedUrl(item.access_url);
  const review_policy_url=trustedUrl(item.review_policy_url);
  sources.push({source_id,institution,title,publication_date,url,evidence_category,reuse_status,
   authors:textList(item.authors,{maxItems:24,maxLength:160}),doi:doiValue(item.doi),
   topics:textList(item.topics,{maxItems:24,maxLength:120}),summary_claim_ids:textList(item.summary_claim_ids,{maxItems:32,maxLength:100}),
   modules,suggested_citation:text(item.suggested_citation,1400),source_scope:text(item.source_scope,1200),
   evidence_limitations:text(item.evidence_limitations,1600),metadata_note:text(item.metadata_note,1000),
   metadata_source_url,access_url,review_policy_url,review_status:text(item.review_status,180)});
 }
 if(!sources.length)throw Error('No reviewed references are available.');
 return {schema_version:raw.schema_version,reviewed_at:text(raw.reviewed_at,40)||'UNKNOWN',sources};
}

export function sourcesForModule(registry,module=null){
 if(!registry||!Array.isArray(registry.sources))throw Error('Invalid normalized source registry.');
 if(module===null)return registry.sources;
 if(!MODULES.has(module))throw Error('Unknown source module.');
 return registry.sources.filter(source=>source.modules.includes(module));
}
