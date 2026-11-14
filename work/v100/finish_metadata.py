from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
manifest=json.loads((R/'docs/v100/voice-model-downloads.json').read_text())
(R/'engine/vigile/voice_assets/models.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
p=R/'engine/vigile/voice.py';s=p.read_text();s=s.replace("else root/'manifest.json'","else Path(__file__).with_name('voice_assets')/'models.json'");p.write_text(s,encoding='utf8')
for rel in ['engine/vigile/api.py','engine/vigile/portal.py','engine/vigile/web/index.html','engine/pyproject.toml']:
 p=R/rel;s=p.read_text(encoding='utf8');p.write_text(s.replace('0.11.0','1.0.0'),encoding='utf8')
p=R/'engine/pyproject.toml';s=p.read_text();s=s.replace('[project.optional-dependencies]','[project.optional-dependencies]\nvoice = ["vosk==0.3.45"]');s=s.replace('"web/*"]','"web/*", "voice_assets/*.ps1", "voice_assets/*.json"]');p.write_text(s,encoding='utf8')