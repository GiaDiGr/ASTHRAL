# ASTHRAL

**Astronaut Support Tool for Health Risk Assessment and Logistics**

**Offline-First Astronaut Health Monitoring and Medical Decision Support**

ASTHRAL is a research prototype for NASA Space Apps Challenge 2026. It combines deterministic biomedical assessment, longitudinal astronaut monitoring, traceable local evidence, a local assistant, and optional public scientific reference retrieval. It is designed to continue functioning without Internet access. It has not been clinically, operationally, or flight validated.

## Current results — 14 November 2026

The figures below identify the branch and kind of evidence. Software coverage, synthetic checks, model latency, and clinical accuracy are different measures.

| Evidence | Verified result | Scope |
|---|---:|---|
| Python regression on `feature/asthral-computer-vision` | **894 passed, 2 skipped, 0 failed** in 264.86 s | Full Python suite on this workstation, including four safe-sync tests. |
| Directed computer-vision, SkinGuard, metric, and benchmark tests | **130 passed**; **95.28% combined line coverage** | Coverage is limited to the three listed vision modules: Computer Vision 92%, SkinGuard 100%, metric calculator 99%. |
| OcularVision CPU benchmark | **0.839 s median / 0.855 s p95 per synthetic image** | 10 runs after 2 warmups; 1.192 images/s on this workstation. |
| EchoVision CPU benchmark | **0.093 s median / 0.100 s p95 per synthetic frame** | 10 runs after 2 warmups; 10.771 frames/s on this workstation. |
| MotionGuard CPU benchmark | **0.021 s median / 0.023 s p95 per synthetic frame** | 10 runs after 2 warmups; 48.074 frames/s on this workstation. |
| SkinGuard inference | **Not available** | Compatible model weights are not installed; no detection metric was generated. |
| Workstation sync helper | **4/4 tests passed** | Fast-forward backup, preservation of dirty edits, deletion block, and divergence block. |

The benchmark uses deterministic, nonmedical patterns. It measures local load and inference time, not accuracy. Full commands, context, model limitations, and comparison with published work are in [the Computer Vision test and benchmark report](docs/asthral/BENCHMARKS.md); the [machine-run JSON](artifacts/benchmarks/asthral-cv-benchmark-2026-11-14.json) contains versions, model hashes, and timing summaries. These numbers do not establish clinical, operational, or flight validation.

