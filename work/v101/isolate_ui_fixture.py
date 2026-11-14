from pathlib import Path
import json
R=Path(__file__).resolve().parents[2];folder=R/'engine/tests/fixtures';folder.mkdir(exist_ok=True)
r=json.loads((R/'engine/data/mission-v101-management/management-report.json').read_text(encoding='utf8'))
value={'synthetic':True,'clinical_validation':False,'scenarios':r['scenarios'],'management_records':r['management_records'],'monitoring':{'clinical_evaluations':{'DKA':r['monitoring']['clinical_evaluations']['DKA']}}}
(folder/'management-v101-report.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
p=R/'engine/tests/management_ui_unit.cjs';s=p.read_text(encoding='utf8').replace("'../data/mission-v101-management/management-report.json'","'fixtures/management-v101-report.json'");p.write_text(s,encoding='utf8')
p=R/'engine/tests/test_management_v101.py';s=p.read_text(encoding='utf8').replace(" assert 'selected?.management' in js and 'AUTHORIZATION' not in js or 'authority_verification' in js"," assert 'selected?.management' in js and 'authority_verification' in js");s=s.replace("Path(__file__).resolve().parents[1]/'data/mission-v101-management/management-report.json'","Path(__file__).with_name('fixtures')/'management-v101-report.json'");p.write_text(s,encoding='utf8')