from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[2]
# Expose only the reviewed corpus files, not every original report/archive in their folders.
p=R/'.gitignore';s=p.read_text(encoding='utf8')
paths=[row['path'] for row in json.loads((R/'ASTHRAL_CORPUS_SHA256.json').read_text(encoding='utf8'))]
for directory in sorted({path.split('/')[0] for path in paths}):s+='\n/'+directory+'/**\n'
for parent in sorted({str(Path(path).parent).replace('\\','/') for path in paths if len(Path(path).parts)>2}):s+='!/'+parent+'/\n'
for path in sorted(paths):s+='!/'+path+'\n'
s+='\n!/engine/Modelfile.example\n!/docs/v101/\n/docs/v101/*\n!/docs/v101/CODE_FREEZE.json\n!/docs/asthral/verification-summary.json\n'
p.write_text(s,encoding='utf8')
print('Reviewable publication manifest restricted to source, exact computable corpus, English docs and safe examples')