import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const source=(await readFile(new URL('../src/ml-worker.js',import.meta.url),'utf8')).replace("import {auditedFetch} from './network-audit.js';",'const auditedFetch=fetcher=>fetcher;');
async function requestFor(data){
 let request;const messages=[];
 const configuration={max_tokens:700,system:'Original reference system',schema:{type:'object',properties:{sentences:{type:'array'}}}};
 const fakeEngine={chat:{completions:{create:async value=>{request=value;return (async function*(){yield {choices:[{delta:{content:'{"sentences":[]}'}}]};})();}}},runtimeStatsText:async()=>'MOCK_NOT_REAL_INFERENCE'};
 const self={fetch:async url=>Response.json(url==='./models.json'?{models:[]}:configuration),postMessage:message=>messages.push(message)};
 const context=vm.createContext({self,Response,performance,fakeEngine});vm.runInContext(source,context);vm.runInContext("engine=fakeEngine;selected={id:'SYNTHETIC_TEST_MODEL'};",context);
 self.onmessage({data:{id:'synthetic',action:'generate',data:{question:'synthetic question',blocks:[],explain:true,...data}}});await vm.runInContext('queue',context);
 assert.equal(messages.at(-1).error,undefined);return {request,configuration};
}
test('browser assistant forwards the original response schema to the model runtime',async()=>{
 const {request,configuration}=await requestFor({});assert.equal(request.response_format.type,'json_object');assert.deepEqual(JSON.parse(request.response_format.schema),configuration.schema);assert.equal(request.messages[0].content,configuration.system);assert.equal(request.max_tokens,configuration.max_tokens);
});
test('typed-fact generation preserves original prepared schema, messages and token budget',async()=>{
 const schema={type:'object',properties:{sentences:{type:'array',items:{properties:{fact_id:{enum:['F-synthetic']}}}}}};
 const prepared=[{role:'system',content:'Original finite grammar'}, {role:'user',content:'Synthetic scoped facts'}];
 const {request}=await requestFor({prepared_schema:schema,prepared_messages:prepared,prepared_max_tokens:400});
 assert.deepEqual(JSON.parse(request.response_format.schema),schema);assert.deepEqual(request.messages,prepared);assert.equal(request.max_tokens,400);assert.equal(request.temperature,0);
});
