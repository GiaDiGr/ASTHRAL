"""Prepare a fresh v0.7 portal demonstration; preserve all previous databases.

Reuse-config keeps the existing local model configuration and reader credentials.
Only the new demo's server-owned reader scope gains its three synthetic subjects.
"""
from pathlib import Path
import argparse,json,shutil,hashlib
from .portal_demo import prepare
from .monitoring_demo import scenarios
from .store import Store
from .service import Engine
from .registry import Registry

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reuse-config',type=Path)
    args=parser.parse_args();root=Path(__file__).resolve().parents[2];folder=args.output.resolve()
    if folder.exists():raise ValueError('OUTPUT_ALREADY_EXISTS_PRESERVE_HISTORY')
    prepare(root,folder)
    if args.reuse_config:
        previous=json.loads(args.reuse_config.read_text(encoding='utf-8'))
        for key,name in [('reader_token_file','reader-token.txt'),('access_code_file','portal-access.txt')]:
            shutil.copyfile(Path(previous[key]),folder/name);previous[key]=str(folder/name)
        shutil.copyfile(args.reuse_config.parent/'server-tokens.json',folder/'server-tokens.json')
        (folder/'portal-config.json').write_text(json.dumps(previous,indent=2),encoding='utf-8')
    mapping=json.loads((folder/'server-tokens.json').read_text(encoding='utf-8'))
    token=(folder/'reader-token.txt').read_text(encoding='utf-8').strip()
    key='sha256:'+hashlib.sha256(token.encode()).hexdigest()
    if key not in mapping:key=token
    principal=mapping[key]
    if principal['role']!='reader':raise ValueError('READER_CREDENTIAL_REQUIRED')
    for field,prefix in [('subject_ids','v07-crew-'),('mission_ids','v07-mission-')]:
        principal[field]=sorted(set(principal[field]+[prefix+s for s in 'ABC']))
    (folder/'server-tokens.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
    store=Store(folder/'vigile.sqlite3')
    try:
        engine=Engine(Registry(root),store);report=scenarios(engine)
        report['implementation_hash']=engine.implementation_hash
    finally:store.close()
    (folder/'monitoring-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'folder':str(folder),'config':str(folder/'portal-config.json'),'cycles':report['cycles'],'replay_matches':sum(r['matches'] for r in report['replays']),'implementation_hash':report['implementation_hash'],'clinical_validation':False},indent=2))

if __name__=='__main__':main()
