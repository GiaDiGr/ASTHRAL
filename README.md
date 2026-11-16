# ASTHRAL

## ASTHRAL 1.2 personal integration candidate

See the [English personal-account, voice and vector demo](docs/asthral/PERSONAL_V120.md) for offline provisioning, setup, reproducibility and deployment limits. The earlier shared-code instructions below describe the legacy synthetic demo.

**Astronaut Support Tool for Health Risk Assessment and Logistics**

**Offline-First Astronaut Health Monitoring and Medical Decision Support**

ASTHRAL is a research prototype for NASA Space Apps Challenge 2026. It combines deterministic biomedical assessment, longitudinal astronaut monitoring, traceable local evidence, a local assistant, and optional public scientific reference retrieval. It is designed to continue functioning without Internet access. It has not been clinically, operationally, or flight validated.

## Final integration candidate — 15 November 2026

The candidate branch `feature/asthral-final-integration-20261115` is based on the fetched `origin/main` history, which retains the earlier EVA integration. It preserves the 3D body map, health, computer-vision, NeuroGuard, assistant, voice, and exercise routes; includes the local Three.js globe and SGP4 propagation from public ISS GP/OMM elements when the provider is available; and retains the synthetic spacecraft as a separate mode. Orbital, model, and voice assets remain on demand. Live public observations, propagated estimates, cached data, unavailable feeds, and synthetic scenarios are labelled separately.

Latest local software suite results: **958 Python passed / 19 skipped / 0 failed** (197.50 s; one Starlette/httpx deprecation warning), **148 browser-local JavaScript tests passed**, and **3 color-wave regression tests passed**. Chromium acceptance verified the blue–violet–blue sequence, all 24 palette assets, synthetic controls, and the heart-rate-driven ECG; the offline acceptance verified 139 cached resources and 24 scene assets, including six representative scenes after an offline reload. A separate mission-control run reached the WebGL2 globe and completed EVA, training-alert acknowledgement, encrypted report storage, and lock/reload recovery, but did not finish the full acceptance script because its former anatomy-navigation selector timed out. The live CelesTrak request returned HTTP 403 during that run. The application has a distinct `ISS ELEMENTS UNAVAILABLE` state and separately labelled synthetic orbit, but the failed run did not capture that state. No live ISS estimate was verified in that run. Independent clinical, operational, and flight validation remains pending. The earlier mission-control test record is [here](docs/asthral/MISSION_CONTROL_INTEGRATION.md); its historical results should not be conflated with this candidate.

## Browser application and mission features

`web-local/` is ASTHRAL's English, static browser application. It combines the 3D anatomical orientation map and systemic vital-sign dashboard with the biomedical engine, historical evidence, mission control, EVA, exercise, computer-vision, NeuroGuard, voice, and assistant modules. EVA uses synthetic training scenarios and the existing profile-history and reporting services; it does not represent suit telemetry. Public NASA archive records, cached observations, propagated orbital estimates, unavailable feeds, and synthetic scenarios are labelled separately.

Mission Control renders an interactive Three.js Earth and time-stamped orbital estimates. The EVA workflow has four monitored cards, scenario alerts, pause/resume, completion, and an encrypted local handover report. These behaviors are software demonstrations, not NASA operational systems or flight validation.

The 22 horizontal route tabs each select a distinct local starfield. Their blue-to-violet ambience follows a smooth 10-tab cycle, returning to blue between violet peaks. Cross-fading, assets, and the app shell are included in the offline resource manifest. After opening the app while connected, use **Settings → Install offline resources**, wait for verification, reload once online, then test with connectivity disabled. Live public data cannot refresh offline.

**Synthetic Test Mode** exposes training-only vital-sign sliders, a heart-rate-driven ECG illustration, and independent cabin/spacesuit oxygen concentration and pressure inputs. Notices are deterministic software examples. The displayed atmospheric warning bounds are illustrative and are not NASA limits or life-support safety determinations. Synthetic controls never submit to the clinical engine or profile history.

## Run, test, build, and deploy the browser app

From the repository root in PowerShell, create a fresh build directory, build the local bundle, and serve it on loopback:

```powershell
$build = Join-Path (Get-Location) 'web-local\build-output-local'
$env:ASTHRAL_BUILD_OUTPUT = $build
& .\engine\.venv\Scripts\python.exe .\web-local\build.py
& .\engine\.venv\Scripts\python.exe .\tools\serve_browser_build.py $build --port 8919
```

Run the full deterministic engine tests from the repository root:

```powershell
& .\engine\.venv\Scripts\python.exe -m pytest -q .\engine\tests
```

Run browser-local tests from `web-local/` against the exact build you just generated:

```powershell
Set-Location .\web-local
$env:ASTHRAL_TEST_DIST = (Resolve-Path .\build-output-local).Path
node --test .\tests\*.test.mjs
```

