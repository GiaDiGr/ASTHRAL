from pathlib import Path
import base64, json, os, subprocess, sys, time
import httpx
root = Path(__file__).resolve().parents[2]
engine = root/'engine'
sys.path.insert(0, str(engine))
sys.path.insert(0, str(engine/'tools'))
from vigile.mission_demo import prepare, SUBJECTS, MID
from vigile.knowledge_v08 import SOURCES, build
from vigile.voice import LocalVoice
from demo_asthral import personal

folder = engine/'data'/'asthral-v120-vector-smoke'
passwords = ('fixture-only alpha passphrase', 'fixture-only bravo passphrase')
backend_url = 'http://127.0.0.1:8931'
portal_url = 'http://127.0.0.1:8932'
env = {k:v for k,v in os.environ.items() if not k.startswith('VIGILE_')}
backend_env = dict(env, VIGILE_DB=str(folder/'vigile.sqlite3'), VIGILE_TOKEN_FILE=str(folder/'server-tokens.json'))
def spawn(args, child_env):
    return subprocess.Popen([sys.executable, *args], cwd=engine, env=child_env,
                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def portal():
    return spawn(['-m','vigile.portal','--config',str(folder/'portal-config.json'),'--port','8932'],env)
def wait():
    for _ in range(100):
        try:
            if httpx.get(portal_url+'/auth-mode',timeout=.5,trust_env=False).is_success:
                return
        except httpx.HTTPError:
            pass
        time.sleep(.1)
    raise RuntimeError('Portal unavailable')
def post(c, path, **data):
    return c.post('/api/'+path,json=data,headers={'Origin':portal_url})
def login(client, name, password):
    post(client,'login',username=name,password=password).raise_for_status()
backend = spawn(['-m','uvicorn','vigile.api:create_app','--factory','--host','127.0.0.1','--port','8931','--no-access-log'],backend_env)
p = portal()
try:
    wait()
    voice=LocalVoice()
    try:
        audio,_=voice.synthesize('Record my exercise duration as twenty minutes in the past twenty four hours.','en')
    finally:
        voice.close()
    with httpx.Client(base_url=portal_url,timeout=90,trust_env=False) as a:
        login(a,'crew-alpha',passwords[0])
        capture=post(a,'voice/health-capture',capture_id='real-exercise-sapi',auto_save=True,
                     audio_base64=base64.b64encode(audio).decode()).raise_for_status().json()
        print('REAL_AUTO_VOICE',json.dumps({k:capture.get(k) for k in ('status','confidence','transcript','observation')}),flush=True)
        question=post(a,'assistant',monitoring_id='mission-crew-A-cycle-35',question='Compare the recorded aerobic capacity and its baseline')
        answer=question.raise_for_status().json()
        print('REAL_ASSISTANT',json.dumps({k:answer.get(k) for k in ('status','inference_trace','failure_trace')}),flush=True)
finally:
    for child in (p,backend):
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=10)
