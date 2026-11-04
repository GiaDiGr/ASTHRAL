"""Optional SQLCipher boundary. Never silently fall back to plaintext.
Not wired into Store until a separately verified migration and replay exercise.
Official API: https://www.zetetic.net/sqlcipher/sqlcipher-api/
"""
import importlib,sqlite3,re

def capabilities():
 c=sqlite3.connect(':memory:')
 try:version=c.execute('PRAGMA cipher_version').fetchone()
 finally:c.close()
 try:importlib.import_module('sqlcipher3.dbapi2');provider=True
 except ImportError:provider=False
 return {'active_store':'STANDARD_SQLITE','active_database_encrypted':False,'sqlite_cipher_version':version[0] if version else None,'sqlcipher_provider_available':provider,'migration':'BLOCKED_PENDING_DEPENDENCY_AND_VERIFIED_MIGRATION'}

def open_sqlcipher(database,key_hex):
 if not re.fullmatch(r'[a-fA-F0-9]{64}',key_hex):raise ValueError('RAW_256_BIT_KEY_REQUIRED')
 try:provider=importlib.import_module('sqlcipher3.dbapi2')
 except ImportError:raise RuntimeError('SQLCIPHER_DEPENDENCY_UNAVAILABLE') from None
 c=provider.connect(str(database))
 try:
  version=c.execute('PRAGMA cipher_version').fetchone()
  if not version or not version[0]:raise RuntimeError('SQLCIPHER_PROVIDER_NOT_VERIFIED')
  c.execute('PRAGMA key = "x\''+key_hex+'\'"')
  c.execute('SELECT count(*) FROM sqlite_master').fetchone()
  return c
 except Exception:c.close();raise
