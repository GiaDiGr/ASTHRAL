"""Loopback static preview with explicit JavaScript/WASM MIME types."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.wasm':'application/wasm'}
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        super().end_headers()
    def do_GET(self):
        from urllib.parse import urlsplit
        if urlsplit(self.path).path != '/api/radlab':
            return super().do_GET()
        from radlab_proxy import fetch_radlab
        import json
        query=urlsplit(self.path).query
        try:
            _, payload=fetch_radlab(query)
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-ASTHRAL-RadLab-Payload','RAW')
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, ConnectionError) as error:
            code=400 if isinstance(error,ValueError) and 'NASA RadLab returned HTTP' not in str(error) else 502
            body=json.dumps({'error':str(error),'provider':'NASA_OSDR_RADLAB'}).encode()
            self.send_response(code)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            self.wfile.write(body)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8960);parser.add_argument('--root',type=Path,default=Path('dist'));args=parser.parse_args()
    web_root=Path(__file__).resolve().parent
    root=args.root if args.root.is_absolute() else web_root/args.root
    root=root.resolve()
    if root!=web_root and web_root not in root.parents:parser.error('--root must stay inside web-local')
    if not root.is_dir():parser.error('static root does not exist')
    ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(root))).serve_forever()
