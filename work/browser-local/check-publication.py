"""Offline publication scan of the complete current Git index; never prints secret values."""
from pathlib import Path
import io,json,os,re,subprocess,zipfile
ROOT=Path.cwd()
paths=[p for p in subprocess.check_output(["git","ls-files","-z"],cwd=ROOT).decode().split("\0") if p]
text_ext={".py",".js",".mjs",".cjs",".html",".css",".md",".txt",".json",".csv",".xml",".yaml",".yml",".toml",".ini",".ps1",".bat",".cmd",".sh",".svg",".webmanifest",".lock",".conf",".modelfile"}
patterns=[("github_token",re.compile(rb"(?i)(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})")),("private_key",re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),("openai_or_anthropic_key",re.compile(rb"(?i)(?<![A-Za-z0-9])sk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}")),("google_api_key",re.compile(rb"AIza[0-9A-Za-z_-]{35}")),("cloudflare_api_token",re.compile(rb"(?i)(?:CLOUDFLARE_API_TOKEN|CF_API_TOKEN)\s*[:=]\s*[\"']?[A-Za-z0-9_-]{30,}"))]
blocked_parts={".venv","venv","node_modules","__pycache__",".pytest_cache",".wrangler","tts-toolchain"}
blocked_suffixes=(".sqlite",".sqlite3",".db",".dpapi",".gguf",".onnx",".pyc",".pyd",".exe",".dll",".log")
findings=[];scanned=0;archives=0;oversized=[]
for p in paths:
 low=p.lower();parts=set(low.replace("\\","/").split("/"))
 if parts&blocked_parts: findings.append([p,"environment_or_cache"])
 if low.endswith(blocked_suffixes): findings.append([p,"local_database_or_runtime_binary"])
 if low.endswith((".env",".dpapi","runtime-key.txt")) or "portal-access" in low or "portal-config" in low or re.search(r"(^|/)\.env(?:\.|$)",low): findings.append([p,"local_credential_or_config"])
 try:
  size=os.path.getsize(p)
  if size>=100*1024*1024: oversized.append([p,size])
 except OSError: findings.append([p,"missing_index_file"]);continue
 if low.endswith(".zip"):
  try:
   with zipfile.ZipFile(p) as z:
    for m in z.infolist():
     name=m.filename.lower()
     if m.is_dir(): continue
     if name.endswith(blocked_suffixes) or any(x in name for x in ("portal-access","portal-config","runtime-key",".env")): findings.append([p+"!/"+m.filename,"sensitive_archive_member"]);continue
     if m.file_size>20*1024*1024 or Path(name).suffix not in text_ext: continue
     raw=z.read(m)
     for label,pat in patterns:
      if pat.search(raw): findings.append([p+"!/"+m.filename,label])
   archives+=1;scanned+=1
  except Exception: findings.append([p,"unreadable_archive"])
 elif Path(low).suffix in text_ext:
  try: raw=Path(p).read_bytes()
  except OSError: findings.append([p,"unreadable_index_file"]);continue
  scanned+=1
  for label,pat in patterns:
   if pat.search(raw): findings.append([p,label])
report={"scope":"complete current Git index","repository_visibility":"private, asserted by owner","tracked_paths":len(paths),"text_and_archives_scanned":scanned,"archives_scanned":archives,"oversized_files":oversized,"findings":findings}
out=ROOT/"work/browser-local/publication-check.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2),encoding="utf-8")
if findings or oversized: raise SystemExit("Publication scan found issues; inspect local report (values are never emitted).")
print(json.dumps({k:v for k,v in report.items() if k!="findings"}))