The separate browser release work on `main` has its own evidence: its release report records **49/49 browser-local tests passed** and a **782/782 Python baseline** for that release snapshot. See the [main-branch browser release report](https://github.com/GiaDiGr/ASTHRAL/blob/main/docs/asthral/WEB_RELEASE_20261114.md). Those figures are reported separately from the 894-test run above.

The SkinGuard module adds private, local skin-photo intake and a provenance-gated interface for a separately supplied lesion-localization model. No dermatology model or image dataset is bundled; until a reviewed model is configured, SkinGuard validates files and creates reports without generating predictions. See [SkinGuard scope, setup, and limits](docs/asthral/SKINGUARD.md).

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

## Code and test map

- `engine/vigile/computer_vision.py` connects the existing portal API to SkinGuard, OcularVision, EchoVision, and MotionGuard processing, output images, video summaries, and model status.
- `engine/vigile/skinguard.py` validates photo inputs and only accepts a detector when its model, license, weights hash, and held-out evaluation report satisfy the documented contract.
- `engine/vigile/computer_vision_metrics.py` calculates segmentation Dice/IoU, binary classification metrics, and single-class detection AP from supplied predictions and labeled references.
- `engine/tests/test_computer_vision.py`, `test_skinguard.py`, `test_computer_vision_metrics.py`, and `test_benchmark_computer_vision.py` cover input errors, transformations, exports, synthetic metric-calculator examples, model-adapter contracts, and local timing code.
- `engine/tools/sync_asthral.ps1` and `engine/tests/test_sync_asthral.py` implement and test safe branch-scoped updates across workstations.
- `engine/tools/benchmark_computer_vision.py` runs a repeatable CPU timing check on synthetic patterns. It does not read patient data.
- `web-local/tests/` covers the separate browser-local interface and offline behavior; the branch-specific release evidence is linked above.

Passing a synthetic test means the tested software behavior matched that test's expected result. It is not a model accuracy score. Dice, AUROC, sensitivity, specificity, and mAP for an ASTHRAL model require authorized, correctly labeled, held-out evaluation data.

## Requirements and Windows setup

- Python 3.11 or later; the owner environment was tested with Python 3.13.
- FastAPI, Pydantic, Pillow, SQLite, uvicorn, pytest, and httpx. Optional ONNX Runtime is needed only for a separately supplied SkinGuard detector; no new runtime dependency is required for online retrieval.
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

## Computer Vision research modules

The existing portal navigation now includes SkinGuard, OcularVision, EchoVision, and MotionGuard. Read [the Computer Vision setup and model provenance guide](docs/asthral/COMPUTER_VISION.md) before installing optional packages or model assets. Model weights stay in ignored local storage; no image dataset is bundled. SkinGuard has no compatible detector installed, so it validates and documents photos without generating lesion predictions. OcularVision, EchoVision, and MotionGuard use local research checkpoints with the scope and limits described in their reports. None is an ASTHRAL clinical validation or diagnosis.

Install the optional CPU runtime from `engine/`, then explicitly select the model assets needed for the current machine:

```powershell
Set-Location engine
.\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
.\.venv\Scripts\python.exe -m pip install -e ".[vision]"
.\.venv\Scripts\python.exe tools\install_computer_vision_models.py --model oct
.\.venv\Scripts\python.exe tools\install_computer_vision_models.py --model motion
```

EchoNet's LV segmentation checkpoint is a separate ~303 MiB download. Review its research-use and redistribution limits in the linked guide before selecting `--model echo`. Computer Vision runs in the existing portal process on port 8922; it does not start another web server or change the SLM.

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
.\.venv\Scripts\python.exe -m pytest tests\test_computer_vision.py tests\test_skinguard.py tests\test_computer_vision_metrics.py tests\test_benchmark_computer_vision.py -q --cov=vigile.computer_vision --cov=vigile.skinguard --cov=vigile.computer_vision_metrics --cov-fail-under=90
.\.venv\Scripts\python.exe -m pytest tests\test_sync_asthral.py -q
.\.venv\Scripts\python.exe tools\benchmark_computer_vision.py --warmup 2 --repeats 10 --output ..\artifacts\benchmarks\asthral-cv-benchmark-local.json
```

New synthetic tests exercise modes, privacy sentinels, SSRF, redirect rejection, response limits, metadata validation, prompt injection, cache integrity, mode changes, name aliases, reader scope, and invariance of all seven clinical pathways. The new fixed retrieval comparison is separate from development fixtures and does not reuse the previously consumed reserved bank. It is a small lexical/software fixture evaluation, not independent clinical relevance validation or proof of real-world retrieval improvement. Live PubMed smoke results are reported separately. No electrical-power savings are claimed.

The full owner regression also checks legacy supplied artifacts; an archival corpus-specific benchmark is explicitly omitted on clean clones that do not contain that nonredistributed research pack. Current English retrieval, clinical contracts, and hybrid safety have separate tests. Source pinning, semantic checks, and tests do not establish clinical, operational, or flight validation. Physical microphone/listening and complete visual acceptance must be reported separately from automated synthetic and HTTP/DOM tests. Current evidence and acceptance states are in [the release report](docs/asthral/RELEASE.md).

## Team collaboration, security, and attribution

The repository is intended to be **private** under the owner-selected GitHub account. Use `main` for reviewed stable code and `feature/*` branches and pull requests for work. Never overwrite a teammate's branch or force-push. No invitations are sent without explicit usernames and authorization. See [CONTRIBUTING.md](CONTRIBUTING.md).

### Keep work from every computer

GitHub stores committed history per branch. Uncommitted edits remain local and are not included in a pull. The Computer Vision implementation and its test results are on `feature/asthral-computer-vision`; newer browser release evidence is on `main`. At this snapshot, the `main` tree does not contain the CV modules. Keep these streams separate until a reviewed integration retains both sets of work; do not replace one branch with the other or assume `main` contains every feature.

For a fresh Computer Vision checkout, clone its branch explicitly. From an existing clean checkout, the safe updater checks only the current branch's configured upstream:

```powershell
git clone --branch feature/asthral-computer-vision https://github.com/GiaDiGr/ASTHRAL.git
Set-Location ASTHRAL
& .\engine\tools\sync_asthral.ps1
```

The updater fetches without pruning branches, stops when it finds local or untracked work, creates a local backup branch before an update, and advances only when Git can fast-forward the current branch without deleting files. It refuses divergent histories and incoming deletions for review. It does not push or merge `main` into a feature branch. Use `-FetchOnly` to check GitHub without updating the local branch.

When the updater stops, preserve local work in a reviewed commit on its own branch. Before integrating another branch, inspect `git diff --name-status HEAD..origin/main`, create a backup branch, and review every deletion and conflict. Resolve a merge only after confirming that it retains work from both branches; if a clean, uncommitted merge introduces unexpected changes, use `git merge --abort`. Never use `git reset --hard`, `git clean`, or force-push to synchronize team work. Keep separate clones or Git worktrees when branches contain different versions of the same files.

SQLite/WAL/backups are **not encrypted**. DPAPI/ACL protects local credentials from other identities but does not isolate same-user processes. A storage-controlling attacker can rewrite data/hash chains; software hashes are not clinical signatures or external tamper-proof anchors. Isolation, operational authority policy, clinical review, and data-at-rest encryption remain pending. Use synthetic data only. See [SECURITY.md](SECURITY.md).

Scientific provenance is retained in the computable source registry and clinical manifest. Online API documentation: [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/) and [NLM usage guidance](https://www.nlm.nih.gov/dataguide/eutilities/utilities.html). Public scientific metadata is not a license to redistribute entire papers. Model/runtime licenses and exclusions are described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). **No project license has been selected or added.** Private team access does not itself grant third-party redistribution rights.
