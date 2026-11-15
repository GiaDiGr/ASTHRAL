"""Install versioned Apache-2.0 MediaPipe browser pose assets with pinned hashes."""
import base64,hashlib,io,json,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NPM_URL='https://registry.npmjs.org/@mediapipe/tasks-vision/-/tasks-vision-0.10.21.tgz'
NPM_SHA512='TuhKH+credq4zLksGbYrnvJ1aLIWMc5r0UHwzxzql4BHECJwIAoBR61ZrqwGOW6ZmSBIzU1t4VtKj8hbxFaKeA=='
MODEL_URL='https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'
MODEL_SHA256='59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a'
LICENSE_URL='https://raw.githubusercontent.com/google-ai-edge/mediapipe/v0.10.21/LICENSE'
LICENSE_SHA256='8707eef0533987efc5b155d64761eeb6e20793f50b9bd1a68dad1cf4719d0ed8'
TARGET=ROOT/'web-local/src/motion-runtime'
def put(relative,raw):
 path=TARGET/relative;path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=raw:raise ValueError('EXISTING_ASSET_MISMATCH:'+relative)
 path.write_bytes(raw)
 return {'path':relative,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
if __name__=='__main__':
 raw=urllib.request.urlopen(NPM_URL,timeout=60).read()
 if base64.b64encode(hashlib.sha512(raw).digest()).decode()!=NPM_SHA512:raise ValueError('NPM_ARCHIVE_INTEGRITY_FAILED')
 archive=tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz');names=['vision_bundle.mjs','wasm/vision_wasm_internal.js','wasm/vision_wasm_internal.wasm','wasm/vision_wasm_nosimd_internal.js','wasm/vision_wasm_nosimd_internal.wasm']
 files=[put(name,archive.extractfile('package/'+name).read()) for name in names]
 model=urllib.request.urlopen(MODEL_URL,timeout=60).read()
 if hashlib.sha256(model).hexdigest()!=MODEL_SHA256:raise ValueError('POSE_MODEL_INTEGRITY_FAILED')
 files.append(put('pose_landmarker_lite.task',model))
 license_bytes=urllib.request.urlopen(LICENSE_URL,timeout=60).read()
 if hashlib.sha256(license_bytes).hexdigest()!=LICENSE_SHA256:raise ValueError('POSE_LICENSE_INTEGRITY_FAILED')
 put('LICENSE.txt',license_bytes)
 metadata={'runtime':'@mediapipe/tasks-vision','version':'0.10.21','license':'Apache-2.0','archive':NPM_URL,'archive_sha512_base64':NPM_SHA512,'model':MODEL_URL,'model_sha256':MODEL_SHA256,'model_card':'https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf','license_source':'https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE','files':files,'clinical_validation':False}
 put('manifest.json',(json.dumps(metadata,indent=2)+'\n').encode());print(json.dumps({'files':len(files),'bytes':sum(x['size'] for x in files),'runtime':metadata['runtime'],'version':metadata['version']}))
