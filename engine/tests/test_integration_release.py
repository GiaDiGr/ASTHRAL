import json,socket,hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from vigile.simulator import generate,SyntheticDataset
from vigile.adapters import SyntheticAdapter,LocalClient
from vigile.api import create_app
from vigile.integration import exercise,run,deny_external_network
from vigile.store import Store,digest
from conftest import ROOT

WRITE='synthetic-bootstrap-token-32-characters'
READ='synthetic-rag-token-32-characters-long'
FRONT='synthetic-front-token-32-characters-long'
TOKENS={WRITE:'clinician',READ:dict(id='rag',role='reader',subject_ids=['sim-crew'],mission_ids=['sim-mission']),
    FRONT:dict(id='front',role='operator',subject_ids=['sim-crew'],mission_ids=['sim-mission'])}

class InProcessClient:
    def __init__(self,client,token): self.client=client; self.token=token
    def call(self,method,path,body=None,expected=None):
        response=self.client.request(method,path,json=body,headers={'Authorization':'Bearer '+self.token})
        assert response.status_code==expected if expected else 200<=response.status_code<300, response.text
        return response.json()

def test_dataset_reproducibility_and_phases():
    first=generate(42); second=generate(42); different=generate(43)
    assert digest(first.model_dump(mode='json'))==digest(second.model_dump(mode='json'))
    assert first.measurements!=different.measurements
    assert {m.phase for m in first.measurements}=={'PRE_MISSION','IN_MISSION','POST_MISSION'}
    assert len(first.measurements)==38 and all(m.synthetic for m in first.measurements)

@pytest.mark.parametrize('corruption',['nonsynthetic','duplicate','reference','group','version'])
def test_adapter_rejects_bad_envelope_before_writes(corruption):
    raw=generate().model_dump(mode='json')
    if corruption=='nonsynthetic': raw['measurements'][0]['synthetic']=False
    if corruption=='duplicate': raw['measurements'].append(raw['measurements'][0])
    if corruption=='reference': raw['measurements'][0]['device_id']='absent'
    if corruption=='group': raw['groups']['bad']=['absent']
    if corruption=='version': raw['schema_version']='unknown.v99'
    with pytest.raises(ValidationError): SyntheticAdapter(raw)

def test_adapter_file_roundtrip(tmp_path):
    path=tmp_path/'synthetic.json'; data=generate(123); path.write_text(data.model_dump_json(),encoding='utf-8')
    assert list(SyntheticAdapter.from_file(path).measurements())==data.measurements

@pytest.mark.parametrize('url',['https://example.com','http://localhost:8765','http://127.0.0.1@evil.invalid','http://127.0.0.1/path'])
def test_adapter_prevents_token_exfiltration(url):
    with pytest.raises(ValueError): LocalClient(url,READ)

def test_end_to_end_all_layers_in_process(tmp_path):
    database=tmp_path/'e2e.sqlite'
    with TestClient(create_app(ROOT,database,TOKENS)) as client:
        result=exercise(InProcessClient(client,WRITE),InProcessClient(client,READ),generate(),InProcessClient(client,FRONT))
        assert len(result['inconclusive_results'])==7
        assert result['audit_valid'] and result['replay_verified']
        assert result['clinical_execution']=='BLOCKED' and not result['clinical_validation']
        reader=InProcessClient(client,READ)
        reader.call('POST','/rules',{'role':'clinician','rule':'replace'},expected=403)
        reader.call('GET','/profiles/sim-crew',expected=403)
        reader.call('POST','/clinical-notes',{'kind':'DIAGNOSIS'},expected=403)
        reader.call('POST','/evidence/revisions',{'status':'VALIDATED'},expected=403)
        writer=InProcessClient(client,WRITE)
        writer.call('POST','/baselines/withdrawals',{'baseline_id':'baseline-vo2','effective_at':'2025-01-02T00:00:00Z','reason':'SYNTHETIC withdrawal'})
        availability=InProcessClient(client,FRONT).call('GET','/baselines/baseline-vo2/status?as_of=2025-04-01T00%3A00%3A00Z')
        assert availability['availability']=='BASELINE_WITHDRAWN'

        scoped=InProcessClient(client,FRONT)
        scoped.call('GET','/profiles/other',expected=403)
        scoped.call('POST','/evaluations',{'subject_id':'sim-crew','mission_id':'sim-mission','bindings':[]},expected=403)
    store=Store(database)
    try: assert store.verify() and store.get('finding',result['findings']['inconclusive'])['result']=='INCONCLUSIVE'
    finally: store.close()

def test_offline_guard_rejects_external_connections(monkeypatch):
    for name in ('connect','connect_ex','sendto'): monkeypatch.setattr(socket.socket,name,getattr(socket.socket,name))
    monkeypatch.setattr(socket,'getaddrinfo',socket.getaddrinfo)
    deny_external_network()
    with socket.socket() as sock:
        with pytest.raises(OSError,match='EXTERNAL_NETWORK_DISABLED'): sock.connect(('203.0.113.1',443))
    with pytest.raises(OSError,match='EXTERNAL_NETWORK_DISABLED'): socket.getaddrinfo('example.com',443)

def test_real_http_end_to_end_and_private_exports(tmp_path):
    result=run(ROOT,tmp_path/'real-http',seed=42)
    assert result['persisted_after_database_reopen'] and result['reader_results']>=10
    assert result['offline_test'].startswith('PASSED')
    mapping=json.loads((tmp_path/'real-http/server-tokens.json').read_text())
    assert {v['role'] for v in mapping.values()}=={'reader','operator'}
    assert all(k.startswith('sha256:') for k in mapping)
    transcript=(tmp_path/'real-http/api-examples.json').read_text(encoding='utf-8')
    for name in ('reader-token.txt','frontend-token.txt'):
        assert (tmp_path/'real-http'/name).read_text() not in transcript
    assert result['performance']['requests']>50

def test_same_seed_reproduces_decisions_across_fresh_databases(tmp_path):
    outputs=[]
    for index in range(2):
        with TestClient(create_app(ROOT,tmp_path/('repeat'+str(index)+'.sqlite'),TOKENS)) as client:
            outputs.append(exercise(InProcessClient(client,WRITE),InProcessClient(client,READ),generate(42),InProcessClient(client,FRONT)))
    assert outputs[0]['dataset_hash']==outputs[1]['dataset_hash']
    assert outputs[0]['findings']==outputs[1]['findings']
    assert outputs[0]['inconclusive_results']==outputs[1]['inconclusive_results']
