import argparse,json,secrets,hashlib
from pathlib import Path
from .registry import Registry
from .store import Store

def main():
    parser=argparse.ArgumentParser(description='VIGILE offline research engine')
    parser.add_argument('command',choices=['init','serve','audit','demo','simulate','integration-demo','import-synthetic','clinical-demo'])
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--managed-stdin',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--integration-dir',type=Path)
    parser.add_argument('--dataset',type=Path)
    parser.add_argument('--url',default='http://127.0.0.1:8765')
    parser.add_argument('--token-file',type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    if args.command=='clinical-demo':
        from .clinical_demo import run
        print(json.dumps(run(root,args.output),indent=2))
    elif args.command=='simulate':
        from .simulator import generate
        dataset=generate(args.seed)
        if args.output:
            with args.output.open('x',encoding='utf-8') as stream: stream.write(dataset.model_dump_json(indent=2))
            print('Synthetic dataset written:',args.output)
        else: print(dataset.model_dump_json(indent=2))
    elif args.command=='integration-demo':
        from .integration import run
        print(json.dumps(run(root,args.output,args.seed),indent=2))
    elif args.command=='import-synthetic':
        from .adapters import SyntheticAdapter,LocalClient
        if not args.dataset or not args.token_file: parser.error('--dataset and --token-file required')
        adapter=SyntheticAdapter.from_file(args.dataset)
        receipts=adapter.submit(LocalClient(args.url,args.token_file.read_text(encoding='utf-8').strip()))
        print(json.dumps({'measurements_received':len(receipts),'clinical_validation':False}))
    elif args.command=='init':
        data=root/'engine/data';data.mkdir(exist_ok=True)
        from .credentials import provision
        provision(data)
        store=Store(data/'vigile.sqlite3');r=Registry(root);r.import_to(store);store.close()
        print('Initialized offline corpus and local credential hashes in tokens.json and private tokens in client-credentials.json. Protect both files; never give write tokens to the LLM.')
    elif args.command=='serve':
        import os
        if args.integration_dir:
            folder=args.integration_dir.resolve()
            if not (folder/'server-tokens.json').is_file(): parser.error('Integration credential configuration missing')
            os.environ.pop('VIGILE_TOKENS',None)
            os.environ['VIGILE_DB']=str(folder/'vigile.sqlite3')
            os.environ['VIGILE_TOKEN_FILE']=str(folder/'server-tokens.json')
            (folder/'server-process.json').write_text(json.dumps({'pid':os.getpid()}),encoding='utf-8')
        if os.environ.get('VIGILE_TEST_NO_EXTERNAL_NETWORK')=='1':
            from .integration import deny_external_network
            deny_external_network()
        import uvicorn
        from .api import create_app
        if not args.integration_dir and not (root/'engine/data/tokens.json').exists():
            parser.error('Run python -m vigile init first, or use the documented uvicorn factory with VIGILE_TOKENS')
        if args.managed_stdin:
            if not args.integration_dir: parser.error('Managed lifecycle requires isolated integration directory')
            import threading,sys
            server=uvicorn.Server(uvicorn.Config(create_app(),host='127.0.0.1',port=args.port,access_log=False))
            def shutdown_on_eof():
                sys.stdin.buffer.read(1)
                server.should_exit=True
            threading.Thread(target=shutdown_on_eof,daemon=True).start()
            server.run()
        else:
            uvicorn.run(create_app(),host='127.0.0.1',port=args.port,access_log=False)
    elif args.command=='audit':
        registry=Registry(root)
        print(json.dumps({'corpus':registry.fingerprint,'counts':{k:len(v) for k,v in registry.catalogs.items()},'issues':registry.issues},ensure_ascii=True,indent=2))
    else:
        from .demo import run
        print(json.dumps(run(root),indent=2))

if __name__=='__main__': main()
