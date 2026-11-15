import test from 'node:test';
import assert from 'node:assert/strict';
const {indexedDB}=await import(process.env.FAKE_INDEXEDDB_MODULE||'fake-indexeddb');
Object.defineProperty(globalThis,'indexedDB',{value:indexedDB});
Object.defineProperty(globalThis,'navigator',{value:{storage:{estimate:async()=>({quota:1000000000,usage:0})}}});
const {Vault}=await import('../src/vault.js');
const password='Synthetic-only passphrase for tests';
const id=()=> 'profile-'+crypto.randomUUID();

test('different local profiles have different salts and cannot unlock each other',async()=>{
  const a=await Vault.create('Synthetic A',password,id());
  const b=await Vault.create('Synthetic B','Different synthetic passphrase',id());
  await a.save('PRIVATE_SYNTHETIC_A');
  await b.save('PRIVATE_SYNTHETIC_B');
  assert.notEqual(a.row.salt,b.row.salt);
  assert.ok(!a.export().includes('PRIVATE_SYNTHETIC_A'));
  assert.ok(!a.export().includes(password));
  assert.equal((await Vault.unlock(a.row.id,password)).database,'PRIVATE_SYNTHETIC_A');
  await assert.rejects(Vault.unlock(b.row.id,password));
  assert.equal((await Vault.unlock(b.row.id,'Different synthetic passphrase')).database,'PRIVATE_SYNTHETIC_B');
  a.lock();
  await assert.rejects(a.save('LATE_WRITE'));
});
test('encrypted export recovers after local deletion and rejects accidental overwrite',async()=>{
  const a=await Vault.create('Recovery fixture',password,id());
  await a.save('SYNTHETIC_RECOVERY');
  const backup=a.export();
  await assert.rejects(Vault.recover(backup));
  await a.remove();
  await Vault.recover(backup);
  assert.equal((await Vault.unlock(a.row.id,password)).database,'SYNTHETIC_RECOVERY');
});
test('stale tabs cannot overwrite a newer encrypted revision',async()=>{
  const a=await Vault.create('Concurrent fixture',password,id());
  await a.save('first');
  const second=(await Vault.unlock(a.row.id,password)).vault;
  await a.save('newer');
  await assert.rejects(second.save('stale'));
  assert.equal((await Vault.unlock(a.row.id,password)).database,'newer');
});
test('tampered ciphertext fails authentication after recovery',async()=>{
  const a=await Vault.create('Tamper fixture',password,id());
  await a.save('SYNTHETIC_SECRET');
  const row=JSON.parse(a.export());
  row.ciphertext=(row.ciphertext[0]==='A'?'B':'A')+row.ciphertext.slice(1);
  await a.remove();
  await Vault.recover(JSON.stringify(row));
  await assert.rejects(Vault.unlock(row.id,password));
});
test('import policies reject unsupported KDF and schema versions',async()=>{
  const a=await Vault.create('Version fixture',password,id());
  await a.save('fixture');
  const row=JSON.parse(a.export());
  row.iterations=1;
  await assert.rejects(Vault.recover(JSON.stringify(row)));
  row.iterations=600000;
  row.format='UNKNOWN';
  await assert.rejects(Vault.recover(JSON.stringify(row)));
});
test('a profile locked while encryption is pending cannot commit the late write',async()=>{
  const a=await Vault.create('Pending fixture',password,id());
  await a.save('committed');
  const pending=a.save('late');
  a.lock();
  await assert.rejects(pending);
  assert.equal((await Vault.unlock(a.row.id,password)).database,'committed');
});
test('local email sign-in remains encrypted, device-local and compatible with legacy profile keys',async()=>{
  const email='synthetic.astronaut@example.test',a=await Vault.createLocalAccount(email,password,id());
  await a.save('SYNTHETIC_ACCOUNT_DATA');
  const exportText=a.export();
  assert.ok(!exportText.includes(email));
  const opened=await Vault.unlockByEmail('SYNTHETIC.ASTRONAUT@example.test',password);
  assert.equal(opened.database,'SYNTHETIC_ACCOUNT_DATA');
  await assert.rejects(Vault.unlockByEmail(email,'wrong synthetic password'));
  await assert.rejects(Vault.unlockByEmail('other@example.test',password));
  const legacy=await Vault.create('Legacy label',password,id());
  await legacy.save('SYNTHETIC_LEGACY_DATA');
  const previousRevision=legacy.row.revision;
  await legacy.setLocalEmail('migrated@example.test');
  assert.equal(legacy.row.revision,previousRevision);
  assert.equal((await Vault.unlock(legacy.row.id,password)).database,'SYNTHETIC_LEGACY_DATA');
  assert.equal((await Vault.unlockByEmail('migrated@example.test',password)).database,'SYNTHETIC_LEGACY_DATA');
  assert.ok(!legacy.export().includes('migrated@example.test'));
});
