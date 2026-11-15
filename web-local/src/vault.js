const FORMAT='ASTHRAL-ENCRYPTED-SQLITE-1';
const ITERATIONS=600000;
const MAX_BYTES=32*1024*1024;
const encoder=new TextEncoder();
const emailAAD=id=>encoder.encode(FORMAT+'|local-identifier|'+id);
function canonicalEmail(value) {
  const email=String(value??'').trim().toLowerCase();
  if(email.length>254||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw Error('Enter a valid email address.');
  return email;
}

function base64(bytes) {
  let value='';
  for(let i=0;i<bytes.length;i+=8192) value+=String.fromCharCode(...bytes.subarray(i,i+8192));
  return btoa(value);
}
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
function open() {
  return new Promise((resolve,reject)=>{
    const request=indexedDB.open('asthral-encrypted-profiles',1);
    request.onupgradeneeded=()=>request.result.createObjectStore('profiles',{keyPath:'id'});
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
}
async function read(id) {
  const db=await open();
  try {
    return await new Promise((resolve,reject)=>{
      const request=db.transaction('profiles').objectStore('profiles').get(id);
      request.onsuccess=()=>resolve(request.result);
      request.onerror=()=>reject(request.error);
    });
  } finally { db.close(); }
}
async function write(row,expected,admit=()=>true) {
  const db=await open();
  try {
    await new Promise((resolve,reject)=>{
      const transaction=db.transaction('profiles','readwrite');
      const store=transaction.objectStore('profiles');
      const request=store.get(row.id);
      request.onsuccess=()=>{
        if(!admit()||(request.result?.revision??0)!==expected) { transaction.abort(); return; }
        store.put(row);
      };
      transaction.oncomplete=resolve;
      transaction.onerror=()=>reject(transaction.error);
      transaction.onabort=()=>reject(Error('Concurrent change or existing profile. Lock and unlock the latest profile.'));
    });
  } finally { db.close(); }
}
async function derive(password,salt) {
  if(password.length<14||password.length>256) throw Error('Passphrase must contain 14 to 256 characters.');
  const material=await crypto.subtle.importKey('raw',encoder.encode(password),'PBKDF2',false,['deriveKey']);
  return crypto.subtle.deriveKey(
    {name:'PBKDF2',hash:'SHA-256',salt,iterations:ITERATIONS},
    material,{name:'AES-GCM',length:256},false,['encrypt','decrypt']
  );
}
const associatedData=row=>encoder.encode(FORMAT+'|'+row.id+'|'+row.revision);

export class Vault {
  constructor(row,key) { this.row=row; this.key=key; this.locked=false; }
  static async list() {
    const db=await open();
    try {
      return await new Promise((resolve,reject)=>{
        const request=db.transaction('profiles').objectStore('profiles').getAll();
        request.onsuccess=()=>resolve(request.result.map(({id,label})=>({id,label})));
        request.onerror=()=>reject(request.error);
      });
    } finally { db.close(); }
  }
  static async create(label,password,id) {
    const salt=crypto.getRandomValues(new Uint8Array(16));
    const row={format:FORMAT,id,label:label.slice(0,60),salt:base64(salt),iterations:ITERATIONS,revision:0};
    return new Vault(row,await derive(password,salt));
  }
  static async createLocalAccount(email,password,id) {
    const normalized=canonicalEmail(email);
    const salt=crypto.getRandomValues(new Uint8Array(16));
    const row={format:FORMAT,id,label:'Local account',salt:base64(salt),iterations:ITERATIONS,revision:0};
    const key=await derive(password,salt);
    row.email_box=await Vault.sealEmail(normalized,id,key);
    return new Vault(row,key);
  }
  static async sealEmail(email,id,key) {
    const iv=crypto.getRandomValues(new Uint8Array(12));
    const ciphertext=await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:emailAAD(id)},key,encoder.encode(email));
    return {iv:base64(iv),ciphertext:base64(new Uint8Array(ciphertext))};
  }
  static async unlockByEmail(email,password) {
    const wanted=canonicalEmail(email),db=await open();
    let rows;
    try { rows=await new Promise((resolve,reject)=>{const request=db.transaction('profiles').objectStore('profiles').getAll();request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);}); }
    finally { db.close(); }
    for(const row of rows) {
      if(!row.email_box) continue;
      Vault.validate(row);
      let key;
      try {
        key=await derive(password,decode(row.salt));
        const data=await crypto.subtle.decrypt({name:'AES-GCM',iv:decode(row.iv),additionalData:associatedData(row)},key,decode(row.ciphertext));
        const email=await crypto.subtle.decrypt({name:'AES-GCM',iv:decode(row.email_box.iv),additionalData:emailAAD(row.id)},key,decode(row.email_box.ciphertext));
        if(new TextDecoder().decode(email)===wanted) return {vault:new Vault(row,key),database:new TextDecoder().decode(data)};
      } catch { /* A different password/profile is expected while scanning local encrypted records. */ }
    }
    throw Error('No local profile matched those credentials. Local accounts have no online password reset.');
  }
  static async unlock(id,password) {
    const row=await read(id);
    if(!row) throw Error('Profile unavailable.');
    Vault.validate(row);
    const key=await derive(password,decode(row.salt));
    try {
      const data=await crypto.subtle.decrypt(
        {name:'AES-GCM',iv:decode(row.iv),additionalData:associatedData(row)},key,decode(row.ciphertext)
      );
      return {vault:new Vault(row,key),database:new TextDecoder().decode(data)};
    } catch { throw Error('Passphrase incorrect or encrypted data damaged.'); }
  }
  static validate(row) {
    if(row.format!==FORMAT||row.iterations!==ITERATIONS||!/^profile-[a-f0-9-]{36}$/.test(row.id)||
      !Number.isSafeInteger(row.revision)||row.revision<1||typeof row.ciphertext!=='string'||
      row.ciphertext.length>MAX_BYTES||decode(row.salt).length!==16||decode(row.iv).length!==12) {
      throw Error('Unsupported or damaged encrypted export.');
    }
    if(row.email_box && (typeof row.email_box.iv!=='string'||typeof row.email_box.ciphertext!=='string'||decode(row.email_box.iv).length!==12||row.email_box.ciphertext.length>1024)) throw Error('Unsupported or damaged encrypted export.');
  }
  async setLocalEmail(email) {
    if(this.locked) throw Error('Local profile locked.');
    const normalized=canonicalEmail(email),row={...this.row,email_box:await Vault.sealEmail(normalized,this.row.id,this.key)};
    await write(row,this.row.revision,()=>!this.locked);
    this.row=row;
  }
  async save(database) {
    if(this.locked) throw Error('Local profile locked.');
    const plaintext=encoder.encode(database);
    if(plaintext.length>MAX_BYTES) throw Error('Profile exceeds the supported local size. Export and review storage.');
    const quota=await navigator.storage?.estimate?.();
    if(quota?.quota&&quota.quota-quota.usage<plaintext.length*2) throw Error('Insufficient browser storage. Export before continuing.');
    const row={...this.row,revision:this.row.revision+1,iv:base64(crypto.getRandomValues(new Uint8Array(12)))};
    const encrypted=await crypto.subtle.encrypt(
      {name:'AES-GCM',iv:decode(row.iv),additionalData:associatedData(row)},this.key,plaintext
    );
    row.ciphertext=base64(new Uint8Array(encrypted));
    await write(row,this.row.revision,()=>!this.locked);
    this.row=row;
  }
  export() { return JSON.stringify(this.row); }
  static async recover(text) {
    if(text.length>MAX_BYTES) throw Error('Export exceeds supported size.');
    const row=JSON.parse(text);
    Vault.validate(row);
    if(await read(row.id)) throw Error('Profile already exists. Restore into another browser or back up and remove its local copy first.');
    await write(row,0);
    return row.id;
  }
  async remove() {
    const db=await open();
    try {
      await new Promise((resolve,reject)=>{
        const transaction=db.transaction('profiles','readwrite');
        transaction.objectStore('profiles').delete(this.row.id);
        transaction.oncomplete=resolve;
        transaction.onerror=()=>reject(transaction.error);
      });
    } finally { db.close(); }
    this.key=null;
  }
  lock() { this.locked=true; this.key=null; }
}
