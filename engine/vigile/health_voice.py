"""Session-bound health capture with a separate self-reported history."""
import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException, Request
from pydantic import Field
from .models import Model, Id
from .local_protection import _crypt
from .voice import VoiceError, MAX_WAV_BYTES

PATTERNS = {
    'heart_rate': (r'heart rate (?:as|is) (.+) beats per minute', 'beats/min'),
    'blood_pressure': (r'blood pressure (?:as|is) (.+) over (.+?)(?: millimeters of mercury)?', 'mmHg'),
    'temperature': (r'temperature (?:as|is) (.+) degrees celsius', 'Cel'),
    'body_mass': (r'(?:body mass|weight) (?:as|is) (.+) kilograms', 'kg'),
    'blood_glucose': (r'blood glucose (?:as|is) (.+) milligrams per deciliter', 'mg/dL'),
    'oxygen_saturation': (r'oxygen saturation (?:as|is) (.+) percent', '%'),
    'sleep_duration': (r'sleep duration (?:as|is) (.+) hours', 'h'),
    'exercise_duration': (r'exercise duration (?:as|is) (.+) minutes', 'min'),
    'pain_score': (r'pain score (?:as|is) (.+) out of ten', '1'),
    'fatigue_score': (r'fatigue score (?:as|is) (.+) out of ten', '1'),
}
DIGITS = dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(), range(20)))
TENS = dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), range(20, 100, 10)))

def number(text):
    if re.fullmatch(r'[0-9]{1,4}(?:\.[0-9]{1,3})?', text):
        return float(text)
    left, separator, right = text.partition(' point ')
    words = left.split()
    total = 0
    if len(words) >= 2 and words[1] == 'hundred' and 1 <= DIGITS.get(words[0], 0) <= 9:
        total = DIGITS[words[0]] * 100
        words = words[2:]
    if len(words) == 1 and words[0] in DIGITS | TENS:
        total += (DIGITS | TENS)[words[0]]
    elif len(words) == 2 and words[0] in TENS and 1 <= DIGITS.get(words[1], 0) <= 9:
        total += TENS[words[0]] + DIGITS[words[1]]
    elif words or not total:
        raise ValueError
    if separator:
        digits = right.split()
        if not 1 <= len(digits) <= 3 or any(DIGITS.get(d, 10) > 9 for d in digits):
            raise ValueError
        total += float('0.' + ''.join(str(DIGITS[d]) for d in digits))
    return total

def parse(text):
    statement = text.lower().strip().rstrip('.')
    if '?' in statement:
        return None
    statement = re.sub(r'^(?:asthral|astral),? ', '', statement)
    match = re.fullmatch(r'(record my|my) (.+)', statement)
    if not match:
        sleep = re.fullmatch(r'i slept (.+) hours last night', statement)
        if sleep:
            result = parse('my sleep duration is ' + sleep[1] + ' hours')
            return {**result, 'time_reference': 'LAST_NIGHT'} if result else {'kind': 'unresolved', 'structured': False}
        if statement.startswith(('i have a question', 'i have another question')):
            return None
        if re.match(r"^(?:i feel |i have |i've been feeling )", statement):
            return {'kind': 'symptom', 'structured': False}
        return None
    content = match[2]
    time_reference = None
    if content.endswith(' in the past twenty four hours'):
        content = content.removesuffix(' in the past twenty four hours')
        time_reference = 'PAST_24_HOURS'
    elif content.endswith(' right now'):
        content = content.removesuffix(' right now')
        time_reference = 'AT_RECORDING'
    for kind, (pattern, unit) in PATTERNS.items():
        measurement = re.fullmatch(pattern, content)
        if not measurement:
            continue
        try:
            values = [number(part) for part in measurement.groups()]
        except ValueError:
            break
        if kind in ('oxygen_saturation', 'pain_score', 'fatigue_score'):
            valid = all(0 <= v <= (100 if kind == 'oxygen_saturation' else 10) for v in values)
        else:
            valid = all(v > 0 for v in values)
        if kind in ('sleep_duration', 'exercise_duration'):
            valid &= values[0] <= (24 if unit == 'h' else 1440)
        if kind == 'blood_pressure':
            valid &= values[0] > values[1] and all(v.is_integer() for v in values)
        return {'kind': kind, 'structured': valid, 'values': values, 'unit': unit,
                'reported': measurement.groups(), 'time_reference': time_reference, 'explicit': match[1] == 'record my'}
    return {'kind': 'unresolved', 'structured': False} if match[1] == 'record my' else None

