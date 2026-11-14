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
    root=Path(__file__).resolve().parent/'dist'
    ThreadingHTTPServer(('127.0.0.1',8960),partial(Handler,directory=str(root))).serve_forever()
