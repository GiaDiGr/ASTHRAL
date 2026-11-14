"""Verify actual local protections; no credentials in report or stdout."""
from pathlib import Path
import sys,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.local_protection import verified_backup,restore_backup,anchor_database,verify_anchor,read_secret,PREFIX
from vigile.encrypted_storage import capabilities
from vigile.store import Store
folder=ROOT/'engine/data'/sys.argv[1];db=folder/'vigile.sqlite3'
report={'clinical_validation':False,'encryption':capabilities(),'process_isolation':'SAME_WINDOWS_USER_NOT_ISOLATED','same_user_can_decrypt_DPAPI':True}
files=('server-tokens.json','reader-token.txt','portal-access.txt','acquisition-token.txt')
report['secret_envelopes']={f:(folder/f).read_text(encoding='utf8').startswith(PREFIX) for f in files}
mapping=json.loads(read_secret(folder/'server-tokens.json'));report['credential_roles']=sorted(v['role'] for v in mapping.values());assert report['credential_roles']==['operator','reader']
report['directory_acl']=subprocess.run(['icacls',str(folder)],capture_output=True,text=True,check=True).stdout
backup=ROOT/'engine/data/backups'/folder.name;restored=ROOT/'engine/data/backups'/(folder.name+'-restored')
report['backup']=verified_backup(db,backup);report['restored']=restore_backup(backup,restored)
external=Path.home()/'AppData/Local/Vigile/integrity';anchor=external/(folder.name+'.anchor.json');key=external/'audit-key.dpapi'
report['anchor_creation']=anchor_database(db,anchor,key);report['anchor_verification']=verify_anchor(db,anchor,key)
report['original_v010_anchor']=verify_anchor(ROOT/'engine/data/portal-v0100-integrated/vigile.sqlite3',external/'v0100-integrated.anchor.json',key)
pin=json.loads((ROOT/'docs/v010/reserved-bank-pin.json').read_text(encoding='utf8'))
report['reserved_bank_unchanged']=hashlib.sha256((ROOT/pin['path']).read_bytes()).hexdigest()==pin['sha256'];assert report['reserved_bank_unchanged']
report['reserved_bank_hash']=pin['sha256']
source=Store(db)
try: report['audit_valid']=source.verify();report['checkpoint']=source.checkpoint()
finally:source.close()
report['limitations']=['SQLITE_AND_BACKUPS_PLAINTEXT','DPAPI_IS_NOT_PROCESS_ISOLATION','HMAC_KEY_ACCESS_OR_SOURCE_CONTROL_CAN_FORGE_AUDIT','NO_THERAPEUTIC_EXECUTION','NO_CRYPTOGRAPHIC_MIGRATION_ATTEMPTED_WITHOUT_SQLCIPHER_PROVIDER']
(ROOT/'docs/v011'/('storage-'+folder.name+'.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:report[k] for k in ('encryption','secret_envelopes','audit_valid','reserved_bank_unchanged')},indent=2))
