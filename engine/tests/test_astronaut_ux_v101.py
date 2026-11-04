"""Presentation-only integration tests on existing, synthetic mission cases."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import pytest
from conftest import ROOT
from test_mission_v011 import mission,frame
from vigile.mission_demo import SUBJECTS,MID
from vigile.registry import Registry


def test_astronaut_actual_assets_simulated_dom(mission,tmp_path):
    c=mission[0];frames={name:frame(mission,sid,day) for name,sid,day in [('a35',SUBJECTS[0],35),('a21',SUBJECTS[0],21),('b18',SUBJECTS[1],18),('b47',SUBJECTS[1],47)]}
    frames['index']=c.app.state.engine.store.all('mission_frame');frames['index']=[r['index'] for r in frames['index']]
    p=tmp_path/'synthetic-frames.json';p.write_text(json.dumps(frames),encoding='utf8')
    node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    if not Path(node).exists():pytest.skip('Node unavailable; simulated DOM cannot be executed')
    result=subprocess.run([node,str(Path(__file__).with_name('astronaut_ui_unit.cjs')),str(p)],capture_output=True,text=True,encoding='utf8',timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    assert json.loads(result.stdout)['simulated_DOM_cases']==13


def test_ux_reuses_exact_catalogue_excerpts():
    text=(ROOT/'engine/vigile/web/management.js').read_text(encoding='utf8');start=text.index('const astronautGuideCatalogue=')+len('const astronautGuideCatalogue=');data=json.JSONDecoder().raw_decode(text[start:])[0];r=Registry(ROOT)
    for cid,v in data.items():
        if cid=='sources':continue
        original=r.get('conditions',cid)
        translations=json.loads((ROOT/'engine/vigile/web/translations-en.json').read_text(encoding='utf8'))
        assert v=={'name':translations.get(original['catalog_record']['name_specialty'],original['catalog_record']['name_specialty']),'context':translations.get(original['catalog_record']['description_spaceflight'],original['catalog_record']['description_spaceflight']),'source_ids':original['source_ids']}
    assert all(source['source_id']==r.get('sources',sid)['source_id'] for sid,source in data['sources'].items()) # Original record remains in the immutable catalogue.


def test_ux_keeps_python_engine_and_clinical_knowledge_unchanged():
    freeze=json.loads((ROOT/'docs/v101/CODE_FREEZE.json').read_text(encoding='utf8'))
    for row in freeze['files']:
        if row['path'].startswith('engine/vigile/') and (row['path'] in ('engine/vigile/clinical_engine.py','engine/vigile/clinical_logic.py','engine/vigile/monitoring.py','engine/vigile/management.py') or '/clinical_knowledge/' in row['path']):
            assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']


def test_ux_navigation_does_not_add_write_or_external_requests():
    text=(ROOT/'engine/vigile/web/management.js').read_text(encoding='utf8')
    assert 'fetch(' not in text and 'innerHTML' not in text and 'XMLHttpRequest' not in text
    assert "evaluationOrigin(id)" in text and "guideScope()!==scope" in text
    assert "'journey-links','journey-evaluation'" in (ROOT/'engine/vigile/web/app.js').read_text(encoding='utf8')


def test_longitudinal_urgent_management_and_followup_are_same_scope(mission):
    data=frame(mission,SUBJECTS[1],18);cycle=data['monitoring'][-1];evaluation=cycle['clinical_evaluations']['DKA'];result=evaluation['results']['DKA']
    assert result['diagnostic_status']=='CRITERIA_MET' and result['urgency']=='EMERGENCY'
    assert 'potassium_mmol_l' in result['required_for_protocol_safety']
    assert not result['missing_required'] and {'bicarbonate_mmol_l','urine_ketones_plus'}<=set(result['optional_not_measured'])
    view=evaluation['management']['DKA'];assert view['clinical_execution']=='BLOCKED'
    assert all(i['authorization']=='AUTHORIZATION_REQUIRED' and not i['execution_enabled'] for i in view['interventions'])
    episode_ids={e['id'] for e in data['episodes']};assert all(f['episode_id'] in episode_ids for f in data['followups'])
    assert cycle['subject_id']==data['profile']['id']==SUBJECTS[1] and cycle['mission_id']==MID