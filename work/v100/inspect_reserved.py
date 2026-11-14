from pathlib import Path
import json,statistics
R=Path(__file__).resolve().parents[2]
r=json.loads((R/'docs/v100/reserved/results.json').read_text(encoding='utf8'));print('RESERVED',r['total'],r['generated_cases'],r['errors'],r['clinical_outputs_unchanged'],r['audit_valid'])
for row in r['rows']:
 reply=row.get('response',{});print(row['case']['id'],row['case']['question'],row['case'].get('expected'),row.get('status'),reply.get('reason'),reply.get('failure_trace'))
 for g in reply.get('generated',[]):print(g['text'])