# ASTHRAL

## ASTHRAL 1.2 personal integration candidate

See the [English personal-account, voice and vector demo](docs/asthral/PERSONAL_V120.md) for offline provisioning, setup, reproducibility and deployment limits. The earlier shared-code instructions below describe the legacy synthetic demo.

**Astronaut Support Tool for Health Risk Assessment and Logistics**

**Offline-First Astronaut Health Monitoring and Medical Decision Support**

ASTHRAL is a research prototype for NASA Space Apps Challenge 2026. It combines deterministic biomedical assessment, longitudinal astronaut monitoring, traceable local evidence, a local assistant, and optional public scientific reference retrieval. It is designed to continue functioning without Internet access. It has not been clinically, operationally, or flight validated.

## Architecture and authority

```text
Sensors / synthetic generators → validation → personal baselines and trends
                              → deterministic clinical engine → findings / episodes / follow-up
                              → immutable snapshots, audit, deterministic replay
                                          ↓ scoped read-only API
                  English astronaut dashboard + local RAG + local Qwen3 through Ollama
                                          ↓ optional public-topic ID only
                      PubMed bibliography adapter → REMOTE_UNREVIEWED reference panel
```

Seven existing clinical pathways remain implemented: diabetes, DKA, hypoglycemia, orthostatic hypotension, POTS, acute kidney injury, and anaphylaxis. The differential engine, four-state AND/OR logic, criteria thresholds, units, potassium restrictions, mission resources, and medical authorization gates are retained. Criteria met is not a signed diagnosis. A missing alternative does not become required when another valid OR branch is satisfied. Missing protocol safety data remain independent. No treatment execution, dose calculation for administration, dispensing, stock consumption, or verified mission medical authority is enabled.

The internal Python package and historical identifiers remain `vigile` for compatibility. Original hashes, clinical records, and archived names are preserved. The current product and astronaut interface are ASTHRAL, in American English. Original-language evidence is never silently rewritten: curated presentation translations are marked, and text without an approved English rendering is withheld with an explicit limitation. Numerical facts, clinical codes, units, and source hashes are not translated.

## Requirements and Windows setup

- Python 3.11 or later; the owner environment was tested with Python 3.13.
- Existing FastAPI, Pydantic, SQLite, uvicorn, pytest, and httpx dependencies; no new runtime dependency for online retrieval.
- Windows DPAPI and ACL support for protected demonstration credentials.
- Node.js for simulated DOM lifecycle tests; no Node frontend build is required.
- Optional local Ollama with `vigile-qwen3-4b:latest` at `http://127.0.0.1:8891`.
- Optional Vosk English model and an installed English Windows SAPI voice.

```powershell
git clone https://github.com/GiaDiGr/ASTHRAL.git
Set-Location ASTHRAL\engine
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,integration]"
.\.venv\Scripts\python.exe tools\setup_asthral.py
```

The dependency declarations are in `engine/pyproject.toml`; `requirements-v100.lock.txt` retains the previous environment pin set for reference. The public corpus contains the project's computable rules, catalogues, and bibliographic metadata, with `ASTHRAL_CORPUS_SHA256.json`. Full third-party papers, original private research bundles, databases, credentials, runtime logs, model weights, and binary voice/runtime assets are excluded. When the original 105-file manifest exists locally, its original integrity check is retained; a clean clone verifies the reduced redistributable corpus instead.

### Optional Ollama and speech assets

Ollama is a separately installed local runtime. Do not replace the existing owner's configuration, restore quarantined binaries, disable antivirus protection, or run the legacy llama downloader to start ASTHRAL. Keep the existing model; no fine-tuning is performed.

For a new teammate workstation, obtain the separately licensed Qwen3-4B-Instruct-2507 GGUF only from the reviewed source/version and verify the pinned SHA-256 in `docs/asthral/MODELS.md`. With an approved Ollama installation, an example import file is provided:

```powershell
# Run only on a new approved setup. Copy Modelfile.example beside the separately acquired GGUF.
# Run from that folder; the FROM path is relative to the Modelfile.
ollama create vigile-qwen3-4b:latest -f .\Modelfile.example
```

Configure that workstation's local Ollama endpoint to match the example config. These are teammate setup instructions, not commands run to change the owner's installed model. ASTHRAL remains usable through deterministic and extractive fallback when Ollama is absent.

For voice, obtain the English `vosk-model-small-en-us-0.15` separately using the official URL and hashes in `engine/vigile/voice_assets/models.json`, and install `vosk==0.3.45` if voice is needed. Place the extracted model under `engine/local_ai/voice/`. Windows SAPI must provide an English voice; the existing integration selects Microsoft David Desktop. Spanish legacy assets are retained locally but not exposed as astronaut options. No runtime model download, cloud speech, always-on microphone, or wake-word service exists. Push-to-talk requires transcript review and explicit send; playback is also explicit. Leading assistant-name aliases `astral` and the observed synthetic recognition `as thrill` are narrowly scoped. Original transcripts remain available for review; medical terms, values, units, and negations are not corrected.

## Reproduce the synthetic mission

Use a NEW output directory. No patient data or existing mission records are modified.

```powershell
Set-Location engine
$py = '.\.venv\Scripts\python.exe'
& $py tools\setup_asthral.py
& $py tools\demo_asthral.py prepare --output data\asthral-demo
& $py tools\demo_asthral.py verify --output data\asthral-demo --report data\asthral-demo\verification.json
& $py tools\demo_asthral.py serve --output data\asthral-demo
```

