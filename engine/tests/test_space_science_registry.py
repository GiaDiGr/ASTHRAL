import json
from pathlib import Path

from vigile.knowledge_v08 import ROOT, SOURCES, build, search


def test_curated_source_registry_is_parseable_and_links_are_official():
    registry=json.loads((ROOT/'docs/asthral/science/sources.json').read_text(encoding='utf-8'))
    assert registry['schema_version']=='1.0.0'
    assert len(registry['sources']) >= 10
    ids={row['source_id'] for row in registry['sources']}
    assert len(ids)==len(registry['sources'])
    assert all(row['url'].startswith('https://') for row in registry['sources'])
    assert any(source[0]=='docs/asthral/science/space-health-summary.md' and
               source[1]=='ASTHRAL_CURATED_PRIMARY_SOURCE_SUMMARY' for source in SOURCES)


def test_space_health_summary_is_hash_verified_and_offline_retrievable(tmp_path):
    out=tmp_path/'library.json'
    manifest=build(ROOT,out)
    assert manifest['missing_documents']==[]
    assert any(row['document']=='docs/asthral/science/space-health-summary.md' for row in manifest['documents'])
    loaded=json.loads(out.read_text(encoding='utf-8'))
    rows,issues=search(loaded,'Crew Active Dosimeter absorbed dose rate instrument Gy Sv',5,ROOT)
    assert rows
    assert any(row['reference']['document']=='docs/asthral/science/space-health-summary.md' for row in rows)
    assert all(row['reference']['sha256'] for row in rows)


def test_local_science_hash_manifest_checks_cleanly():
    import hashlib
    manifest=json.loads((ROOT/'docs/asthral/science/source-integrity.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        raw=(ROOT/row['path']).read_bytes()
        assert len(raw)==row['bytes']
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
