from pathlib import Path
import json,statistics
R=Path(__file__).resolve().parents[2]
for name in ['voice-benchmark/results.json','e2e-final/results.json','e2e-r2/results.json']:
 p=R/'docs/v100'/name
 if not p.exists():continue
 r=json.loads(p.read_text(encoding='utf8'));print(name,'rows',len(r['rows']),'keys',list(r['rows'][0]))
 if 'summary' in r:print(r['summary'])
 if 'monitoring_replays' in r:print('replays',len(r['monitoring_replays']),len(r['clinical_replays']),r['audit_valid'])
 print('before',r.get('before'),'after',r.get('after'))