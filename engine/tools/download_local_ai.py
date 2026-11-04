from pathlib import Path
import urllib.request,hashlib,json,zipfile,time
root=Path(__file__).resolve().parents[2];dest=root/'engine/local_ai';dest.mkdir(exist_ok=True)
items=[('llama-b11721-bin-win-vulkan-x64.zip','https://github.com/ggml-org/llama.cpp/releases/download/b11721/llama-b11721-bin-win-vulkan-x64.zip','b2dab62833cc07aae4a1f28752874668b6a98d304a7f8ca6c1421a0d1e1a7075',32315391),('Qwen3-4B-Instruct-2507-Q4_K_M.gguf','https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF/resolve/4edb920b6f14e3b9284d4502a6485103d72cde05/Qwen3-4B-Instruct-2507-Q4_K_M.gguf','8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc',2497280448)]
manifest=[]
for name,url,expected,size in items:
 p=dest/name
 if not p.exists():
  print('Downloading '+name,flush=True)
  with urllib.request.urlopen(url,timeout=120) as source,p.with_suffix(p.suffix+'.part').open('wb') as target:
   last=time.monotonic();total=0
   while chunk:=source.read(4*1024*1024):
    target.write(chunk);total+=len(chunk)
    if time.monotonic()-last>20:print(f'{name}: {total}/{size} bytes',flush=True);last=time.monotonic()
  p.with_suffix(p.suffix+'.part').rename(p)
 h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
 if h!=expected or p.stat().st_size!=size:raise ValueError('DOWNLOAD_INTEGRITY_FAILURE '+name)
 manifest.append({'file':name,'url':url,'sha256':h,'bytes':size})
 if p.suffix=='.zip':
  runtime=dest/'llama-b11721'
  if runtime.exists():
   if not (runtime/'llama-server.exe').is_file():raise RuntimeError('EXISTING_RUNTIME_INCOMPLETE_REVIEW_SECURITY_NO_AUTOMATIC_RESTORE')
  else:
   runtime.mkdir()
   with zipfile.ZipFile(p) as z:
    for member in z.infolist():
     if not (runtime/member.filename).resolve().is_relative_to(runtime.resolve()):raise ValueError('UNSAFE_ARCHIVE')
    z.extractall(runtime)
(dest/'download-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for name,url in [('QWEN-LICENSE','https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/raw/main/LICENSE'),('LLAMA-LICENSE','https://raw.githubusercontent.com/ggml-org/llama.cpp/b11721/LICENSE')]:
 with urllib.request.urlopen(url,timeout=30) as r:(dest/name).write_bytes(r.read())
print('Verified runtime and model',flush=True)
