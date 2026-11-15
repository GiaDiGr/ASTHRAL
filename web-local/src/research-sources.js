const text=(value,max)=>typeof value==='string'&&value.trim()&&value.length<=max?value.trim():null;
const trustedUrl=value=>{try{const url=new URL(value);const official=(url.hostname==='nasa.gov'||url.hostname.endsWith('.nasa.gov')||url.hostname==='usda.gov'||url.hostname.endsWith('.usda.gov'));return url.protocol==='https:'&&official&&url.username===''&&url.password===''?url.href:null;}catch{return null;}};

export function normalizeSourceRegistry(raw){
 if(!raw||typeof raw!=='object'||raw.schema_version!=='1.0.0'||!Array.isArray(raw.sources)||raw.sources.length>100)throw Error('Invalid local source registry.');
 const seen=new Set(),sources=[];
 for(const item of raw.sources){
  if(!item||typeof item!=='object')continue;
  const source_id=text(item.source_id,100),institution=text(item.institution,200),title=text(item.title,500),publication_date=text(item.publication_date,180),url=trustedUrl(item.url),evidence_category=text(item.evidence_category,120),reuse_status=text(item.reuse_status,120);
  if(!source_id||seen.has(source_id)||!institution||!title||!publication_date||!url||!evidence_category||!reuse_status)continue;
  seen.add(source_id);sources.push({source_id,institution,title,publication_date,url,evidence_category,reuse_status});
 }
 if(!sources.length)throw Error('No reviewed official references are available.');
 return {schema_version:raw.schema_version,reviewed_at:text(raw.reviewed_at,40)||'UNKNOWN',sources};
}
