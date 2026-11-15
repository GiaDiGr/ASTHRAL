import hashlib,http.client,importlib.util,threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

def test_browser_static_server_preserves_http11_connections_and_complete_asset_bytes(tmp_path):
    source=Path(__file__).resolve().parents[2]/'tools/serve_browser_build.py'
    spec=importlib.util.spec_from_file_location('static_server_regression',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    (tmp_path/'_headers').write_text("/*\n  Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'\n  Referrer-Policy: no-referrer\n")
    raw=bytes(range(256))*2048;(tmp_path/'engine.zip').write_bytes(raw);(tmp_path/'runtime.mjs').write_text('export const ready=true;')
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(module.Handler,directory=str(tmp_path)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
    try:
        peer=None
        for _ in range(6):
            client.request('GET','/engine.zip');response=client.getresponse();received=response.read()
            assert response.getheader('Referrer-Policy')=='no-referrer'
            assert response.getheader('Content-Security-Policy')=="default-src 'self'; script-src 'self' 'wasm-unsafe-eval'"
            assert response.version==11 and response.status==200 and response.getheader('Content-Length')==str(len(raw))
            assert hashlib.sha256(received).digest()==hashlib.sha256(raw).digest()
            assert client.sock is not None
            current=client.sock.getsockname()
            if peer is not None:assert current==peer
            peer=current
        client.request('GET','/runtime.mjs');response=client.getresponse();assert response.getheader('Content-Type').startswith('text/javascript');assert response.getheader('X-Content-Type-Options')=='nosniff';assert b'export const ready' in response.read()
    finally:client.close();server.shutdown();server.server_close();thread.join(timeout=5)
