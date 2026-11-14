import test from 'node:test';
import assert from 'node:assert/strict';
import {validateVector,hybridRank} from '../src/vectors.js';
const unit=i=>Array.from({length:384},(_,j)=>Number(i===j));
const index={model:'MiniLM-L6-ONNX-q8',revision:'r1',corpus:'hash',vectors:[{id:'a',vector:unit(0)},{id:'b',vector:unit(1)}]};
const lexical=[{id:'a',text:'verified a'},{id:'b',text:'verified b'}];
test('hybrid reranking never admits a source absent from verified lexical candidates',()=>{
  const result=hybridRank(lexical,index,unit(1),'hash','r1');
  assert.deepEqual(new Set(result.map(x=>x.id)),new Set(['a','b']));
  assert.ok(result.every(x=>x.retrieval_algorithm==='LEXICAL_GATED_BROWSER_MINILM_RRF_1'));
  assert.equal(result.find(x=>x.id==='b').local_similarity,1);
});
test('stale or malformed public indexes fail closed to the caller fallback',()=>{
  assert.throws(()=>hybridRank(lexical,index,unit(1),'changed','r1'),/version mismatch/);
  assert.throws(()=>hybridRank(lexical,index,unit(1),'hash','changed'),/version mismatch/);
  assert.throws(()=>validateVector([1]),/Invalid/);
  assert.throws(()=>validateVector(Array(384).fill(NaN)),/Invalid/);
  assert.throws(()=>validateVector(Array(384).fill(0)),/normalized/);
  assert.throws(()=>hybridRank(lexical,{...index,vectors:[index.vectors[0],index.vectors[0]]},unit(1),'hash','r1'),/Duplicate/);
});
