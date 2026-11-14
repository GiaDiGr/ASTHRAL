"""Start the verified portable runtime. No installation, downloads or firewall changes."""
from pathlib import Path
import os, json, subprocess, time, socket
import httpx

def main():
    root=Path(__file__).resolve().parents[1]
    ai=root/'local_ai'
    exe=ai/'ollama-v0.40.6/ollama.exe'
    if not exe.is_file():
        raise SystemExit('Runtime missing: investigate antivirus history; do not restore automatically.')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',8891)) # fail closed if any process owns the port
    env={k:v for k,v in os.environ.items() if not k.upper().startswith('VIGILE_') and not any(word in k.upper() for word in ('TOKEN','SECRET','PASSWORD','API_KEY'))}
    env.update(OLLAMA_HOST='127.0.0.1:8891',OLLAMA_NO_CLOUD='1',OLLAMA_MODELS=str(ai/'ollama-models'))
    with (ai/'ollama.log').open('a',encoding='utf-8') as log:
        p=subprocess.Popen([str(exe),'serve'],env=env,cwd=ai,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    (ai/'ollama-process.json').write_text(json.dumps({'pid':p.pid,'exe':str(exe),'host':env['OLLAMA_HOST']}))
    with httpx.Client(trust_env=False,timeout=2) as client:
        for _ in range(60):
            if p.poll() is not None:raise SystemExit('Runtime stopped; inspect local_ai/ollama.log')
            try:
                r=client.get('http://127.0.0.1:8891/api/version');r.raise_for_status()
                print(json.dumps({'pid':p.pid,'version':r.json(),'cloud_enabled':False}));return
            except httpx.HTTPError:time.sleep(.5)
    raise SystemExit('Runtime startup timeout; inspect log before retrying')

if __name__=='__main__':main()

