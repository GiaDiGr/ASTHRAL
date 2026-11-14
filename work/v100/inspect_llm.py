from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
for name in ('llm-before','llm-after'):
 p=root/('docs/v100/'+name+'.json')
 if p.exists():
  report=json.loads(p.read_text(encoding='utf8'))
  for r in report['rows']:
   print(name,r['kind'],r['response']['status'],r['raw_model_calls'])
   print('facts',r['response'].get('structured_facts',[])[:1])