Cloudflare Pages project `asthral-web` is managed with Wrangler and serves `https://asthral-web.pages.dev/`. For an authorized production release, use the verified build generated from the integrated `main` branch and the configured production branch:

```powershell
npx wrangler pages deploy <build-directory> --project-name asthral-web --branch main
```

Wrangler must be authenticated to the ASTHRAL Cloudflare account. Do not deploy a feature preview to the production domain. Deployment does not imply clinical, operational, or flight qualification.

## Repository map and branches

`main` is the default branch and the integrated project baseline. A successful push to another branch does **not** update `main`; every branch is a separate line of commits. The branch pointers below were checked on 15 November 2026. Confirm them again before starting new work because branches can move.

| Branch | Purpose and current relationship to `main` |
|---|---|
| [`main`](https://github.com/GiaDiGr/ASTHRAL/tree/main) | Integrated ASTHRAL baseline and browser release evidence. The current release report is [`WEB_RELEASE_20261114.md`](docs/asthral/WEB_RELEASE_20261114.md). |
| `feature/integrate-biomedical-contribution` | Reviewable integration branch based on the latest `origin/main`; contains the inspected Computer Vision contribution, compatibility fixes, and license gates. Not merged into `main`. |
| [`feature/asthral-computer-vision`](https://github.com/GiaDiGr/ASTHRAL/tree/feature/asthral-computer-vision) | Contributor source branch for SkinGuard, OcularVision, EchoVision, MotionGuard, evaluation utilities, tests, and benchmarks; preserved separately. |
| `feature/asthral-hybrid` | Earlier hybrid assistant and guarded PubMed retrieval work; its current branch tip is in `main`'s commit history. |
| `feature/secure-voice-vector-rag` | Voice, personal sessions, and retrieval development line. Its branch tip is not in `main`'s commit history. |
| `feature/cloudflare-mobile-demo` | Isolated synthetic mobile-demo deployment line; its branch tip is not in `main`'s commit history. |
| `feature/browser-local-pages` | Browser-local/static-pages development line; its branch tip is not in `main`'s commit history. |
| `feature/browser-complete-release` | Browser release-candidate line; its branch tip is not in `main`'s commit history. |

These relationships describe Git history, not a guarantee that every file is absent or present: work can be copied or squashed between branches. Before reusing or merging a branch, inspect its latest commit, compare its files with the target, and check whether its commits are already included. Do not merge branches merely because their names look related.

To inspect the current checkout and remote branches:

```powershell
git status --short --branch
git branch --all --verbose
git fetch origin --no-tags
```

For an existing checkout, update only the branch you intend to work on. Commit or otherwise preserve local work first; if the branch is clean and only behind its upstream, use a fast-forward-only update. If it is dirty or has diverged, stop and review the differences. Do not use `git reset --hard`, `git clean`, or force-push to synchronize team work. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the collaboration rules.

Safe update sequence for a clean checkout with an upstream configured:

```powershell
git status --short --branch
git branch --show-current
git fetch origin --no-tags
# Run only if the working tree is clean and this branch is strictly behind its upstream.
git merge --ff-only '@{u}'
```

If local and remote commits diverged, do not run the merge command above. Preserve both histories and prepare a reviewed integration or pull request.

## Guidance for AI coding assistants

When an AI assistant works in this repository, use these as project instructions:

1. **Establish the state first.** Confirm the repository root, active branch, upstream, and `git status`. Read this README, [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), and the relevant `docs/asthral/` pages before editing. Treat the checked-out branch as the requested scope; never assume another branch's code is present.
2. **Preserve the existing design.** The Python package and compatible internal identifiers are named `vigile`. The core lives under `engine/vigile/`; the browser application lives under `web-local/`; Python tests are under `engine/tests/`; release and research evidence is documented in `docs/asthral/` and `artifacts/`. Extend the existing API, session, storage, and UI patterns instead of creating a duplicate application or backend.
3. **Respect the clinical authority boundary.** Deterministic, versioned rules and validated inputs produce clinical findings. The local language model and retrieval tools are supporting interfaces; they do not diagnose, change rules, authorize care, or execute treatment. Public PubMed metadata is optional, off by default, marked unreviewed, and kept outside the clinical rule engine. ASTHRAL is not clinically, operationally, or flight validated.
4. **Do not invent evidence.** Keep synthetic software checks, local performance, and clinical evaluation clearly separate. Never present synthetic tests as clinical accuracy or fabricate model weights, dataset labels, metrics, or treatment outcomes. If an optional model or dataset is absent, report that state and leave its inference unavailable.
5. **Protect work across computers.** Do not switch away from a dirty branch, merge another branch without reviewing its file changes, rewrite shared history, or delete files to make an update pass. If histories diverge, preserve both sides and prepare a reviewed integration rather than choosing one branch automatically.
6. **Verify and report precisely.** Run the relevant tests from `engine/` and, for browser changes, use the browser verification procedure in the release report. State the exact branch, commands, pass/skip/fail counts, limitations, and files changed. Do not call a module complete based on a screen or a unit test alone.

### Project flow at a glance

Sensors or synthetic inputs are validated, then used for baselines and longitudinal trends. The deterministic clinical engine evaluates pathways and creates findings, episodes, and follow-up records. Snapshots, audit data, and replay support traceability. A scoped API serves the astronaut dashboard, local retrieval, and optional local Qwen3 inference through Ollama. Optional online retrieval is limited to approved public-topic PubMed metadata; it is not clinical evidence and cannot alter the rules. The browser release and Computer Vision integration have separate evidence and verification scope.

## Current results — 15 November 2026

The figures below distinguish this integration run from upstream branch reports. Software tests, synthetic benchmarks, and clinical performance are separate evidence categories.

| Evidence | Verified result | Scope |
|---|---:|---|
| Full Python suite on `feature/integrate-biomedical-contribution` | **882 passed, 17 skipped, 0 failed** in 261.90 s | Run in isolated Python 3.13 worktree environment; 13 tests skipped for missing OpenCV, 2 for missing PyTorch, and 2 for missing voice dependencies. One Starlette/httpx deprecation warning. |
| Upstream Computer Vision branch report | **894 passed, 2 skipped** (reported by contributor) | Historical contributor report; not reproduced by the integration run. |
| OcularVision and MotionGuard local synthetic benchmarks | Historical measurements only | See the dated machine-run report. The integration run did not install model weights. |
| EchoVision | **Blocked** | Checkpoint rights and written permission are unverified; installer and API fail closed. The source-branch benchmark is historical and does not imply current availability. |
| SkinGuard inference | **Not available** | No compatible, provenance-reviewed model weights or evaluation dataset is installed. |

The contributor benchmark uses deterministic nonmedical patterns and measures workstation runtime, not accuracy. Its historic EchoVision mask and timing are not evidence of current enabled functionality. The report and source JSON are [here](docs/asthral/BENCHMARKS.md) and [here](artifacts/benchmarks/asthral-cv-benchmark-2026-11-14.json). None of these results establishes clinical, operational, or flight validation.

The separate browser release evidence on `main` records **49/49 browser-local tests passed** and a **782/782 Python baseline** for that release snapshot. See the [main-branch browser release report](https://github.com/GiaDiGr/ASTHRAL/blob/main/docs/asthral/WEB_RELEASE_20261114.md). Those figures are separate from the integration suite above.

SkinGuard supports private local image intake and creates reports without predictions when there is no compatible detector. See [SkinGuard scope, setup, and limits](docs/asthral/SKINGUARD.md).
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

The existing portal navigation now includes SkinGuard, OcularVision, EchoVision, and MotionGuard. Read [the Computer Vision setup and model provenance guide](docs/asthral/COMPUTER_VISION.md) before installing optional packages or model assets. Model weights stay in ignored local storage; no image dataset is bundled. SkinGuard has no compatible detector installed, so it validates and documents photos without generating lesion predictions. OcularVision and MotionGuard can use explicitly installed local research assets. EchoVision is disabled pending written permission and checkpoint rights review. None is an ASTHRAL clinical validation or diagnosis.

Install the optional CPU runtime from `engine/`, then explicitly select the model assets needed for the current machine:

```powershell
Set-Location engine
.\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
.\.venv\Scripts\python.exe -m pip install -e ".[vision]"
.\.venv\Scripts\python.exe tools\install_computer_vision_models.py --model oct
.\.venv\Scripts\python.exe tools\install_computer_vision_models.py --model motion
```

EchoNet download and inference are blocked until written permission and checkpoint rights are verified. Computer Vision runs in the existing portal process on port 8922; it does not start another web server or change the SLM.

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

The full owner regression also checks legacy supplied artifacts; an archival corpus-specific benchmark is explicitly omitted on clean clones that do not contain that nonredistributed research pack. Current English retrieval, clinical contracts, and hybrid safety have separate tests. Source pinning, semantic checks, and tests do not establish clinical, operational, or flight validation. Physical microphone/listening and complete visual acceptance must be reported separately from automated synthetic and HTTP/DOM tests. Current browser release, tests, deployment and limitations are in [the 2026-11-14 web release report](docs/asthral/WEB_RELEASE_20261114.md); historical implementation status remains in [the release history](docs/asthral/RELEASE.md).

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

The isolated public synthetic demo uses Cloudflare Quick Tunnel. See [Cloudflare operation, credentials and mobile acceptance](docs/asthral/CLOUDFLARE_PUBLIC_DEMO.md).
