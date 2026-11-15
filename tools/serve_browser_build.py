"""Loopback-only static development server; serves public build assets only."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from fnmatch import fnmatch
from urllib.parse import urlsplit
class Handler(SimpleHTTPRequestHandler):
    # Keep responses on persistent HTTP/1.1 connections. Immediate HTTP/1.0
    # close correlated with lost/reset loopback responses in transport probes.
    protocol_version = "HTTP/1.1"
    def log_message(self,*args): pass
    def end_headers(self):
        # Mirror the public build's deployment policy in local acceptance tests.
        headers = {'X-Content-Type-Options': 'nosniff'}
        config = Path(self.directory) / '_headers'
        if config.is_file():
            matched = False
            for line in config.read_text(encoding='utf-8').splitlines():
                if not line.strip() or line.lstrip().startswith('#'): continue
                if not line[0].isspace():
                    matched = fnmatch(urlsplit(self.path).path, line.strip())
                elif matched and ':' in line:
                    key, value = line.strip().split(':', 1)
                    if '\r' not in value and '\n' not in value: headers[key] = value.strip()
        for key, value in headers.items(): self.send_header(key, value)
        super().end_headers()
    def guess_type(self,path):
        # Windows registry MIME associations may map .mjs to text/plain.
        kind={'.js':'text/javascript','.mjs':'text/javascript','.wasm':'application/wasm'}.get(Path(path).suffix.lower(),super().guess_type(path))
        return kind+'; charset=utf-8' if kind.startswith('text/') or kind=='application/javascript' else kind
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--port',type=int,default=8919);args=parser.parse_args()
    root=args.directory.resolve(strict=True)
    if not (root/'assets.json').is_file():parser.error('Only an ASTHRAL public build directory may be served')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(root)))
    print(f'ASTHRAL public assets: http://127.0.0.1:{args.port}/',flush=True)
    server.serve_forever()