Portal: **http://127.0.0.1:8922/**. Backend: **http://127.0.0.1:8921/health**. The supervisor refuses occupied ports and stops only its own children. Obtain the portal access code in a private console; never paste it into chats, issues, screenshots, or the repository:

```powershell
.\.venv\Scripts\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/asthral-demo/portal-access.txt'))"
```

The seed-42 longitudinal mission retains the original two synthetic astronauts, 26 receipt checkpoints, measurements, dates, and clinical results. Follow the [English demonstration](docs/asthral/DEMO.md). Plans are not proof of completed treatment, efficacy, recovery, or authorization.

## Local and optional online RAG

Local retrieval uses the existing provenance-checked sparse retrieval/citation pipeline. `tools/setup_asthral.py` builds a separate English project-authored implementation library. `LOCAL_PINNED` means fixed local provenance; it does not imply clinical validation. Historical libraries remain recoverable and their original retrieval behavior is retained where the supplied historical research pack exists.

**Only PubMed/NCBI E-utilities is implemented as an online provider.** NASA HRP/NTRS/OSDR and other APIs are not advertised as implemented adapters. PubMed ESearch/ESummary provide bounded title metadata, publication information, PMID/DOI where available, retrieval time, version, and hash. This is not abstract/full-text review. The material is marked `REMOTE_UNREVIEWED` and appears in a separate scientific-information panel; it never enters the clinical rule engine or the LLM evidence guard/prompt.

| Mode | Local behavior | External scientific requests |
|---|---|---|
| FULL | Existing local RAG and local inference/fallback | Only with explicit trusted enablement and an approved selected public topic |
| LOW_POWER | Existing reduced local resource policy | Zero |
| CRITICAL | Existing deterministic/extractive fallback; no LLM inference | Zero |

Online retrieval is OFF by default. To authorize public-topic retrieval for a NEW synthetic demo, the trusted local operator must explicitly add `--enable-online` at preparation:

```powershell
.\.venv\Scripts\python.exe tools\demo_asthral.py prepare --output data\asthral-online-demo --enable-online
```

This writes `online_retrieval.enabled=true` to a protected local configuration. There is no reader/LLM enablement or privilege-escalation endpoint. Connectivity and FULL alone do not enable access. The UI topic selector requests one approved public topic; it is not an authorization toggle. Requests contain only predefined public search terms or provider-returned public PMIDs, fixed headers, and no private question, context, identifiers, records, audio, token, or embeddings. HTTP failures, DNS failure, timeouts, rejection, and resource limits preserve local behavior. Mode changes invalidate in-flight remote results. Cached references remain separate and visibly cached/unreviewed.

Allowlist: outbound TLS to `eutils.ncbi.nlm.nih.gov:443`, fixed ESearch/ESummary paths only. Canonical displayed references use `pubmed.ncbi.nlm.nih.gov/<PMID>/`. Redirects are rejected, TLS verification is enabled, resolved addresses are checked and pinned, and private/special destinations are rejected. Default budget: 4 seconds per retrieval, two public topics per minute, at most three documents, 128 KiB per response, at most one retry. Provider requests are spaced by at least 0.4 seconds. Cache: at most five fixed topic files, 16 KiB each, 24-hour fresh TTL and at most seven-day stale fallback. See [hybrid contracts](docs/asthral/HYBRID_RAG.md).

## Tests and evidence

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest tests\test_asthral_hybrid.py -q
```

New synthetic tests exercise modes, privacy sentinels, SSRF, redirect rejection, response limits, metadata validation, prompt injection, cache integrity, mode changes, name aliases, reader scope, and invariance of all seven clinical pathways. The new fixed retrieval comparison is separate from development fixtures and does not reuse the previously consumed reserved bank. It is a small lexical/software fixture evaluation, not independent clinical relevance validation or proof of real-world retrieval improvement. Live PubMed smoke results are reported separately. No electrical-power savings are claimed.

The full owner regression also checks legacy supplied artifacts; an archival corpus-specific benchmark is explicitly omitted on clean clones that do not contain that nonredistributed research pack. Current English retrieval, clinical contracts, and hybrid safety have separate tests. Source pinning, semantic checks, and tests do not establish clinical, operational, or flight validation. Physical microphone/listening and complete visual acceptance must be reported separately from automated synthetic and HTTP/DOM tests. Current evidence and acceptance states are in [the release report](docs/asthral/RELEASE.md).

## Team collaboration, security, and attribution

The repository is intended to be **private** under the owner-selected GitHub account. Use `main` for reviewed stable code and `feature/*` branches and pull requests for work. Never overwrite a teammate's branch or force-push. No invitations are sent without explicit usernames and authorization. See [CONTRIBUTING.md](CONTRIBUTING.md).

SQLite/WAL/backups are **not encrypted**. DPAPI/ACL protects local credentials from other identities but does not isolate same-user processes. A storage-controlling attacker can rewrite data/hash chains; software hashes are not clinical signatures or external tamper-proof anchors. Isolation, operational authority policy, clinical review, and data-at-rest encryption remain pending. Use synthetic data only. See [SECURITY.md](SECURITY.md).

Scientific provenance is retained in the computable source registry and clinical manifest. Online API documentation: [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/) and [NLM usage guidance](https://www.nlm.nih.gov/dataguide/eutilities/utilities.html). Public scientific metadata is not a license to redistribute entire papers. Model/runtime licenses and exclusions are described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). **No project license has been selected or added.** Private team access does not itself grant third-party redistribution rights.

The isolated public synthetic demo uses Cloudflare Quick Tunnel. See [Cloudflare operation, credentials and mobile acceptance](docs/asthral/CLOUDFLARE_PUBLIC_DEMO.md).
