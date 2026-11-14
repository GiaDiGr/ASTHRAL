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
