import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const source=await readFile(new URL('../voice_csp_glue.js',import.meta.url),'utf8');
const load=extra=>vm.runInNewContext('"use strict";'+source+';({createNamedFunction,craftInvokerFunction,__emval_get_method_caller})',{makeLegalFunctionName:name=>name.replace(/[^a-z0-9_]/gi,'_'),throwBindingError:message=>{throw Error(message);},runDestructors:stack=>{while(stack.length){const pointer=stack.pop();stack.pop()(pointer);}},...extra},{codeGeneration:{strings:false,wasm:false}});
test('CSP-safe ABI wrappers preserve receiver, conversions, arity gates and destructor cleanup',()=>{
 const destroyed=[];const glue=load();
 const type={name:'int',toWireType:(stack,value)=>value+1,fromWireType:value=>value*2,destructorFunction:value=>destroyed.push(value)};
 const klass={name:'class',toWireType:(stack,self)=>self.pointer,destructorFunction:null};
 const fn=glue.craftInvokerFunction('Model::method',[type,klass,type],{},(target,self,value)=>target+self+value,100);
 assert.equal(fn.call({pointer:5},3),218);assert.deepEqual(destroyed,[4]);
 assert.throws(()=>fn.call({pointer:5}),/expected 1/);
});
test('CSP-safe ABI wrappers preserve dynamic destructor-stack and emval method calling',()=>{
 const destroyed=[];const lookup=[{isVoid:false,toWireType:(stack,value)=>value*3},{argPackAdvance:8,readValueFromPointer:pointer=>pointer,deleteObject:value=>destroyed.push(value)}];let caller;
 const glue=load({__emval_lookupTypes:()=>lookup,__emval_addMethodCaller:fn=>{caller=fn;return 42;}});
 assert.equal(glue.__emval_get_method_caller(2,0),42);assert.equal(caller({offset:2,sum(value){return value+this.offset;}},'sum',[],10),36);assert.deepEqual(destroyed,[10]);
 const type={name:'int',toWireType:(stack,value)=>{stack.push(value=>destroyed.push(value),value);return value;},fromWireType:value=>value};
 const fn=glue.craftInvokerFunction('sum',[type,null,type],null,(target,value)=>target+value,7);
 assert.equal(fn(3),10);assert.equal(destroyed.at(-1),3);
});

test('generated speech runtime contains the reviewed CSP-safe wrappers',async()=>{
 const runtime=await readFile(new URL('../src/vosk.js',import.meta.url),'utf8');
 const encoded=runtime.match(/createBase64WorkerFactory\('([A-Za-z0-9+/=]+)'/);
 assert.ok(encoded,'embedded worker must be inspectable');
 const worker=Buffer.from(encoded[1],'base64').toString('utf8');
 assert.doesNotMatch(worker,/new\s+Function\s*\(|new_\s*\(\s*Function|\beval\s*\(/);
 for(const name of ['createNamedFunction','craftInvokerFunction','__emval_get_method_caller'])assert.ok(worker.includes('// END '+name));
 assert.ok(worker.includes('asthral_final: true'));
});
