from pathlib import Path
import argparse, base64, json, os, socket, subprocess, sys, time
import httpx
root = Path(__file__).resolve().parents[2]
engine = root/'engine'
sys.path.insert(0, str(engine))
sys.path.insert(0, str(engine/'tools'))
from vigile.mission_demo import prepare, SUBJECTS, MID
from vigile.knowledge_v08 import SOURCES, build
from vigile.voice import LocalVoice
from demo_asthral import personal

parser = argparse.ArgumentParser(description='Exercise two synthetic accounts and local SAPI/Vosk over loopback')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--vector-digest', help='Exercise the existing local Qwen assistant with a pinned MiniLM index')
args = parser.parse_args()
folder = args.output.resolve()
for port in (8931, 8932):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', port))
passwords = ('fixture-only alpha passphrase', 'fixture-only bravo passphrase')
result = prepare(folder, seed=42)
build(root, folder/'library.json', sources=[SOURCES[0]])
config = json.loads((folder/'portal-config.json').read_text())
backend_url = 'http://127.0.0.1:8931'
portal_url = 'http://127.0.0.1:8932'
config.update(backend_url=backend_url, structured_explanations=True, voice_enabled=True,
              library_manifest=str(folder/'library.json'), mode='FULL')
personal(folder, config, passwords)
if args.vector_digest:
    from vigile.vector_library import MiniLM, build as build_index
    url = config['model_url']
    index = folder/'vectors.db'
    build_index(folder/'library.json', index, MiniLM(url, args.vector_digest))
    config['vector_retrieval'] = {'index': str(index), 'url': url,
                                  'digest': args.vector_digest, 'hybrid_enabled': True}
(folder/'portal-config.json').write_text(json.dumps(config))
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
        audio,_=voice.synthesize('My heart rate is eighty two beats per minute.','en')
        exercise_audio,_=voice.synthesize('Record my exercise duration as twenty minutes in the past twenty four hours.','en')
        transcribed=voice.transcribe(audio,'en')
        print('VOSK',repr(transcribed['text']),transcribed['transcription_seconds'],flush=True)
    finally:
        voice.close()
    with httpx.Client(base_url=portal_url,timeout=90,trust_env=False) as a, httpx.Client(base_url=portal_url,timeout=90,trust_env=False) as b:
        login(a,'crew-alpha',passwords[0]);login(b,'crew-bravo',passwords[1])
        for i,client in enumerate((a,b)):
            assert [r['id'] for r in client.get('/api/subjects').json()]==[SUBJECTS[i]]
        own=b.get(f'/api/dashboard/{SUBJECTS[1]}?mission_id={MID}').raise_for_status().json()
        foreign=b.get(f'/api/frames/{SUBJECTS[1]}?mission_id={MID}').raise_for_status().json()
        eid=own['evaluations'][0]['id']
        for path in [f'dashboard/{SUBJECTS[1]}?mission_id={MID}&frame_id='+foreign[0]['id'],
                     f'dashboard/{SUBJECTS[0]}?mission_id={MID}&frame_id='+foreign[0]['id'],
                     f'frames/{SUBJECTS[1]}?mission_id={MID}', 'replay/clinical/'+eid]:
            r=a.get('/api/'+path)
            assert (r.status_code,r.json())==(404,{'detail':'RESULT_NOT_FOUND'}), (path,r.status_code,r.text[:100])
        denied=post(a,'assistant',evaluation_id=eid,question='Explain the recorded clinical results')
        assert denied.status_code==404, denied.text
        if args.vector_digest:
            dka = next(row['id'] for row in own['evaluations'] if row.get('condition_id')=='DKA')
            reply = post(b, 'assistant', evaluation_id=dka,
                         question='Does missing potassium still restrict insulin if the DKA criteria are satisfied?'
                         ).raise_for_status().json()
            assert reply.get('sources'), 'Expected existing scoped clinical sources'
            print('ASSISTANT', json.dumps({'status': reply['status'],
                                          'trace': reply.get('inference_trace'),
                                          'history_used': reply.get('history_used')}), flush=True)
            narrative = post(a, 'assistant', monitoring_id='mission-crew-A-cycle-35',
                             question='Compare the recorded aerobic capacity and its baseline'
                             ).raise_for_status().json()
            print('LOCAL NARRATIVE', json.dumps({'status': narrative['status'],
                                                'trace': narrative.get('inference_trace')}), flush=True)
        captured=post(a,'voice/health-capture',capture_id='sapi-fixture',audio_base64=base64.b64encode(audio).decode()).raise_for_status().json()
        assert captured['status']=='DRAFT' and captured['observation']['values']==[82], captured
        saved=post(a,'voice/health-review',record_id=captured['record_id'],transcript=captured['transcript']).raise_for_status().json()
        expected_history = [saved]
        exercise = post(a, 'voice/health-capture', capture_id='exercise-fixture', auto_save=True,
                        audio_base64=base64.b64encode(exercise_audio).decode()).raise_for_status().json()
        assert exercise['status'] in ('SAVED', 'DRAFT', 'IGNORED')
        if exercise['status']=='SAVED':
            assert exercise['observation']['values']==[20] and exercise['observation']['kind']=='exercise_duration'
            expected_history.insert(0, exercise)
        print('EXERCISE CAPTURE', json.dumps({'status': exercise['status'],
                                             'confidence': exercise.get('confidence')}), flush=True)
        assert b.get('/api/voice/health-history').json()==[]
        print('HTTP cross-user dashboard, frames, replay, assistant and voice denied; saved via real SAPI/Vosk',flush=True)
        p.terminate();p.wait(timeout=10);p=portal();wait()
        assert a.get('/api/voice/health-history').status_code==401
        login(a,'crew-alpha',passwords[0]);assert a.get('/api/voice/health-history').json()==expected_history
        print('PROCESS RESTART: saved event present; old cookie revoked',flush=True)
        report = json.loads((folder/'mission-report.json').read_text(encoding='utf8'))
        print('MISSION', json.dumps({'cycles': result['cycles'], 'audit_integrity': result['audit_integrity'],
                                     'clinical_replays': len(result['clinical_replays']),
                                     'matching_monitoring_replays': sum(row['matches'] for row in report['replays'])}), flush=True)
finally:
    for child in (p,backend):
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=10)
