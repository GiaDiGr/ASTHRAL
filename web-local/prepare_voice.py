"""Package the already-reviewed English Vosk model into Pages-sized public chunks."""
from pathlib import Path
import base64
import gzip
import hashlib
import httpx
import io
import json
import ssl
import tarfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'engine/local_ai/voice'
OUT=ROOT/'web-local/src/voice-assets'
def main():
    specification=json.loads((ROOT/'engine/vigile/voice_assets/models.json').read_bytes())['models'][0]
    if specification['language']!='en' or specification['license']!='Apache-2.0':raise ValueError('UNREVIEWED_VOICE_MODEL')
    buffer=io.BytesIO()
    with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w') as archive:
            for row in specification['files']:
                relative=Path(row['path'].replace('\\','/'))
                file=SOURCE/relative
                raw=file.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('VOICE_SOURCE_HASH_MISMATCH')
                name='model/'+relative.relative_to(specification['model']).as_posix()
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o644;item.mtime=0
                archive.addfile(item,io.BytesIO(raw))
    raw=buffer.getvalue()
    OUT.mkdir(exist_ok=True)
    parts=[]
    for number,offset in enumerate(range(0,len(raw),8*1024*1024)):
        name=f'part-{number:02}.bin';data=raw[offset:offset+8*1024*1024]
        (OUT/name).write_bytes(data)
        parts.append({'path':'voice-assets/'+name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    with httpx.Client(verify=ssl.create_default_context(),trust_env=False,timeout=30,follow_redirects=True) as client:
        metadata=client.get('https://registry.npmjs.org/vosk-browser/0.0.8').raise_for_status().json()
        data=client.get(metadata['dist']['tarball']).raise_for_status().content
        expected='sha512-df9MuChirUGKxP/+4k8tBV6hJOic8IRdJXv64+ET0Ue5CddOzLZINiHOWCka765gBzHJWNtQKgaYakS0FXZIJA=='
        if 'sha512-'+base64.b64encode(hashlib.sha512(data).digest()).decode()!=expected:raise ValueError('VOSK_RUNTIME_INTEGRITY_FAILED')
        with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
            (ROOT/'web-local/src/vosk.js').write_bytes(archive.extractfile('package/dist/vosk.js').read())
    manifest={'model':specification['model'],'license':specification['license'],'source':specification['url'],
              'original_archive_sha256':specification['sha256'],'bytes':len(raw),
              'sha256':hashlib.sha256(raw).hexdigest(),'parts':parts,'runtime':'vosk-browser-0.0.8'}
    (ROOT/'web-local/src/voice-model.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps({'bytes':len(raw),'chunks':len(parts),'model':specification['model']}))
if __name__=='__main__':main()
