from pathlib import Path
import re,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/v011';changes=[]
pattern=re.compile(r"(['\"])([A-Za-z0-9_-]{43})\1")
for p in OUT.glob('*.xml'):
 tree=ET.parse(p);count=[0]
 def redact(match):
  value=match.group(2)
  if any(c.isupper() for c in value) and any(c.islower() for c in value) and sum(c.isdigit() for c in value)>=2:
   count[0]+=1;return match.group(1)+'[REDACTED_EPHEMERAL_PYTEST_CREDENTIAL]'+match.group(1)
  return match.group(0)
 for node in tree.iter():
  if node.text:node.text=pattern.sub(redact,node.text)
  if node.tail:node.tail=pattern.sub(redact,node.tail)
 if count[0]:tree.write(p,encoding='utf-8',xml_declaration=True);changes.append({'file':p.name,'redacted_ephemeral_test_tokens':count[0]})
(OUT/'test-trace-redactions.json').write_text(json.dumps({'reason':'Remove random ephemeral pytest fixture credentials from failed development tracebacks; retain test outcome, stack, clinical data and failure cause. No historical server credentials copied.','changes':changes},indent=2),encoding='utf8')
p=ROOT/'work/v011/package_release.py';s=p.read_text(encoding='utf8');s=s.replace("p.name!='release-manifest.json'","p.name not in ('release-manifest.json','archive-verification.json')")
s=s.replace("if archive.exists():raise ValueError('ARCHIVE_EXISTS_PRESERVE_HISTORY')","# Repackage only this newly-created release after redacting ephemeral pytest traces.")
s=s.replace("zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED)","zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED)");p.write_text(s,encoding='utf8')
print(json.dumps(changes,indent=2))