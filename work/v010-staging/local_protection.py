"""Windows DPAPI secret envelopes, verified SQLite backups and external HMAC anchors.
DPAPI/ACL protect other identities; processes running as the same Windows user remain a threat.
"""
from pathlib import Path
import os,ctypes,base64,json,hashlib,hmac,secrets,sqlite3,subprocess
from ctypes import wintypes
PREFIX='VIGILE-DPAPI-1:'
class Blob(ctypes.Structure):_fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
def _crypt(raw,decrypt=False):
 if os.name!='nt':raise RuntimeError('WINDOWS_DPAPI_REQUIRED')
 buffer=ctypes.create_string_buffer(raw);source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
 crypt=ctypes.WinDLL('crypt32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
 function=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
 function.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
 # CRYPTPROTECT_UI_FORBIDDEN; current-user scope, not machine-wide scope.
 if not function(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):raise ValueError('DPAPI_OPERATION_FAILED')
 try:return ctypes.string_at(target.data,target.size)
 finally:kernel.LocalFree(target.data)
def read_secret(path):
 text=Path(path).read_text(encoding='utf-8-sig').strip()
 if text.startswith(PREFIX):return _crypt(base64.b64decode(text[len(PREFIX):],validate=True),True).decode('utf8')
 return text

def protect_secret(text,destination):
 p=Path(destination);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as f:f.write(PREFIX+base64.b64encode(_crypt(text.encode('utf8'))).decode('ascii'))
 return {'protected':True,'scope':'WINDOWS_CURRENT_USER_DPAPI','path':str(p)}

def restrict_directory(path):
 p=Path(path).resolve()
 if not p.is_dir() or p.parent==p:raise ValueError('EXPLICIT_DIRECTORY_REQUIRED')
 result=subprocess.run(['whoami','/user','/fo','csv','/nh'],capture_output=True,text=True,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 import csv
 sid=next(csv.reader([result.stdout.strip()]))[1]
 subprocess.run(['icacls',str(p),'/inheritance:r','/grant:r',f'*{sid}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F'],capture_output=True,text=True,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 return {'path':str(p),'user_sid':sid,'scope':'CURRENT_USER_AND_SYSTEM','same_user_processes_isolated':False}

def _state(connection,record_limit=None):
 from .store import digest
 rows=connection.execute('SELECT seq,kind,id,payload FROM records '+('WHERE seq<=? ' if record_limit is not None else '')+'ORDER BY seq',(() if record_limit is None else (record_limit,))).fetchall()
 audit=connection.execute('SELECT seq,hash FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
 return {'record_sequence':rows[-1][0] if rows else 0,'record_count':len(rows),'records_hash':digest([list(row) for row in rows]),'audit_sequence':audit[0] if audit else 0,'audit_hash':audit[1] if audit else '0'*64}

def verified_backup(source,destination):
 source=Path(source).resolve();destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=False);target=destination/'vigile.sqlite3'
 src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True);dst=sqlite3.connect(target)
 try:
  src.execute('BEGIN');state=_state(src);src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert _state(dst)==state
 finally:src.close();dst.close()
 from .store import Store
 store=Store(target)
 try:
  if not store.verify():raise ValueError('BACKUP_AUDIT_INVALID')
 finally:store.close()
 manifest={'format':'VIGILE_SQLITE_BACKUP_1','source':str(source),'database':'vigile.sqlite3','sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'state':state,'sqlite_encryption':'NONE'}
 (destination/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');return manifest

def restore_backup(backup,destination):
 backup=Path(backup);manifest=json.loads((backup/'manifest.json').read_text());database=backup/'vigile.sqlite3'
 if hashlib.sha256(database.read_bytes()).hexdigest()!=manifest['sha256']:raise ValueError('BACKUP_HASH_MISMATCH')
 restored=verified_backup(database,destination)
 if restored['state']!=manifest['state']:raise ValueError('RESTORE_STATE_MISMATCH')
 return restored

def anchor_database(database,anchor_path,key_path):
 from .store import canonical
 database=Path(database);key_path=Path(key_path);anchor_path=Path(anchor_path)
 if anchor_path.resolve().is_relative_to(database.resolve().parent) or key_path.resolve().is_relative_to(database.resolve().parent):raise ValueError('ANCHOR_AND_KEY_MUST_BE_OUTSIDE_DATA_DIRECTORY')
 if not key_path.exists():protect_secret(secrets.token_hex(32),key_path)
 key=bytes.fromhex(read_secret(key_path));c=sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)
 try:c.execute('BEGIN');state=_state(c)
 finally:c.close()
 signed={'version':1,'algorithm':'HMAC-SHA256','checkpoint':state}
 mac=hmac.new(key,canonical(signed).encode('utf8'),hashlib.sha256).hexdigest()
 anchor_path.parent.mkdir(parents=True,exist_ok=True)
 with anchor_path.open('x',encoding='utf8') as f:json.dump({'signed':signed,'mac':mac},f,indent=2)
 return {'anchor':str(anchor_path),'algorithm':'HMAC-SHA256','checkpoint':state,'same_user_compromise_resistant':False}

def verify_anchor(database,anchor_path,key_path):
 from .store import canonical,Store
 value=json.loads(Path(anchor_path).read_text());signed=value['signed'];key=bytes.fromhex(read_secret(key_path))
 if signed.get('algorithm')!='HMAC-SHA256' or not hmac.compare_digest(value['mac'],hmac.new(key,canonical(signed).encode('utf8'),hashlib.sha256).hexdigest()):raise ValueError('ANCHOR_AUTHENTICATION_FAILED')
 expected=signed['checkpoint'];store=Store(database)
 try:
  if not store.verify():raise ValueError('AUDIT_INVALID')
  actual=_state(store.db,expected['record_sequence']);audit=store.db.execute('SELECT hash FROM audit WHERE seq=?',(expected['audit_sequence'],)).fetchone()
  if any(actual[k]!=expected[k] for k in ('record_sequence','record_count','records_hash')) or (audit[0] if audit else '0'*64)!=expected['audit_hash']:raise ValueError('ANCHORED_PREFIX_MISMATCH')
  return {'valid':True,'anchored_prefix':expected,'latest_checkpoint':store.checkpoint(),'protection':'DB_ONLY_TAMPERING_DETECTION_NOT_SAME_USER_COMPROMISE'}
 finally:store.close()

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('command',choices=['backup','restore','anchor','verify-anchor']);p.add_argument('--database',type=Path);p.add_argument('--backup',type=Path);p.add_argument('--destination',type=Path);p.add_argument('--anchor',type=Path);p.add_argument('--key',type=Path);a=p.parse_args()
 result=verified_backup(a.database,a.destination) if a.command=='backup' else restore_backup(a.backup,a.destination) if a.command=='restore' else anchor_database(a.database,a.anchor,a.key) if a.command=='anchor' else verify_anchor(a.database,a.anchor,a.key)
 print(json.dumps(result,indent=2))
