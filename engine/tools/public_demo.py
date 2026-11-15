"""Operate an isolated synthetic Quick Tunnel demo. No Windows autostart."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import time
import ssl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'engine'))
from vigile.local_protection import protect_secret, read_secret, restrict_directory

FOLDER = ROOT/'engine/data/cloudflare-public-demo'
STATE = FOLDER/'processes.json'
ORIGIN = FOLDER/'public-origin.txt'
BINARY = ROOT/'work/cloudflare/cloudflared.exe'
BINARY_HASH = 'd5c1d82031da6253dcdcff64c944cd0fe063016edeb2e4fd088075fc9bd52d0a'
BACKEND_PORT = 8951
PORTAL_PORT = 8952

def save(value):
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf8')
    temporary.replace(STATE)

def state():
    return json.loads(STATE.read_text(encoding='utf8')) if STATE.exists() else {}

def alive(item):
    if not item:
        return False
    import ctypes
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, item['pid'])
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)

def spawn(name, args, env=None):
    log = FOLDER/(name+'.log')
    with log.open('ab') as output:
        process = subprocess.Popen(args, cwd=ROOT/'engine', env=env,
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    # Creation time prevents accidental termination of a recycled PID.
    import psutil
    return {'pid': process.pid, 'created': psutil.Process(process.pid).create_time(), 'name': name}

def stop_one(item):
    if not item:
        return
    import psutil
    try:
        process = psutil.Process(item['pid'])
        if process.create_time() != item['created']:
            raise RuntimeError('PID_REUSED_REFUSING_TO_STOP')
        process.terminate()
        process.wait(timeout=15)
    except psutil.NoSuchProcess:
        pass

def ensure_ai():
    import httpx
    url='http://127.0.0.1:8954'
    try:
        response=httpx.get(url+'/api/tags',trust_env=False,timeout=2)
        response.raise_for_status()
        return
    except (httpx.ConnectError,httpx.TimeoutException):
        pass
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',8954))
    environment={k:v for k,v in os.environ.items() if not k.startswith(('VIGILE_','OLLAMA_'))}
    environment.update(OLLAMA_HOST='127.0.0.1:8954',OLLAMA_NO_CLOUD='1',OLLAMA_NOPRUNE='1',
                       OLLAMA_MODELS=str(ROOT/'engine/local_ai/ollama-models'))
    with (ROOT/'work/cloudflare/ollama.log').open('ab') as output:
        process=subprocess.Popen([str(ROOT/'engine/local_ai/ollama-v0.40.6/ollama.exe'),'serve'],
                                 env=environment,cwd=ROOT/'engine',stdin=subprocess.DEVNULL,
                                 stdout=output,stderr=output,creationflags=subprocess.CREATE_NO_WINDOW)
    import psutil
    (ROOT/'work/cloudflare/ai-process.json').write_text(json.dumps(
        {'pid':process.pid,'created':psutil.Process(process.pid).create_time(),'name':'demo-ollama'}))
    for _ in range(60):
        if process.poll() is not None:raise RuntimeError('ISOLATED_AI_STARTUP_FAILED')
        try:
            response=httpx.get(url+'/api/tags',trust_env=False,timeout=2)
            response.raise_for_status()
            return
        except (httpx.ConnectError,httpx.TimeoutException):
            time.sleep(.5)
    raise RuntimeError('ISOLATED_AI_STARTUP_TIMEOUT')

def prepare():
    if FOLDER.exists():
        raise RuntimeError('DEMO_ALREADY_EXISTS')
    ensure_ai()
    from vigile.mission_demo import prepare as mission_prepare
    from vigile.knowledge_v08 import build, SOURCES
    from demo_asthral import personal
    from vigile.vector_library import build as index, MiniLM
    passwords = [secrets.token_urlsafe(24) for _ in range(2)]
    mission_prepare(FOLDER, seed=42)
    restrict_directory(FOLDER)
    build(ROOT, FOLDER/'library.json', sources=[SOURCES[0]])
    config = json.loads((FOLDER/'portal-config.json').read_text(encoding='utf8'))
    personal(FOLDER, config, passwords)
    protect_secret(json.dumps(dict(zip(('crew-alpha','crew-bravo'), passwords))), FOLDER/'demo-credentials.dpapi')
    digest = '4f5da3bd944d9ad1cd3acc7d065ee54367a4c703f51fb6295bd8bc5007ed0c4a'
    config['model_url']='http://127.0.0.1:8954'
    index(FOLDER/'library.json', FOLDER/'vectors.db', MiniLM(config['model_url'], digest))
    config.update(backend_url=f'http://127.0.0.1:{BACKEND_PORT}', accounts_db=str(FOLDER/'personal.sqlite3'),
                  public_origin_file=str(ORIGIN), structured_explanations=True, voice_enabled=True,
                  library_manifest=str(FOLDER/'library.json'),
                  online_retrieval={'enabled': True, 'providers':['pubmed'],'timeout_seconds':4,'queries_per_minute':2,'retries':1},
                  public_science_cache=str(FOLDER/'public-science-cache'),
                  vector_retrieval={'url':config['model_url'], 'digest':digest,'index':str(FOLDER/'vectors.db'),'hybrid_enabled':True})
    (FOLDER/'portal-config.json').write_text(json.dumps(config, indent=2), encoding='utf8')
    (FOLDER/'isolated-empty-cloudflare.yml').write_text('{}\n')
    (FOLDER/'temp').mkdir()
    print('Prepared synthetic demo. Passwords are protected with current-user DPAPI.')

def start():
    ensure_ai()
    current = state()
    if any(alive(current.get(name)) for name in ('backend','portal')):
        raise RuntimeError('DEMO_ALREADY_RUNNING')
    for port in (BACKEND_PORT, PORTAL_PORT):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',port))
    config=json.loads((FOLDER/'portal-config.json').read_text(encoding='utf8'))
    expected={'accounts_db':FOLDER/'personal.sqlite3','public_origin_file':ORIGIN,
              'library_manifest':FOLDER/'library.json','public_science_cache':FOLDER/'public-science-cache'}
    for key,value in expected.items():
        if Path(config[key]).resolve()!=value.resolve():raise RuntimeError('ISOLATED_STORAGE_REQUIRED')
    if config['backend_url']!=f'http://127.0.0.1:{BACKEND_PORT}':raise RuntimeError('DEDICATED_BACKEND_REQUIRED')
    import sqlite3
    with sqlite3.connect((FOLDER/'vigile.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as database:
        profiles=[json.loads(row[0]) for row in database.execute("SELECT payload FROM records WHERE kind='profile'")]
    if not profiles or not all(row.get('synthetic') is True for row in profiles):
        raise RuntimeError('SYNTHETIC_PROFILES_REQUIRED')
    environment = {k:v for k,v in os.environ.items() if not k.startswith(('VIGILE_', 'TUNNEL_'))}
    environment.update(TEMP=str(FOLDER/'temp'), TMP=str(FOLDER/'temp'))
    backend = dict(environment,VIGILE_DB=str(FOLDER/'vigile.sqlite3'),VIGILE_TOKEN_FILE=str(FOLDER/'server-tokens.json'))
    current['backend'] = spawn('backend',[sys.executable,'-m','uvicorn','vigile.api:create_app','--factory','--host','127.0.0.1','--port',str(BACKEND_PORT),'--no-proxy-headers','--no-access-log'],backend)
    save(current)
    current['portal'] = spawn('portal',[sys.executable,'-m','vigile.portal','--config',str(FOLDER/'portal-config.json'),'--port',str(PORTAL_PORT)],environment)
    save(current)
    for _ in range(60):
        if not all(alive(current.get(name)) for name in ('backend','portal')):
            raise RuntimeError('DEMO_STARTUP_FAILED_INSPECT_PRIVATE_LOGS')
        try:
            with socket.create_connection(('127.0.0.1',PORTAL_PORT),timeout=1):
                break
        except OSError:
            time.sleep(.5)
    else:
        raise RuntimeError('DEMO_STARTUP_TIMEOUT')
    print('Dedicated loopback backend and portal started. Public origin stays closed until tunnel admission.')

def tunnel():
    current = state()
    if alive(current.get('tunnel')):
        raise RuntimeError('TUNNEL_ALREADY_RUNNING')
    if not all(alive(current.get(n)) for n in ('portal','backend')):
        raise RuntimeError('START_DEMO_FIRST')
    from check_public_demo import run as preflight
    preflight(local=True)
    if hashlib.sha256(BINARY.read_bytes()).hexdigest() != BINARY_HASH:
        raise RuntimeError('CLOUDFLARED_HASH_MISMATCH')
    ORIGIN.unlink(missing_ok=True)
    log = FOLDER/'tunnel.log'
    if log.exists():
        log.replace(FOLDER/('tunnel-'+str(time.time_ns())+'.log'))
    environment = {k:v for k,v in os.environ.items() if not k.startswith('TUNNEL_')}
    current['tunnel'] = spawn('tunnel',[str(BINARY),'tunnel','--config',str(FOLDER/'isolated-empty-cloudflare.yml'),
                                     '--url',f'http://127.0.0.1:{PORTAL_PORT}','--protocol','quic','--no-autoupdate',
                                     '--metrics','127.0.0.1:8953'],environment)
    save(current)
    for _ in range(120):
        text = log.read_text(errors='replace') if log.exists() else ''
        matches = re.findall(r'https://[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com',text)
        if matches and 'Registered tunnel connection' in text:
            temporary=ORIGIN.with_suffix('.tmp')
            temporary.write_text(matches[0],encoding='utf8')
            temporary.replace(ORIGIN)
            print(matches[0])
            return
        if not alive(current['tunnel']):
            break
        time.sleep(.5)
    stop_one(current.get('tunnel'))
    ORIGIN.unlink(missing_ok=True)
    raise RuntimeError('QUICK_TUNNEL_UNAVAILABLE_INSPECT_PRIVATE_TUNNEL_LOG')

def check():
    import httpx
    origin = ORIGIN.read_text(encoding='utf8').strip() if ORIGIN.exists() else ''
    current = state()
    print(json.dumps({'processes':{key:alive(value) for key,value in current.items()},'public_url':origin}))
    if origin:
        with httpx.Client(verify=ssl.create_default_context(),trust_env=False,timeout=20) as client:
            response = client.get(origin+'/auth-mode')
            print(json.dumps({'public_status':response.status_code,'personal_login':response.json() if response.is_success else None}))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','start','tunnel','url','health','stop-tunnel','stop','credentials'])
    args=parser.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='start':start()
    elif args.command=='tunnel':tunnel()
    elif args.command=='url':print(ORIGIN.read_text(encoding='utf8') if ORIGIN.exists() else 'No admitted public tunnel.')
    elif args.command=='health':check()
    elif args.command=='credentials':
        # Only run manually in a private local terminal. Never put this output into shared logs.
        for name,password in json.loads(read_secret(FOLDER/'demo-credentials.dpapi')).items():
            print(name,password)
    else:
        current=state()
        ORIGIN.unlink(missing_ok=True)
        names=('tunnel',) if args.command=='stop-tunnel' else ('tunnel','portal','backend')
        for name in names:
            stop_one(current.pop(name,None))
            save(current)
        if args.command=='stop':
            ai_state=ROOT/'work/cloudflare/ai-process.json'
            if ai_state.exists():
                stop_one(json.loads(ai_state.read_text(encoding='utf8')));ai_state.unlink()
        print('Stopped only recorded demo processes.')

if __name__=='__main__':
    main()
