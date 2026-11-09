import base64
import json
import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
pytest.importorskip('argon2')
from vigile.personal_accounts import Accounts
from vigile.portal import create_portal
from vigile.health_voice import parse
from vigile.vector_library import VectorLibrary, build
from vigile.knowledge_v08 import build as build_corpus, ROOT

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows DPAPI required')
ORIGIN = 'http://127.0.0.1:8766'
PASSWORD = 'synthetic fixture passphrase'

def post(client, path, **data):
    return client.post('/api/' + path, json=data, headers={'Origin': ORIGIN})

class Voice:
    text = 'record my exercise duration as twenty minutes in the past twenty four hours'
    before_return = None

    def transcribe(self, raw, language, mode):
        assert language == 'en'
        if self.before_return:
            self.before_return()
        return {'text': self.text, 'words': [{'word': word, 'conf': .99} for word in self.text.split()]}

    def close(self):
        pass

class NoModel:
    mode = 'FULL'
    def status(self):
        return {'available': False}

@pytest.fixture
def service(tmp_path, monkeypatch):
    from vigile import personal_accounts
    db = tmp_path / 'accounts.db'
    accounts = Accounts(db)
    for name in ('alpha', 'bravo'):
        accounts.create(name, PASSWORD, name, 'mission', name)
    class Backend:
        def __init__(self, url, credential):
            self.credential = credential
        def close(self):
            pass
        def get(self, path):
            name = self.credential
            if path == '/dashboard/identity':
                return {'role': 'reader', 'subject_ids': [name], 'mission_ids': ['mission']}
            if path == '/dashboard/subjects':
                return [{'id': name, 'mission_id': 'mission'}]
            if name not in path:
                raise RuntimeError('HTTP_403 fixture')
            return {'owner': name}
    monkeypatch.setattr(personal_accounts, 'ReaderClient', Backend)
    voice = Voice()
    def portal(**options):
        return TestClient(create_portal({'accounts_db': str(db), 'backend_url': ORIGIN},
                                        inference=NoModel(), voice=voice, **options), base_url=ORIGIN)
    return accounts, portal, voice

def login(client, username):
    response = post(client, 'login', username=username, password=PASSWORD)
    assert response.status_code == 200, response.text
    assert 'HttpOnly' in response.headers['set-cookie']
    assert 'SameSite=strict' in response.headers['set-cookie']

def capture(client, identifier='capture-one'):
    return post(client, 'voice/health-capture', capture_id=identifier, auto_save=True,
                audio_base64=base64.b64encode(b'synthetic voice bytes').decode())

def test_accounts_sessions_and_voice_restart(service):
    accounts, portal, _ = service
    with portal() as alpha, portal() as bravo:
        assert alpha.get('/api/subjects').status_code == 401
        login(alpha, 'alpha')
        login(bravo, 'bravo')
        assert alpha.get('/api/subjects').json() == [{'id': 'alpha', 'mission_id': 'mission'}]
        assert bravo.get('/api/subjects').json() == [{'id': 'bravo', 'mission_id': 'mission'}]
        for path in ('dashboard/bravo?mission_id=mission', 'frames/bravo?mission_id=mission',
                     'replay/clinical/bravo', 'replay/monitoring/bravo'):
            assert alpha.get('/api/' + path).status_code == 404
        assert post(alpha, 'mode', mode='FULL').status_code == 403
        saved = capture(alpha)
        assert saved.status_code == 200, saved.text
        saved = saved.json()
        assert saved['status'] == 'SAVED' and saved['source'] == 'SELF_REPORTED_VOICE'
        assert saved['sensor_verified'] is False and capture(alpha).json() == saved
        assert bravo.get('/api/voice/health-history').json() == []
        assert post(bravo, 'voice/health-delete', record_id=saved['record_id']).status_code == 404
        assert post(bravo, 'voice/health-review', record_id=saved['record_id'],
                    transcript='my heart rate is 82 beats per minute').status_code == 404
        assert post(alpha, 'logout').status_code == 200
        assert alpha.get('/api/voice/health-history').status_code == 401
    with portal() as restarted:
        login(restarted, 'alpha')
        assert restarted.get('/api/voice/health-history').json() == [saved]
        accounts.reset('alpha', 'another synthetic password')
        assert restarted.get('/api/subjects').status_code == 401
    data = accounts.path.read_bytes()
    assert PASSWORD.encode() not in data
    assert saved['transcript'].encode() not in data
    assert b'synthetic voice bytes' not in data

