"""Verify actual loopback HTTP startup, authenticated contracts, and shutdown."""
import subprocess,sys,time,json,urllib.request,urllib.error,socket
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with socket.socket() as s:
    s.bind(('127.0.0.1',0));port=s.getsockname()[1]
log=root.parent/'docs/server-smoke.log'
with log.open('w',encoding='utf-8') as stream:
    proc=subprocess.Popen([sys.executable,'-m','vigile','serve','--port',str(port)],cwd=root,
       stdout=stream,stderr=stream,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        for i in range(100):
            try:
                health=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=1));break
            except (OSError,urllib.error.URLError):
                if proc.poll() is not None: raise RuntimeError('Server exited; inspect server-smoke.log')
                time.sleep(.1)
        else: raise RuntimeError('Server startup timed out')
        tokens=json.loads((root/'data/client-credentials.json').read_text())
        reader=next(k for k,v in tokens.items() if v=='reader')
        req=urllib.request.Request(f'http://127.0.0.1:{port}/catalog/conditions',headers={'Authorization':'Bearer '+reader})
        conditions=json.load(urllib.request.urlopen(req,timeout=5))
        assert len(conditions)==44 and health['clinical_execution']=='BLOCKED'
        print('Actual loopback server: health OK, authenticated catalog 44, shutdown OK')
    finally:
        proc.terminate();proc.wait(timeout=10)
