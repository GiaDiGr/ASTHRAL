from pathlib import Path
import json
R=Path(__file__).resolve().parents[2];D=R/'docs/asthral'
(R/'README.md').write_text('''# ASTHRAL

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
Set-Location ASTHRAL\\engine
py -3 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -e ".[test,integration]"
.\\.venv\\Scripts\\python.exe tools\\setup_asthral.py
```

The dependency declarations are in `engine/pyproject.toml`; `requirements-v100.lock.txt` retains the previous environment pin set for reference. The public corpus contains the project's computable rules, catalogues, and bibliographic metadata, with `ASTHRAL_CORPUS_SHA256.json`. Full third-party papers, original private research bundles, databases, credentials, runtime logs, model weights, and binary voice/runtime assets are excluded. When the original 105-file manifest exists locally, its original integrity check is retained; a clean clone verifies the reduced redistributable corpus instead.

### Optional Ollama and speech assets

Ollama is a separately installed local runtime. Do not replace the existing owner's configuration, restore quarantined binaries, disable antivirus protection, or run the legacy llama downloader to start ASTHRAL. Keep the existing model; no fine-tuning is performed.

For a new teammate workstation, obtain the separately licensed Qwen3-4B-Instruct-2507 GGUF only from the reviewed source/version and verify the pinned SHA-256 in `docs/asthral/MODELS.md`. With an approved Ollama installation, an example import file is provided:

```powershell
# Run only on a new approved setup, from the folder containing the separately acquired GGUF.
ollama create vigile-qwen3-4b:latest -f path\\to\\ASTHRAL\\engine\\Modelfile.example
```

Configure that workstation's local Ollama endpoint to match the example config. These are teammate setup instructions, not commands run to change the owner's installed model. ASTHRAL remains usable through deterministic and extractive fallback when Ollama is absent.

For voice, obtain the English `vosk-model-small-en-us-0.15` separately using the official URL and hashes in `engine/vigile/voice_assets/models.json`, and install `vosk==0.3.45` if voice is needed. Place the extracted model under `engine/local_ai/voice/`. Windows SAPI must provide an English voice; the existing integration selects Microsoft David Desktop. Spanish legacy assets are retained locally but not exposed as astronaut options. No runtime model download, cloud speech, always-on microphone, or wake-word service exists. Push-to-talk requires transcript review and explicit send; playback is also explicit. Leading assistant-name aliases `astral` and the observed synthetic recognition `as thrill` are narrowly scoped. Original transcripts remain available for review; medical terms, values, units, and negations are not corrected.

## Reproduce the synthetic mission

Use a NEW output directory. No patient data or existing mission records are modified.

```powershell
Set-Location engine
$py = '.\\.venv\\Scripts\\python.exe'
& $py tools\\setup_asthral.py
& $py tools\\demo_asthral.py prepare --output data\\asthral-demo
& $py tools\\demo_asthral.py verify --output data\\asthral-demo --report data\\asthral-demo\\verification.json
& $py tools\\demo_asthral.py serve --output data\\asthral-demo
```

Portal: **http://127.0.0.1:8922/**. Backend: **http://127.0.0.1:8921/health**. The supervisor refuses occupied ports and stops only its own children. Obtain the portal access code in a private console; never paste it into chats, issues, screenshots, or the repository:

```powershell
.\\.venv\\Scripts\\python.exe -c "from vigile.local_protection import read_secret; print(read_secret('data/asthral-demo/portal-access.txt'))"
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
.\\.venv\\Scripts\\python.exe tools\\demo_asthral.py prepare --output data\\asthral-online-demo --enable-online
```

This writes `online_retrieval.enabled=true` to a protected local configuration. There is no reader/LLM enablement or privilege-escalation endpoint. Connectivity and FULL alone do not enable access. The UI topic selector requests one approved public topic; it is not an authorization toggle. Requests contain only predefined public search terms or provider-returned public PMIDs, fixed headers, and no private question, context, identifiers, records, audio, token, or embeddings. HTTP failures, DNS failure, timeouts, rejection, and resource limits preserve local behavior. Mode changes invalidate in-flight remote results. Cached references remain separate and visibly cached/unreviewed.

Allowlist: outbound TLS to `eutils.ncbi.nlm.nih.gov:443`, fixed ESearch/ESummary paths only. Canonical displayed references use `pubmed.ncbi.nlm.nih.gov/<PMID>/`. Redirects are rejected, TLS verification is enabled, resolved addresses are checked and pinned, and private/special destinations are rejected. Default budget: 4 seconds per retrieval, two public topics per minute, at most three documents, 128 KiB per response, at most one retry. Provider requests are spaced by at least 0.4 seconds. Cache: at most five fixed topic files, 16 KiB each, 24-hour fresh TTL and at most seven-day stale fallback. See [hybrid contracts](docs/asthral/HYBRID_RAG.md).

## Tests and evidence

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q
.\\.venv\\Scripts\\python.exe -m pytest tests\\test_asthral_hybrid.py -q
```

New synthetic tests exercise modes, privacy sentinels, SSRF, redirect rejection, response limits, metadata validation, prompt injection, cache integrity, mode changes, name aliases, reader scope, and invariance of all seven clinical pathways. The new fixed retrieval comparison is separate from development fixtures and does not reuse the previously consumed reserved bank. It is a small lexical/software fixture evaluation, not independent clinical relevance validation or proof of real-world retrieval improvement. Live PubMed smoke results are reported separately. No electrical-power savings are claimed.

The full owner regression also checks legacy supplied artifacts; an archival corpus-specific benchmark is explicitly omitted on clean clones that do not contain that nonredistributed research pack. Current English retrieval, clinical contracts, and hybrid safety have separate tests. Source pinning, semantic checks, and tests do not establish clinical, operational, or flight validation. Physical microphone/listening and complete visual acceptance must be reported separately from automated synthetic and HTTP/DOM tests. Current evidence and acceptance states are in [the release report](docs/asthral/RELEASE.md).

## Team collaboration, security, and attribution

The repository is intended to be **private** under the owner-selected GitHub account. Use `main` for reviewed stable code and `feature/*` branches and pull requests for work. Never overwrite a teammate's branch or force-push. No invitations are sent without explicit usernames and authorization. See [CONTRIBUTING.md](CONTRIBUTING.md).

SQLite/WAL/backups are **not encrypted**. DPAPI/ACL protects local credentials from other identities but does not isolate same-user processes. A storage-controlling attacker can rewrite data/hash chains; software hashes are not clinical signatures or external tamper-proof anchors. Isolation, operational authority policy, clinical review, and data-at-rest encryption remain pending. Use synthetic data only. See [SECURITY.md](SECURITY.md).

Scientific provenance is retained in the computable source registry and clinical manifest. Online API documentation: [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/) and [NLM usage guidance](https://www.nlm.nih.gov/dataguide/eutilities/utilities.html). Public scientific metadata is not a license to redistribute entire papers. Model/runtime licenses and exclusions are described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). **No project license has been selected or added.** Private team access does not itself grant third-party redistribution rights.
''',encoding='utf8')
(R/'CONTRIBUTING.md').write_text('''# Contributing to ASTHRAL

Work on a feature branch, keep changes scoped, and open a pull request against main:

```powershell
git switch main
git pull --ff-only
git switch -c feature/your-change
# Edit, run relevant tests and the full regression suite.
git add -- path/to/reviewed/files
git diff --cached
git commit -m "Describe the behavior change"
git push -u origin feature/your-change
```

Do not force-push, rewrite someone else's commits, or include databases, WAL/SHM, backups, logs, secrets, DPAPI envelopes, runtime configurations, model weights, or nonredistributable source papers. Review staged files AND history; gitignore does not remove a committed secret. Do not paste access codes or tokens into issues, PR bodies, Actions, screenshots, fixtures, or prompts. Synthetic fixture credentials must be explicit and must never be usable against a real service.

A PR must explain the trigger and resulting behavior, actual tests/results, privacy effects, compatibility/migration, and limitations. Changes to clinical criteria, units, time windows, confirmation, doses, or safety restrictions require documented source justification and independent clinical review. A software role never grants mission treatment authority. Never promote remote references into rules or verified evidence automatically.

Local RAG remains the base. Online retrieval takes an approved public topic ID only, is opt-in under trusted configuration, and uses the actual operating mode. Keep unreviewed remote references out of the LLM and deterministic engine. Add transport-level privacy/mode/SSRF tests for every provider change. Retain original-language provenance and explicitly mark presentation translations; do not translate identifiers, numbers, units, or negations.

Run the new English/local/hybrid acceptance suite separately from historical retrieval benchmarks. Never describe a reused benchmark as a new independent test or software tests as clinical validation. Record visual and physical voice checks only when actually performed. No new project license, collaborator permissions, production deployment, or publication of private records without owner authorization.
''',encoding='utf8')
(R/'SECURITY.md').write_text('''# ASTHRAL security boundaries

Research prototype, synthetic data only. Reader credentials are scoped by astronaut and mission; the portal holds no clinical write credential. Trusted local configuration controls optional public retrieval. There is no online-enable/medical-authorization endpoint for a reader or model. Remote metadata is untrusted, never executed, and never supplied to the LLM or clinical rule engine.

Never commit .env files, credentials, DPAPI envelopes, databases, backups, runtime logs/configuration, models, or private mission data. If a credential is exposed, stop publication and follow the owner's revocation/remediation process; removing a file from the working tree does not remove history. Report a suspected issue privately to the repository owner; do not publish private clinical records in an issue.

TLS verification remains enabled. The public provider uses approved fixed paths, no proxies/cookies/private headers, rejected redirects, validated public addresses pinned for connection, bounded JSON, and fixed public topics. No arbitrary URL or private question is accepted by the retrieval component. These controls do not protect against a fully compromised OS or same-user process.

SQLite, WAL and backups lack encryption. Audit/hash checks detect internal inconsistency within the design but are not an external trust anchor against storage/codespace control. Process isolation, operational identity governance, verified clinical authority, encryption and independent review remain pending. A private GitHub repository does not make unsafe content safe to upload. No treatment execution is enabled.
''',encoding='utf8')
(R/'THIRD_PARTY_NOTICES.md').write_text('''# Third-party attribution and excluded assets

No project license has been added. The owner must select one explicitly. Dependencies retain their own licenses; installing or using them does not license ASTHRAL or clinical use.

The repository includes project source, computable catalogues/rules, bibliographic metadata, synthetic generators/tests, and project-authored English implementation notes. Scientific statements, source IDs, versions and hashes retain their provenance. Existing reports and third-party full articles/PDF/XML research copies are not redistributed merely because they were available on the owner workstation. The reduced public corpus manifest contains only required project metadata and computable records. Historical large code archives and generated databases are excluded.

Qwen3 model weights, Ollama/llama binaries, Vosk binary model assets, Windows SAPI voices, private configuration and datasets must be obtained separately under applicable terms. Existing voice hash manifests identify external assets, not a vendor signature. Qwen provenance and pinned model hash are in docs/asthral/MODELS.md. Vosk English model provenance is in engine/vigile/voice_assets/models.json. Microsoft speech voices are Windows components, not repository assets.

PubMed E-utilities supplies public bibliographic metadata; the adapter extracts title metadata, not article abstracts or full text. Retrieved references are unreviewed and do not grant redistribution rights or clinical approval. NASA and professional sources cited in the registry retain their original notices and access conditions. No endorsement by NASA, NIH, NCBI, Microsoft, Qwen, or any cited organization is claimed.
''',encoding='utf8')
(D/'MODELS.md').write_text('''# Separately acquired local assets

The owner's existing integration remains `http://127.0.0.1:8891`, provider `ollama`, model `vigile-qwen3-4b:latest`. This work does not change the installed model, fine-tune it, restart/reconfigure Ollama, restore quarantined llama-server.exe, or alter Norton.

The existing pinned weight is Qwen3-4B-Instruct-2507 Q4_K_M GGUF, 2,497,280,448 bytes, SHA-256 `8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc`. Recorded source: `https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF/resolve/4edb920b6f14e3b9284d4502a6485103d72cde05/Qwen3-4B-Instruct-2507-Q4_K_M.gguf`. Obtain and review its terms separately; weights are not committed. Verify hash before import. No download is needed on the owner workstation.

For a new approved workstation, place the separate GGUF beside a copy of engine/Modelfile.example, start an approved loopback-only Ollama instance, and create the existing tag using that file. The example imports the model without training. Change only that workstation's local endpoint configuration if needed; do not assume a remote or cloud model is acceptable.

English speech uses `vosk-model-small-en-us-0.15` and Windows SAPI Microsoft David Desktop. The pinned URLs/archive sizes/hashes and model-file hashes remain in engine/vigile/voice_assets/models.json. Download/install separately and verify the manifest; do not include binary assets in Git. The astronaut portal exposes English only while legacy assets remain locally recoverable. Synthesized-speech recognition is a software smoke test, not microphone accuracy or human listening acceptance. Review every transcript before sending; aliases are limited to the assistant's leading name.
''',encoding='utf8')
(R/'engine/Modelfile.example').write_text('FROM ./Qwen3-4B-Instruct-2507-Q4_K_M.gguf\n',encoding='utf8')
(R/'engine/config.example.json').write_text(json.dumps({'backend_url':'http://127.0.0.1:8921','reader_token_file':'data/your-demo/reader-token.txt','access_code_file':'data/your-demo/portal-access.txt','mode':'FULL','model_url':'http://127.0.0.1:8891','model':'vigile-qwen3-4b:latest','inference_provider':'ollama','structured_explanations':True,'voice_enabled':True,'library_manifest':'local_ai/library-asthral.json','online_retrieval':{'enabled':False,'providers':['pubmed'],'timeout_seconds':4,'max_results':3,'max_response_bytes':131072,'queries_per_minute':2,'retries':1},'public_science_cache':'data/public-science-cache'},indent=2),encoding='utf8')
print('English main README, contribution/security/attribution docs and safe examples written')