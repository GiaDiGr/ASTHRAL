"""Local credential provisioning. Server stores hashes; private client export is separate."""
import hashlib,json,secrets
from pathlib import Path

def provision(data):
    data=Path(data); data.mkdir(exist_ok=True)
    server=data/'tokens.json'; clients=data/'client-credentials.json'
    existing=json.loads(server.read_text(encoding='utf-8')) if server.exists() else {
        secrets.token_urlsafe(32):role for role in ('reader','operator','researcher','clinician')}
    if existing and all(k.startswith('sha256:') for k in existing): return
    if clients.exists(): raise ValueError('Client export exists; review credentials before migrating')
    mapping={}
    for token,role in existing.items():
        if not isinstance(role,str): raise ValueError('Manual migration required for custom descriptors')
        fingerprint=hashlib.sha256(token.encode()).hexdigest()
        mapping['sha256:'+fingerprint]={'id':'local-'+role,'role':role,
            'subject_ids':[] if role=='reader' else ['*'],
            'mission_ids':[] if role=='reader' else ['*'],'disabled':False}
    with clients.open('x',encoding='utf-8') as f: json.dump(existing,f,indent=2)
    temporary=data/'tokens.migration.tmp'
    with temporary.open('x',encoding='utf-8') as f: json.dump(mapping,f,indent=2)
    temporary.replace(server)