class Capture(Model):
    capture_id: Id
    audio_base64: str = Field(min_length=1, max_length=1_800_100)
    auto_save: bool = False

class Change(Model):
    record_id: Id

class Review(Change):
    transcript: str = Field(min_length=1, max_length=1200)

def install_health_voice(app, accounts, sessions, inference):
    with accounts.connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS health_events (
            account TEXT NOT NULL, session TEXT NOT NULL, capture TEXT NOT NULL,
            event TEXT NOT NULL PRIMARY KEY, record TEXT NOT NULL, action TEXT NOT NULL,
            payload BLOB NOT NULL, UNIQUE(account,session,capture,action))""")
        db.execute('CREATE INDEX IF NOT EXISTS health_owner ON health_events(account,record)')

    def session_guard(request):
        token = request.cookies.get('vigile_session', '')
        row = sessions.get(token, False)
        account = request.state.account
        if not row or row['account'] != account or not accounts.is_active(account):
            raise HTTPException(401, 'SESSION_EXPIRED_OR_REQUIRED')
        return account, hashlib.sha256(token.encode()).hexdigest()

    def decode(row):
        data = json.loads(_crypt(row['payload'], True))
        if (data['account_id'], data['record_id'], data['audit_event_id'], data['status']) != (
                row['account'], row['record'], row['event'], row['action']):
            raise ValueError('HEALTH_EVENT_BINDING_INVALID')
        return data

    def retry(db, row, audio_hash):
        result = decode(row)
        if result.get('audio_hash') != audio_hash:
            raise HTTPException(409, 'CAPTURE_ID_REUSED')
        latest = db.execute('SELECT * FROM health_events WHERE account=? AND record=? ORDER BY rowid DESC LIMIT 1',
                            (row['account'], row['record'])).fetchone()
        return decode(latest)

    def append(db, account, session, capture, record, action, data):
        event = uuid4().hex
        result = {**data, 'record_id': record, 'audit_event_id': event, 'status': action,
                  'account_id': account.id, 'subject_id': account.subject, 'mission_id': account.mission,
                  'source': 'SELF_REPORTED_VOICE', 'sensor_verified': False, 'clinical_execution': 'BLOCKED',
                  'submitted_at': datetime.now(timezone.utc).isoformat()}
        db.execute('INSERT INTO health_events VALUES (?,?,?,?,?,?,?)',
                   (account.id, session, capture, event, record, action, _crypt(json.dumps(result).encode())))
        return result

    @app.post('/api/voice/health-capture')
    def capture(body: Capture, request: Request):
        account, session = session_guard(request)
        try:
            raw = base64.b64decode(body.audio_base64, validate=True)
        except ValueError:
            raise VoiceError('AUDIO_FORMAT_INVALID') from None
        if len(raw) > MAX_WAV_BYTES:
            raise VoiceError('AUDIO_SIZE_INVALID')
        audio_hash = hashlib.sha256(raw).hexdigest()
        voice = app.state.voice
        if not voice:
            raise HTTPException(503, 'VOICE_NOT_CONFIGURED')
        with accounts.connect() as db:
            old = db.execute('SELECT * FROM health_events WHERE account=? AND session=? AND capture=?',
                             (account.id, session, body.capture_id)).fetchone()
            if old:
                return retry(db, old, audio_hash)
        recorded = datetime.now(timezone.utc).isoformat()
        speech = voice.transcribe(raw, 'en', getattr(inference, 'mode', 'CRITICAL'))
        text = speech['text']
        parsed = parse(text)
        words = speech.get('words') or []
        confidence = min((w.get('conf', 0) for w in words), default=None)
        if not parsed:
            session_guard(request)
            return {'status': 'IGNORED', 'transcript': text, 'clinical_execution': 'BLOCKED'}
        # Only exact, explicit duration statements with physical time bounds auto-save.
        # Physiological readings and symptoms require review independently of confidence.
        auto = (body.auto_save and parsed.get('explicit') and parsed['structured']
                and parsed['kind'] in ('sleep_duration', 'exercise_duration')
                and parsed.get('time_reference') == 'PAST_24_HOURS'
                and confidence is not None and confidence >= .95
                and ' '.join(w.get('word', '') for w in words) == text)
        with sessions.lock, accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            session_guard(request)
            old = db.execute('SELECT * FROM health_events WHERE account=? AND session=? AND capture=?',
                             (account.id, session, body.capture_id)).fetchone()
            if old:
                return retry(db, old, audio_hash)
            return append(db, account, session, body.capture_id, uuid4().hex, 'SAVED' if auto else 'DRAFT',
                          {'transcript': text, 'observation': parsed, 'confidence': confidence, 'audio_hash': audio_hash,
                           'recorded_at': recorded, 'observation_time': recorded if parsed.get('time_reference') == 'AT_RECORDING' else None, 'validation': 'SELF_REPORTED' if auto else 'REVIEW_REQUIRED'})

    @app.post('/api/voice/health-review')
    def review(body: Review, request: Request):
        parsed = parse(body.transcript)
        if not parsed or (not parsed['structured'] and parsed['kind'] != 'symptom'):
            raise HTTPException(422, 'REVIEW_REQUIRES_CLEAR_OBSERVATION')
        with sessions.lock, accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            account, session = session_guard(request)
            row = db.execute('SELECT * FROM health_events WHERE account=? AND record=? ORDER BY rowid DESC LIMIT 1',
                             (account.id, body.record_id)).fetchone()
            if not row or row['action'] == 'DELETED' or (row['action'] == 'DRAFT' and row['session'] != session):
                raise HTTPException(404, 'RESULT_NOT_FOUND')
            data = decode(row)
            if row['action'] != 'DRAFT' and data['transcript'] == body.transcript:
                return data
            data.update(transcript=body.transcript, observation=parsed,
                        observation_time=data['recorded_at'] if parsed.get('time_reference') == 'AT_RECORDING' else None, validation='SELF_REPORTED_USER_REVIEWED')
            return append(db, account, session, uuid4().hex, body.record_id,
                          'SAVED' if row['action'] == 'DRAFT' else 'CORRECTED', data)

    @app.post('/api/voice/health-delete')
    def delete(body: Change, request: Request):
        with sessions.lock, accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            account, session = session_guard(request)
            row = db.execute('SELECT * FROM health_events WHERE account=? AND record=? ORDER BY rowid DESC LIMIT 1',
                             (account.id, body.record_id)).fetchone()
            if not row or (row['action'] == 'DRAFT' and row['session'] != session):
                raise HTTPException(404, 'RESULT_NOT_FOUND')
            if row['action'] == 'DELETED':
                return decode(row)
            return append(db, account, session, uuid4().hex, body.record_id, 'DELETED', {})

    @app.get('/api/voice/health-history')
    def history(request: Request):
        account, _ = session_guard(request)
        with accounts.connect() as db:
            rows = db.execute("""SELECT * FROM health_events WHERE rowid IN
                (SELECT max(rowid) FROM health_events WHERE account=? GROUP BY record)
                AND action IN ('SAVED','CORRECTED') ORDER BY rowid DESC LIMIT 100""", (account.id,)).fetchall()
            return [decode(row) for row in rows]
