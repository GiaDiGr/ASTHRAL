"""Offline provisioning and exact backend reader bindings."""
from contextvars import ContextVar
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
import re
import sqlite3

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from .local_protection import _crypt
from .local_assistant import ReaderClient

@dataclass(frozen=True)
class Account:
    id: str
    username: str
    subject: str
    mission: str
    generation: int

class Accounts:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
        self.dummy = self.hasher.hash(uuid4().hex)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                subject TEXT UNIQUE NOT NULL, mission TEXT NOT NULL, reader BLOB NOT NULL,
                active INTEGER NOT NULL DEFAULT 1, generation INTEGER NOT NULL DEFAULT 1)""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, username, password, subject, mission, token):
        username = username.lower()
        if not re.fullmatch(r'[a-z0-9_.-]{3,64}', username):
            raise ValueError('INVALID_USERNAME')
        if not all(re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', item) for item in (subject, mission)):
            raise ValueError('INVALID_BINDING')
        identifier = uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO accounts(id,username,password,subject,mission,reader) VALUES (?,?,?,?,?,?)',
                       (identifier, username, self.password_hash(password), subject, mission, _crypt(token.encode())))
        return identifier

    def password_hash(self, password):
        if not 14 <= len(password) <= 256:
            raise ValueError('PASSWORD_LENGTH_14_TO_256')
        return self.hasher.hash(password)

    def reset(self, username, password):
        with self.connect() as db:
            return db.execute('UPDATE accounts SET password=?,generation=generation+1 WHERE username=?',
                              (self.password_hash(password), username.lower())).rowcount == 1

    def disable(self, username):
        with self.connect() as db:
            return db.execute('UPDATE accounts SET active=0,generation=generation+1 WHERE username=?',
                              (username.lower(),)).rowcount == 1

    def authenticate(self, username, password):
        with self.connect() as db:
            row = db.execute('SELECT * FROM accounts WHERE username=?', (username.lower(),)).fetchone()
        try:
            self.hasher.verify(row['password'] if row else self.dummy, password)
        except VerifyMismatchError:
            return None
        return self.account(row) if row and row['active'] else None

    @staticmethod
    def account(row):
        return Account(*(row[key] for key in ('id', 'username', 'subject', 'mission', 'generation')))

    def is_active(self, account):
        with self.connect() as db:
            return db.execute('SELECT 1 FROM accounts WHERE id=? AND active=1 AND generation=?',
                              (account.id, account.generation)).fetchone() is not None

    def resolve(self, account):
        with self.connect() as db:
            row = db.execute('SELECT * FROM accounts WHERE id=? AND active=1 AND generation=?',
                             (account.id, account.generation)).fetchone()
        return _crypt(row['reader'], True).decode() if row else None

class PersonalReader:
    """Dispatch portal calls through the credential admitted for this request."""
    def __init__(self, backend):
        self.backend = backend
        self.current = ContextVar('personal_reader')

    def bind(self, account, token):
        client = ReaderClient(self.backend, token)
        try:
            verify_binding(client, account.subject, account.mission)
            return client
        except BaseException:
            client.close()
            raise

    def get(self, path):
        return self.current.get().get(path)

    def close(self):
        pass

def verify_binding(client, subject, mission):
    identity = client.get('/dashboard/identity')
    if (identity.get('role'), identity.get('subject_ids'), identity.get('mission_ids')) != (
            'reader', [subject], [mission]):
        raise RuntimeError('READER_BINDING_MISMATCH')

def main():
    import argparse
    from getpass import getpass
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', required=True)
    parser.add_argument('action', choices=['create', 'reset', 'disable'])
    parser.add_argument('username')
    parser.add_argument('--subject')
    parser.add_argument('--mission')
    parser.add_argument('--backend', default='http://127.0.0.1:8765')
    args = parser.parse_args()
    accounts = Accounts(args.database)
    if args.action == 'disable':
        if not accounts.disable(args.username):
            parser.error('Account not found')
        return
    password = getpass('Password: ')
    if password != getpass('Repeat password: '):
        parser.error('Passwords differ')
    if args.action == 'reset':
        if not accounts.reset(args.username, password):
            parser.error('Account not found')
        return
    if not args.subject or not args.mission:
        parser.error('Creation requires --subject and --mission')
    token = getpass('Exact-scope backend reader token: ')
    reader = ReaderClient(args.backend, token)
    try:
        verify_binding(reader, args.subject, args.mission)
        print(accounts.create(args.username, password, args.subject, args.mission, token))
    finally:
        reader.close()

if __name__ == '__main__':
    main()
