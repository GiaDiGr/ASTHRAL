import importlib.util,sys,pytest,sqlite3,json
from pathlib import Path
from vigile.store import Store
ROOT=Path(__file__).parent
def module(name):
 spec=importlib.util.spec_from_file_location('vigile.'+name,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
sessions=module('portal_sessions');protection=module('local_protection')
def test_session_expiry_rotation_and_rate():
 now=[0];s=sessions.Sessions(idle=10,absolute=30,clock=lambda:now[0]);token=s.create()
 for _ in range(12):assert s.admit(token,True)
 assert not s.admit(token,True)
 now[0]=5;new=s.renew(token);assert s.get(token) is None
 assert not s.admit(new,True)
 now[0]=14;assert s.get(new)
 now[0]=23;assert s.get(new)
 now[0]=30;assert s.get(new) is None
 assert new not in s.rows

def test_idle_poll_does_not_renew():
 now=[0];s=sessions.Sessions(idle=5,absolute=30,clock=lambda:now[0]);token=s.create()
 now[0]=4;assert s.get(token,False)
 now[0]=5;assert s.get(token,False) is None

def test_backup_restore_and_tamper(tmp_path):
 db=tmp_path/'data'/'test.sqlite3';db.parent.mkdir();s=Store(db);s.put('synthetic','one',{'synthetic':True});s.close()
 manifest=protection.verified_backup(db,tmp_path/'backup');assert manifest['state']['record_count']==1
 result=protection.restore_backup(tmp_path/'backup',tmp_path/'restored');assert result['state']==manifest['state']
 with (tmp_path/'backup'/'vigile.sqlite3').open('ab') as f:f.write(b'tampered')
 with pytest.raises(ValueError,match='BACKUP_HASH'):protection.restore_backup(tmp_path/'backup',tmp_path/'bad')

@pytest.mark.skipif(sys.platform!='win32',reason='Windows DPAPI')
def test_dpapi_and_external_anchor(tmp_path):
 secret=tmp_path/'secret';protection.protect_secret('synthetic-test-only',secret)
 assert 'synthetic-test-only' not in secret.read_text();assert protection.read_secret(secret)=='synthetic-test-only'
 with pytest.raises(FileExistsError):protection.protect_secret('other',secret)
 db=tmp_path/'data'/'test.sqlite3';db.parent.mkdir();s=Store(db);s.put('synthetic','one',{'synthetic':True});s.close()
 anchor=tmp_path/'integrity'/'anchor.json';key=tmp_path/'integrity'/'key.dpapi'
 protection.anchor_database(db,anchor,key);assert protection.verify_anchor(db,anchor,key)['valid']
 s=Store(db);s.put('synthetic','two',{'synthetic':True});s.close();assert protection.verify_anchor(db,anchor,key)['valid']
 value=json.loads(anchor.read_text());value['signed']['checkpoint']['record_count']=42;anchor.write_text(json.dumps(value))
 with pytest.raises(ValueError,match='AUTHENTICATION'):protection.verify_anchor(db,anchor,key)
 with pytest.raises(ValueError,match='OUTSIDE'):protection.anchor_database(db,db.parent/'anchor',key)


def test_recomputed_audit_cannot_match_external_anchor(tmp_path):
 from vigile.store import digest,canonical
 if sys.platform!='win32':pytest.skip('Windows DPAPI')
 db=tmp_path/'data'/'test.sqlite3';db.parent.mkdir();s=Store(db);s.put('synthetic','one',{'value':1});s.close()
 anchor=tmp_path/'external'/'anchor';key=tmp_path/'external'/'key'
 protection.anchor_database(db,anchor,key)
 c=sqlite3.connect(db);c.execute('DROP TRIGGER records_no_update');c.execute('DROP TRIGGER audit_no_update')
 payload={'value':2};c.execute('UPDATE records SET payload=?',(canonical(payload),))
 previous='0'*64
 for seq,raw in c.execute('SELECT seq,payload FROM audit ORDER BY seq').fetchall():
  event=json.loads(raw);event['data']['content_hash']=digest(payload);current=digest({'previous':previous,'payload':event})
  c.execute('UPDATE audit SET payload=?,previous=?,hash=? WHERE seq=?',(canonical(event),previous,current,seq));previous=current
 c.commit();c.close();s=Store(db);assert s.verify();s.close()
 with pytest.raises(ValueError,match='ANCHORED_PREFIX_MISMATCH'):protection.verify_anchor(db,anchor,key)

def test_encryption_capability_does_not_claim_plain_sqlite_encrypted():
 encrypted=module('encrypted_storage');assert encrypted.capabilities()['active_database_encrypted'] is False
 with pytest.raises(ValueError,match='256_BIT'):encrypted.open_sqlcipher(':memory:','invalid')
