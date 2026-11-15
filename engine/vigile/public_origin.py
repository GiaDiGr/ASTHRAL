"""Exact operator-selected Quick Tunnel origin. Forwarded headers confer no trust."""
from pathlib import Path
import re
from starlette.responses import JSONResponse

PATTERN = re.compile(r'https://[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com')

class PublicOrigin:
    def __init__(self, app, path):
        self.app = app
        self.path = Path(path)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        headers = scope.get('headers', [])
        hosts = [v.decode('latin1') for k, v in headers if k == b'host']
        origins = [v for k, v in headers if k == b'origin']
        try:
            origin = self.path.read_text(encoding='utf8').strip()
        except OSError:
            origin = ''
        peer = (scope.get('client') or ('', 0))[0]
        if not PATTERN.fullmatch(origin):
            response = JSONResponse({'detail': 'PUBLIC_ORIGIN_NOT_READY'}, 503)
        elif peer not in ('127.0.0.1', '::1') or hosts != [origin[8:]] or len(origins) > 1:
            response = JSONResponse({'detail': 'PUBLIC_HOST_REJECTED'}, 400)
        else:
            scope = dict(scope)
            scope['scheme'] = 'https'
            scope['server'] = (origin[8:], 443)
            # The launcher disables Uvicorn proxy headers. Ignore all client forwarded headers.
            scope['headers'] = [(k,v) for k,v in headers if k not in
                                (b'forwarded', b'x-forwarded-host', b'x-forwarded-proto', b'x-forwarded-for')]
            async def secured(message):
                if message['type'] == 'http.response.start':
                    message['headers'] = list(message.get('headers', [])) + [
                        (b'strict-transport-security', b'max-age=86400'),
                        (b'cache-control', b'no-store')]
                await send(message)
            await self.app(scope, receive, secured)
            return
        response.headers['Cache-Control'] = 'no-store'
        await response(scope, receive, send)
