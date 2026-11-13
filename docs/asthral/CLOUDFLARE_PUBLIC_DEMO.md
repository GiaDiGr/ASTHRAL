# Public synthetic demonstration through Cloudflare

This deployment exposes the dedicated ASTHRAL personal portal through a temporary HTTPS Quick Tunnel. Its code remains in the private GiaDiGr/ASTHRAL repository. Only disposable synthetic mission records are used. The original development databases and runtime configuration are kept outside the demo.

## Open and sign in

Run the following commands in PowerShell from the project's engine directory. Use the local private terminal to display the two random demo passphrases. Do not copy their output into logs, issues or screenshots.

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py tools/public_demo.py url
& $py tools/public_demo.py credentials
```

The accounts are `crew-alpha` and `crew-bravo`. Each account is bound to exactly one synthetic astronaut and the mission. They have different randomly generated passwords, Argon2id verifiers and independently scoped backend readers. There is no public registration or account administration endpoint. A new account or password reset is an owner-only local operation using the existing personal_accounts CLI. Voice-derived entries are synthetic reports belonging to the signed-in account.

## Start, stop and diagnose

First-time dependencies and official cloudflared installation:

```powershell
& $py -m pip install -e '.[test,integration,voice,personal,public_demo]'
& ./tools/install_cloudflared.ps1
& $py tools/public_demo.py prepare
```

Preparation refuses an existing directory. It generates a new synthetic mission and credentials, then builds the existing approved English corpus and MiniLM index. Existing models must already be installed according to PERSONAL_V120.md. A separate loopback Ollama process uses the existing model files, with cloud operation disabled, on port 8954. Its logs and process state belong to this demo. The generator uses the existing personal provisioning helper. It does not copy a development database.

Routine operation:

```powershell
& $py tools/public_demo.py start
& $py tools/public_demo.py tunnel
& $py tools/public_demo.py health
& $py tools/public_demo.py url
& $py tools/public_demo.py stop-tunnel
& $py tools/public_demo.py stop
```

Run `start` and `tunnel` to reopen the demo after stopping it. The tunnel command reruns local admission checks and waits for a registered Cloudflare connection before admitting the generated hostname. Its HTTPS URL changes whenever a new tunnel is created. The host PC must stay awake and connected to the Internet. The tunnel has no uptime guarantee. No Cloudflare account, purchased domain, payment, router change, installed Windows service or Windows autostart is used.

The helper records PID and process creation time, and stops only its recorded processes. `stop-tunnel` also closes public hostname admission. `stop` additionally stops the demo portal, backend and demo-owned Ollama process. It leaves the synthetic files available for a later restart. A startup refusal means a recorded service is still active or a required port is occupied. Inspect `health` and the private logs rather than terminating unrelated programs.

Private operational files live under `engine/data/cloudflare-public-demo`. Logs, DPAPI credentials, databases, origin hostname and process metadata are ignored by Git. The download and the isolated Ollama log live under `work/cloudflare`. The personal directory is restricted to the current Windows identity and SYSTEM. A disposable incomplete preparation is preserved rather than deleted automatically.

## Network boundary

The backend binds to 127.0.0.1:8951. The personal portal binds to 127.0.0.1:8952. Cloudflare metrics bind to 127.0.0.1:8953. The demo Ollama API binds to 127.0.0.1:8954. Only the personal portal is connected to the tunnel. The origin file admits one exact generated trycloudflare.com hostname and is closed when absent or invalid. Wildcard hosts are rejected.

The launcher disables Uvicorn proxy-header interpretation. The outer ASGI middleware accepts only a loopback peer and the exact operator-selected Host, removes forwarded headers, and derives HTTPS from the admitted origin. Browser POST requests must carry the same HTTPS Origin. This deliberate loopback proxy boundary assumes the local Windows identity and operator-controlled files are trusted. Cookies are Secure, HttpOnly, SameSite Strict and host-only. Protected responses and assets use no-store. External visitors cannot select a different origin by sending forwarded headers.

The HTTPS link terminates at Cloudflare, which can process the synthetic traffic. Cloudflare does not encrypt local SQLite files. Same-user local processes, storage rollback/deletion, session theft and account guessing remain deployment risks. Login admission and session limits mitigate abuse but do not provide a distributed denial-of-service defense. Use only these disposable synthetic accounts.

No public generic proxy, raw backend, Ollama API, debug docs, database, file browser, credentials endpoint or provisioning endpoint is offered. Frontend API routes are relative to the same origin. Application requests use ordinary HTTP JSON and POSTed PCM WAV. There is no application SSE or WebSocket requirement. Generation responses are bounded and non-streaming, so model startup and generation can cause visible waiting or an explicit fallback.

## Windows TLS and QUIC

The official Windows x64 cloudflared 2026.11.0 download was checked against its release asset SHA-256 and a valid Cloudflare Authenticode signature.

```text
d5c1d82031da6253dcdcff64c944cd0fe063016edeb2e4fd088075fc9bd52d0a
```

On this PC the attempted HTTP/2 edge connection received a certificate issued by “Norton Web/Mail Shield Untrusted Root” and failed certificate verification. QUIC, an official Cloudflare transport, connected successfully with verification active. No Norton settings, trust-store entries or TLS validation flags were changed. No untrusted Norton certificate was imported. The launcher therefore explicitly uses QUIC. If outbound UDP 7844 is unavailable on another network, connection can fail. Inspect the tunnel log and network policy. Do not disable antivirus, firewall or certificate verification to make the demo work.

Existing owner Cloudflare configuration is not loaded or modified. Quick Tunnel gets an explicit isolated empty configuration file. The source repository remains private independently of the public demonstration URL.

## Verification commands

```powershell
& $py -m pytest -q --tb=short
& $py -m pytest -q tests/test_public_ingress.py
node --test tests/voice_ui_unit.cjs
& $py tools/check_public_demo.py --ai
```

The public workflow checker logs in with both synthetic accounts over real public HTTPS, checks ownership and historical frames, denies foreign IDs and private files, checks Secure cookies, CSRF, logout and reconnection, and exercises SAPI-generated audio through authenticated English Vosk. With `--ai`, it also calls the existing local assistant and optional public-topic PubMed retrieval. It reports whether accepted generation occurred or a safe fallback was returned. Synthetic server-side audio is not physical phone microphone acceptance.

The local check `--local` uses an exact preflight hostname and tests the loopback HTTP origin boundary with an explicitly copied Secure cookie. Never run this mode while sharing an active URL, because it changes the admitted hostname. The tunnel command calls this check before connecting a new tunnel.

Historical replay must use isolated database copies and each original runtime. The full regression suite passed 782 tests with one Starlette test-client deprecation warning. R2, v1.0.1 UX and v1.1.0 each reproduced 50 clinical and 26 monitoring results with valid audit integrity. The new mission also passed its 50 clinical and 26 monitoring replays during preparation.

## Actual public workflow result

The external HTTPS checker passed login with both accounts, dashboard and historical-frame reads, cross-user denial, private-file denial, Secure cookies, CSRF, logout and reconnection. A real local Qwen call returned an accepted explanation with one model request. Optional PubMed returned REMOTE_OPTIONAL for the allowed public topic. English SAPI-generated test audio traveled through the public authenticated endpoint to Vosk and produced a review-only heart-rate record of 82. The saved record was visible only to its owner. Physical audio capture was not used.

An initial combined clinical-plus-documentary request timed out during cold model startup. Retrying the normal assistant workflow after startup produced an accepted answer. This remains a latency limitation for cold starts and combined requests. Text and deterministic results remain available, and failed generation must not be represented as completed inference.

## Mobile acceptance

The public login loaded in the in-app Chromium browser over the actual Cloudflare HTTPS URL. At 360 and 390 CSS pixels, document width matched viewport width. Responsive CSS keeps controls readable, contains long evidence and history text, and uses 16px mobile inputs. This is responsive browser verification, not a physical Android or iPhone result.

Android Chrome, iPhone Safari, desktop Chrome and the authenticated mobile dashboard still require device acceptance. The voice recorder uses user-initiated getUserMedia and AudioWorklet capture over HTTPS. Permission, available browser features, interruption behavior and mobile playback must be tested on the target phone. Server-side Vosk transcribes English and server-side Windows SAPI produces WAV for browser playback. Text remains available if a browser lacks supported audio capture. No Windows SAPI component runs on the phone.

Local SQLite, WAL and backups remain unencrypted. DPAPI protects selected credentials and voice payloads only. Independent security, clinical and operational acceptance remain pending. Tests with synthetic records are software evidence.

Official references are [Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), the [signed release assets](https://github.com/cloudflare/cloudflared/releases/tag/2026.11.0), and [Cloudflare troubleshooting](https://developers.cloudflare.com/tunnel/troubleshooting/).
