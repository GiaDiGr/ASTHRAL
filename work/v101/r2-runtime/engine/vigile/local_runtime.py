"""Start the pinned portable runtime. No downloads, clinical credentials or tools."""
from pathlib import Path
import argparse,hashlib,json,os,secrets,socket,subprocess,time
import httpx

def start(root,mode='FULL',port=8890):
    if mode not in ('FULL','LOW_POWER'):raise ValueError('CRITICAL_DOES_NOT_START_LLM')
    folder=Path(root)/'engine/local_ai';model=folder/'Qwen3-4B-Instruct-2507-Q4_K_M.gguf';exe=folder/'llama-b11721/llama-server.exe'
    with model.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!='8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc':raise ValueError('MODEL_HASH_MISMATCH')
    with socket.socket() as sock:sock.bind(('127.0.0.1',port))
    key=folder/'runtime-key.txt'
    if not key.exists():key.write_text(secrets.token_urlsafe(32),encoding='utf-8')
    if len(key.read_text().strip())<24:raise ValueError('RUNTIME_KEY_INVALID')
    args=[str(exe),'-m',str(model),'--alias','vigile-qwen3-4b','--host','127.0.0.1','--port',str(port),'--offline','--no-webui','--no-agent','--no-webui-mcp-proxy','--api-key-file',str(key),'--cors-origins',f'http://127.0.0.1:{port}','--no-cors-credentials','--parallel','1','--ctx-size','6144' if mode=='FULL' else '3072','--threads','8' if mode=='FULL' else '4','--threads-batch','8' if mode=='FULL' else '4','--gpu-layers','99','--batch-size','512' if mode=='FULL' else '256','--ubatch-size','256' if mode=='FULL' else '128']
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','LOCALAPPDATA','APPDATA','USERPROFILE')}
    env.update(LLAMA_ARG_OFFLINE='1',HF_HUB_OFFLINE='1')
    started=time.perf_counter()
    with (folder/'runtime.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen(args,cwd=folder,stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    record={'pid':process.pid,'mode':mode,'port':port,'executable':str(exe),'model':model.name,'arguments':args,'ready':False}
    (folder/'runtime-process.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    with httpx.Client(trust_env=False,timeout=2,headers={'Authorization':'Bearer '+key.read_text().strip()}) as client:
        for _ in range(240):
            if process.poll() is not None:raise RuntimeError('RUNTIME_EXITED_SEE_LOCAL_LOG')
            try:
                response=client.get(f'http://127.0.0.1:{port}/v1/models')
                if response.status_code==200:
                    record.update(ready=True,startup_to_ready_seconds=time.perf_counter()-started)
                    (folder/'runtime-process.json').write_text(json.dumps(record,indent=2),encoding='utf-8');return record
            except httpx.HTTPError:pass
            time.sleep(.5)
    process.terminate();raise RuntimeError('RUNTIME_START_TIMEOUT')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['FULL','LOW_POWER'],default='FULL');parser.add_argument('--port',type=int,default=8890);args=parser.parse_args()
    print(json.dumps(start(Path(__file__).resolve().parents[2],args.mode,args.port),indent=2))
