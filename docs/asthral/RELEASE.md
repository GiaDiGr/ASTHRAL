# ASTHRAL 1.1.0 — implementation and verification

**Astronaut Support Tool for Health Risk Assessment and Logistics**

**Offline-First Astronaut Health Monitoring and Medical Decision Support**

> This is the historical v1.1.0 implementation status. Its manual acceptance section predates the browser review dated 2026-11-14. For the current tested preview, results and remaining acceptance limits, read [WEB_RELEASE_20261114.md](WEB_RELEASE_20261114.md).

## Implemented

- ASTHRAL branding, English astronaut UI/templates, current English documentation and English-only STT/TTS options. Internal vigile imports/identifiers/cookies and immutable source language are retained for compatibility. Curated translations are separate from the clinical corpus; unsupported source translations are explicitly withheld.
- Existing local RAG and local Qwen3 integration retained. New English pinned implementation library; historical default corpus ranking preserved. The assistant identifies itself as ASTHRAL.
- Real PubMed ESearch/ESummary adapter with fixed public topics, allowlisted destinations, verified TLS/public-address pinning, no redirects, bounded JSON/metadata, rate/time/retry limits, failure fallback and separate bounded public cache.
- Separate REMOTE_UNREVIEWED reference panel. Remote text is not given to the LLM or clinical engine, does not update local knowledge, and has no privileged capability. Trusted local enablement only; no reader/LLM enablement or medical authority endpoint.
- FULL gating and pending-result invalidation using the existing mode controller. LOW_POWER/CRITICAL have zero external retrieval; CRITICAL retains existing no-inference behavior. UI mode changes discard stale scientific replies.
- Narrow leading-name aliases for astral and the observed synthetic recognizer output as thrill. Push-to-talk, review/send, cancel and playback interruption retained; no medical autocorrection or continuous listening.
- Safe private GitHub preparation under the owner-selected account GiaDiGr, explicit publication manifest, exclusion rules, byte-preserving Git attributes, English README/contribution/security/attribution/model docs and reproducible fresh demo commands. No project license or collaborator invitations were added.

## Automatically verified

- Owner full regression: **759 passed, zero failures/errors/omissions**, one existing Starlette/httpx deprecation warning. Final feature regression: **177 passed**. Subsequent test-only portability adjustments: **70 passed**. Counts overlap and must not be added as distinct tests.
- Exact public staged-source export: **756 passed, 3 explicitly skipped, zero failures/errors**. The omissions depend on historical supplied corpus or optional model assets excluded from the repository. They are not claimed as reproduced acceptance.
- **67 new hybrid tests**, including mode gating, private/secret-shaped inputs, public queries only, DNS/private destinations, TLS, redirect/type/size rejection, rate/errors, malformed metadata, stale/cache integrity, instructions in documents, mode changes and seven-pathway invariance. Thirteen simulated astronaut DOM cases, six management DOM cases and eight voice lifecycle cases remain software simulations, not real-browser/microphone acceptance.
- All ten clinical knowledge files and four core clinical/logic/monitoring/management modules retain their previous byte hashes. No threshold, dose, clinical criterion, inventory/authority rule or therapeutic execution block changed.
- New mission: **50 clinical + 26 monitoring replays match** with valid audit; identical longitudinal/clinical semantic hash to R2. Archived R2 and v1.0.1 UX: **50+26 matching replays each**, using isolated copies and matching archived runtimes. Original frozen databases/archives remain intact.
- Real PubMed smoke: **three public references**, two actual provider requests, subsequent cache hit. Live title metadata is not full-text review or clinical evidence approval.
- Real HTTP assistant: **one local Qwen3 request, two accepted English sentences** for a descriptive baseline question. Separate smoke with Ollama stopped preserved extractive results. Existing Ollama was started using its unchanged configuration; no fine-tuning, model replacement, Norton changes or quarantined-file restoration.
- Real HTTP local/online/cached references, urgency/safety and modes. Physical disconnection of Internet was not performed; timeout/disconnection behavior was instrumented in synthetic transport tests.
- Synthetic SAPI→Vosk: English synthesis and recognition worked, with as thrill recognized for ASTHRAL and the restricted name alias applied. No audio was written to disk and no human microphone/listening acceptance was performed.
- Five newly fixed held-out public-topic software cases: local lexical hit 0.6, hybrid-fixture hit 1.0; five cache hits and no model calls. This small synthetic-provider comparison tests mapping/citation plumbing, not independent clinical relevance or demonstrated improvement in real literature quality. Previous reserved data were not reused as a new independent evaluation.

## Manually verified / pending

No independent clinical, operational, flight, human microphone/listening or full visual acceptance is claimed. Computer Use initialized and enumerated Chrome but stopped because it could not confidently determine the browser URL. No ASTHRAL screen inspection was completed and no alternate browser control was used to bypass that stop. Complete the checklist in DEMO.md with a human reviewer.

Pending: physical offline/voice and visual/accessibility/responsive checks; independent review of translation nuance and the preexisting clinical discrepancies/source locators; structured resource requirements for several documentary countermeasures; verified mission clinical authority; encryption and process isolation. SQLite/WAL/backups remain plaintext. Same-user/storage compromise remains outside the hash/ACL boundary. No electrical-power saving, full-text literature review or clinical validation is claimed.

## Repository and team use

Repository: https://github.com/GiaDiGr/ASTHRAL, account **GiaDiGr**, created **PRIVATE**. main is the stable branch; feature/asthral-hybrid preserves the implementation branch. The final delivery records the verified remote commit SHA; a document cannot embed its own commit hash. No force push or collaborator invitations are used. Review the current Git history and CONTRIBUTING.md before branching.

README.md contains installation, protected demo setup, models, tests and security limits. DEMO.md contains the English five-minute walkthrough. HYBRID_RAG.md defines actual policy and contracts. HISTORICAL_COMPATIBILITY.md explains archived runtimes and translation/provenance boundaries. verification-summary.json records machine-readable nonprivate results; detailed local XML, live traces and private backups remain outside the publication manifest.
