"""Loopback static preview with explicit JavaScript/WASM MIME types."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.wasm':'application/wasm'}
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        super().end_headers()
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8960);parser.add_argument('--root',type=Path,default=Path('dist'));args=parser.parse_args()
    web_root=Path(__file__).resolve().parent
    root=args.root if args.root.is_absolute() else web_root/args.root
    root=root.resolve()
    if root!=web_root and web_root not in root.parents:parser.error('--root must stay inside web-local')
    if not root.is_dir():parser.error('static root does not exist')
    ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(root))).serve_forever()
