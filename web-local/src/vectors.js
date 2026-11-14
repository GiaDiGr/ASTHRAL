const cacheKey='asthral-public-science-index';
export async function saveIndex(row) {
  const cache=await caches.open(cacheKey);
  await cache.put(new Request(new URL('./scientific-index',location.href)),new Response(JSON.stringify(row)));
}
export async function readIndex() {
  const cache=await caches.open(cacheKey);
  const response=await cache.match(new URL('./scientific-index',location.href));
  return response?response.json():null;
}
export function validateVector(vector) {
  if(!Array.isArray(vector)||vector.length!==384||vector.some(x=>!Number.isFinite(x))) throw Error('Invalid local embedding.');
  const norm=Math.hypot(...vector);
  if(Math.abs(norm-1)>.001) throw Error('Local embedding is not normalized.');
}
export function hybridRank(lexical,index,query,corpusHash,revision) {
  if(index.corpus!==corpusHash||index.revision!==revision||index.model!=='MiniLM-L6-ONNX-q8') throw Error('Scientific index version mismatch. Rebuild the local index.');
  validateVector(query);
  const records=new Map(index.vectors.map(row=>[row.id,row.vector]));
  if(records.size!==index.vectors.length) throw Error('Duplicate scientific vector identifiers.');
  const ranked=lexical.map((block,i)=>{
    const vector=records.get(block.id);
    validateVector(vector);
    return {block,lexical:i+1,score:vector.reduce((sum,value,j)=>sum+value*query[j],0)};
  }).sort((a,b)=>b.score-a.score||a.block.id.localeCompare(b.block.id));
  ranked.forEach((row,i)=>row.semantic=i+1);
  return ranked.sort((a,b)=>(1/(60+b.lexical)+1/(60+b.semantic))-(1/(60+a.lexical)+1/(60+a.semantic)))
    .map(row=>({...row.block,local_similarity:row.score,retrieval_algorithm:'LEXICAL_GATED_BROWSER_MINILM_RRF_1'}));
}
export function vectorRank(verified,index,query,corpusHash,revision,limit=3){
 if(index.corpus!==corpusHash||index.revision!==revision||index.model!=='MiniLM-L6-ONNX-q8')throw Error('Scientific index version mismatch.');
 validateVector(query);const eligible=new Map(verified.map(b=>[b.id,b])),seen=new Set(),ranked=[];
 for(const row of index.vectors){if(seen.has(row.id))throw Error('Duplicate scientific vector identifiers.');seen.add(row.id);validateVector(row.vector);const block=eligible.get(row.id);if(!block)throw Error('Unverified vector source.');ranked.push({...block,local_similarity:row.vector.reduce((sum,v,i)=>sum+v*query[i],0),retrieval_algorithm:'BROWSER_MINILM_VECTOR_1'});}
 return ranked.sort((a,b)=>b.local_similarity-a.local_similarity||a.id.localeCompare(b.id)).slice(0,limit);
}
export function fuseRankings(lexical,semantic,limit=3){
 const scores=new Map();for(const ranking of [lexical,semantic])ranking.forEach((block,i)=>{const prior=scores.get(block.id);scores.set(block.id,{block:prior?{...prior.block,...block}:block,score:(prior?.score??0)+1/(60+i+1)});});
 return [...scores.values()].sort((a,b)=>b.score-a.score||a.block.id.localeCompare(b.block.id)).slice(0,limit).map(x=>({...x.block,retrieval_algorithm:'BROWSER_BM25_MINILM_RRF_2'}));
}
