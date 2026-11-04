"""SQLite append-only records, transactions and hash-chained audit (not a security HSM)."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from threading import RLock
from datetime import datetime, timezone

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

class Store:
    def __init__(self, path):
        self.lock = RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        version=self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0,1):
            self.db.close()
            raise ValueError('Unsupported database schema version')
        self.db.executescript("""
        PRAGMA foreign_keys=ON;
        PRAGMA journal_mode=WAL;
        PRAGMA busy_timeout=5000;
        CREATE TABLE IF NOT EXISTS records (
          seq INTEGER PRIMARY KEY, kind TEXT NOT NULL, id TEXT NOT NULL,
          payload TEXT NOT NULL, UNIQUE(kind,id));
        CREATE TABLE IF NOT EXISTS audit (
          seq INTEGER PRIMARY KEY, payload TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS records_no_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'append only'); END;
        CREATE TRIGGER IF NOT EXISTS records_no_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'append only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'append only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'append only'); END;
        PRAGMA user_version=1;
        """)

    @contextmanager
    def transaction(self):
        with self.lock:
            # Nested existing services participate atomically in a monitoring cycle.
            from uuid import uuid4
            nested=self.db.in_transaction
            savepoint='sp_'+uuid4().hex
            self.db.execute('SAVEPOINT '+savepoint if nested else 'BEGIN IMMEDIATE')
            try:
                yield
                self.db.execute('RELEASE SAVEPOINT '+savepoint if nested else 'COMMIT')
            except Exception:
                self.db.execute('ROLLBACK TO SAVEPOINT '+savepoint if nested else 'ROLLBACK')
                if nested: self.db.execute('RELEASE SAVEPOINT '+savepoint)
                raise

    def append_audit(self, event, actor, data):
        with self.lock:
            previous = self.db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            previous = previous[0] if previous else "0" * 64
            from .security import audit_identity
            payload = {"event": event, "actor": audit_identity.get() or actor, "role": actor, "data": data,
                       "recorded_at": datetime.now(timezone.utc).isoformat()}
            h = digest({"previous": previous, "payload": payload})
            self.db.execute("INSERT INTO audit(payload,previous,hash) VALUES (?,?,?)", (canonical(payload), previous, h))

    def insert_record(self, kind, identifier, payload, actor):
        self.db.execute("INSERT INTO records(kind,id,payload) VALUES (?,?,?)", (kind, identifier, canonical(payload)))
        self.append_audit("CREATE_" + kind.upper(), actor, {"id": identifier, "content_hash": digest(payload)})

    def put(self, kind, identifier, payload, actor="system"):
        self.put_many([(kind,identifier,payload)],actor)
        return payload

    def put_many(self, records, actor="system"):
        with self.transaction():
            for kind,identifier,payload in records:
                self.insert_record(kind,identifier,payload,actor)

    def checkpoint(self):
        with self.lock:
            row=self.db.execute("SELECT seq,hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            return {"sequence":row['seq'] if row else 0,"hash":row['hash'] if row else '0'*64}


    def audit(self, event, actor, data):
        with self.transaction():
            self.append_audit(event, actor, data)

    def get(self, kind, identifier):
        with self.lock:
            row = self.db.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, identifier)).fetchone()
        if not row:
            raise KeyError(f"{kind}:{identifier}")
        return json.loads(row[0])

    def all(self, kind):
        with self.lock:
            rows = self.db.execute("SELECT payload FROM records WHERE kind=? ORDER BY seq", (kind,)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def verify(self):
        with self.lock:
            rows = self.db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
            records = self.db.execute("SELECT * FROM records").fetchall()
        previous = "0" * 64
        anchored = set()
        for r in rows:
            p = json.loads(r['payload'])
            if r['previous'] != previous or r['hash'] != digest({"previous": previous, "payload": p}):
                return False
            previous = r['hash']
            if p['event'].startswith('CREATE_'):
                anchored.add((p['event'][7:].lower(), p['data']['id'], p['data']['content_hash']))
        actual={(r['kind'], r['id'], digest(json.loads(r['payload']))) for r in records}
        return actual == anchored

    def close(self):
        self.db.close()
