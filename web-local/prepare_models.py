"""Prepare reviewed browser inference runtimes and pinned public model metadata."""
from pathlib import Path
import base64
import hashlib
import httpx
import io
import json
import ssl
import tarfile

HERE=Path(__file__).resolve().parent
MODELS=[
 ('mlc-ai/Qwen3-4B-q4f16_1-MLC','a5c9fab855e3ccbdfed2e7e69683d75f30332161','Qwen3-4B-q4f16_1-ctx4k_cs1k-webgpu.wasm',3432),
 ('mlc-ai/Qwen2.5-0.5B-Instruct-q4f16_1-MLC','32ff081fe7e4dfe4ffb167b94c66fdf11e02b8ad','Qwen2-0.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm',945),
]
LIB_REVISION='146ed9cd4b4062e967b017fd2291f7106b50599f'
MINILM_REVISION='751bff37182d3f1213fa05d7196b954e230abad9'

def main():
    lock_path=HERE/'runtime-lock.json'
    previous=json.loads(lock_path.read_bytes()) if lock_path.exists() else {}
    lock={key:value for key,value in previous.items() if key not in ("@mlc-ai/web-llm","@huggingface/transformers")}
    records=[]
    with httpx.Client(verify=ssl.create_default_context(),trust_env=False,timeout=60,follow_redirects=True) as client:
        for package,version,files in [
            ('@mlc-ai/web-llm','0.2.79',{'lib/index.js':'webllm.js','LICENSE':'WEBLLM_LICENSE.txt'}),
            ('@huggingface/transformers','3.8.1',{name:'embedding-runtime/'+name.split('/')[-1] for name in [
                'dist/transformers.min.js','dist/ort-wasm-simd-threaded.jsep.mjs','dist/ort-wasm-simd-threaded.jsep.wasm']} | {'LICENSE':'TRANSFORMERS_LICENSE.txt'}),
        ]:
            metadata=client.get('https://registry.npmjs.org/'+package+'/'+version).raise_for_status().json()
            expected=previous.get(package,{}).get('integrity') if previous.get(package,{}).get('version')==version else metadata['dist']['integrity']
            raw=client.get(metadata['dist']['tarball']).raise_for_status().content
            actual='sha512-'+base64.b64encode(hashlib.sha512(raw).digest()).decode()
            if actual!=expected:raise ValueError('NPM_PACKAGE_INTEGRITY_FAILED')
            lock[package]={'version':version,'integrity':expected,'url':metadata['dist']['tarball']}
            with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
                for filename,target in files.items():
                    destination=HERE/(target if target.endswith('LICENSE.txt') else 'src/'+target)
                    destination.parent.mkdir(exist_ok=True)
                    destination.write_bytes(archive.extractfile('package/'+filename).read())
        for repo,revision,wasm,vram in MODELS:
            metadata=client.get('https://huggingface.co/api/models/'+repo+'/revision/'+revision,params={'blobs':'true'}).raise_for_status().json()
            if metadata['sha']!=revision:raise ValueError('MODEL_REVISION_MISMATCH')
            prefix='https://huggingface.co/'+repo+'/resolve/'+revision+'/'
            files=[]
            for item in metadata['siblings']:
                name=item['rfilename']
                if name.endswith('.bin') or name in ['mlc-chat-config.json','ndarray-cache.json','tokenizer.json','tokenizer_config.json','merges.txt','vocab.json']:
                    digest=item.get('lfs',{}).get('sha256')
                    if not digest:digest=hashlib.sha256(client.get(prefix+name).raise_for_status().content).hexdigest()
                    files.append({'url':prefix+name,'sha256':digest,'size':item['size']})
            wasm_url='https://raw.githubusercontent.com/mlc-ai/binary-mlc-llm-libs/'+LIB_REVISION+'/web-llm-models/v0_2_48/'+wasm
            data=client.get(wasm_url).raise_for_status().content
            files.append({'url':wasm_url,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)})
            records.append({'id':repo.split('/')[-1],'model':prefix,'model_lib':wasm_url,'files':files,
                            'bytes':sum(f['size'] for f in files),'license':'Apache-2.0','source_revision':revision,
                            'runtime':'WebLLM-0.2.79','vram_mb':vram})
        repo='Xenova/all-MiniLM-L6-v2'
        metadata=client.get('https://huggingface.co/api/models/'+repo+'/revision/'+MINILM_REVISION,params={'blobs':'true'}).raise_for_status().json()
        prefix='https://huggingface.co/'+repo+'/resolve/'+MINILM_REVISION+'/'
        files=[]
        for item in metadata['siblings']:
            name=item['rfilename']
            if name in ['config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','onnx/model_quantized.onnx']:
                digest=item.get('lfs',{}).get('sha256') or hashlib.sha256(client.get(prefix+name).raise_for_status().content).hexdigest()
                files.append({'url':prefix+name,'sha256':digest,'size':item['size']})
        records.append({'id':'MiniLM-L6-ONNX-q8','model':repo,'revision':MINILM_REVISION,'files':files,
                        'bytes':sum(f['size'] for f in files),'license':'Apache-2.0','runtime':'Transformers.js-3.8.1','dimensions':384})
    (HERE/'src/models.json').write_text(json.dumps({'models':records},indent=2),encoding='utf8')
    lock_path.write_text(json.dumps(lock,indent=2),encoding='utf8')
    print(json.dumps([{'id':r['id'],'bytes':r['bytes'],'files':len(r['files'])} for r in records]))

if __name__=='__main__':main()