def test_pending_capture_logout_and_draft_isolation(service):
    _, portal, voice = service
    with portal() as alpha, portal() as separate:
        login(alpha, 'alpha')
        login(separate, 'alpha')
        voice.text = 'my heart rate is eighty two beats per minute'
        draft = capture(alpha).json()
        assert draft['status'] == 'DRAFT'
        assert post(separate, 'voice/health-review', record_id=draft['record_id'],
                    transcript=draft['transcript']).status_code == 404
        voice.before_return = lambda: post(alpha, 'logout')
        assert capture(alpha, 'pending').status_code == 401
        assert separate.get('/api/voice/health-history').json() == []

def test_capture_expiry_and_rejected_foreign_owner(service):
    _, portal, voice = service
    now = [1000]
    with portal(clock=lambda: now[0]) as alpha:
        login(alpha, 'alpha')
        payload = {'capture_id': 'forged', 'audio_base64': 'dGVzdA==', 'subject_id': 'bravo'}
        assert post(alpha, 'voice/health-capture', **payload).status_code == 422
        assert alpha.post('/api/voice/health-capture', json=payload,
                          headers={'Origin': 'https://foreign.invalid'}).status_code == 403
        voice.before_return = lambda: now.__setitem__(0, 2000)
        assert capture(alpha).status_code == 401
        login(alpha, 'alpha')
        assert alpha.get('/api/voice/health-history').json() == []


def test_revision_tombstone_and_idempotent_retry(service):
    accounts, portal, _ = service
    with portal() as alpha:
        login(alpha, 'alpha')
        saved = capture(alpha).raise_for_status().json()
        rid = saved['record_id']
        corrected = post(alpha, 'voice/health-review', record_id=rid,
                         transcript='my exercise duration is ten minutes in the past twenty four hours'
                         ).raise_for_status().json()
        assert corrected['status'] == 'CORRECTED'
        assert corrected['audit_event_id'] != saved['audit_event_id']
        assert capture(alpha).json() == corrected
        deleted = post(alpha, 'voice/health-delete', record_id=rid).raise_for_status().json()
        assert deleted['status'] == 'DELETED' and 'transcript' not in deleted
        assert capture(alpha).json() == deleted
        assert alpha.get('/api/voice/health-history').json() == []
        assert corrected['transcript'].encode() not in accounts.path.read_bytes()


@pytest.mark.parametrize(('utterance', 'expected'), [
    ('My blood pressure is one hundred eighteen over seventy six', [118, 76]),
    ('Astral, record my temperature as thirty seven point two degrees Celsius', [37.2]),
    ('Record my oxygen saturation as 97 percent', [97]),
    ('Record my heart rate as 82', None),
    ('Do I need to record my glucose?', None),
    ('I slept six hours last night', [6]),
    ('Record my heart rate as not eighty beats per minute', None),
])
def test_conservative_parsing(utterance, expected):
    assert (parse(utterance) or {}).get('values') == expected

class FixtureEmbedding:
    identity = 'fixture-only-v1'
    def __call__(self, texts):
        return [[1] + [0]*383 for _ in texts]

def test_vector_reopen_corruption_version_and_mode(tmp_path):
    manifest = tmp_path / 'manifest.json'
    index = tmp_path / 'vectors.db'
    build_corpus(ROOT, manifest)
    embed = FixtureEmbedding()
    assert build(manifest, index, embed) > 0
    mode = ['FULL']
    library = VectorLibrary(manifest, index, embed, lambda: mode[0], hybrid=True)
    question = 'radiation dosimetry accumulated coverage'
    assert library.retrieve(question, 2, 'vector')[0]
    assert library.search(question)[0]
    with sqlite3.connect(index) as db:
        db.execute("UPDATE metadata SET model='incorrect'")
    assert 'VECTOR_UNAVAILABLE_LEXICAL_FALLBACK' in library.search(question)[1]
    build(manifest, index, embed)
    with sqlite3.connect(index) as db:
        db.execute("UPDATE vectors SET vector=zeroblob(1536)")
    assert 'VECTOR_UNAVAILABLE_LEXICAL_FALLBACK' in library.search(question)[1]
    mode[0] = 'CRITICAL'
    assert 'VECTOR_UNAVAILABLE_LEXICAL_FALLBACK' not in library.search(question)[1]
