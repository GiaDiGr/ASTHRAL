from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,subprocess,sys
R=Path(__file__).resolve().parents[2];D=R/'docs/asthral'
def load(name):return json.loads((D/name).read_text(encoding='utf8'))
def suite(name):
 x=ET.parse(D/name).getroot()[0];return {k:x.attrib[k] for k in ('tests','failures','errors','skipped','time','timestamp')}
full=suite('full-tests.xml');features=suite('final-feature-tests.xml');public=suite('public-snapshot-final-tests.xml');portable=suite('portable-owner-tests.xml')
assert full['tests']=='759' and full['failures']==full['errors']=='0';assert public['failures']==public['errors']=='0'
old=json.loads((R/'docs/v101-ux/CODE_FREEZE_UX.json').read_text(encoding='utf8'))
clinical=[x for x in old['files'] if '/clinical_knowledge/' in x['path'] or x['path'] in ['engine/vigile/clinical_engine.py','engine/vigile/clinical_logic.py','engine/vigile/monitoring.py','engine/vigile/management.py']]
assert all(hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in clinical)
mission=load('mission-release-verification.json');http=load('http-assistant-smoke.json');voice=load('voice-smoke.json');performance=load('performance.json');comparison=load('retrieval-comparison.json')
actual=json.loads((R/'engine/data/asthral-release/mission-report.json').read_text(encoding='utf8'));original=json.loads((R/'engine/data/mission-v100-r2/mission-report.json').read_text(encoding='utf8'));assert actual['semantic_hash']==original['semantic_hash']
summary={'product':'ASTHRAL','acronym':'Astronaut Support Tool for Health Risk Assessment and Logistics','subtitle':'Offline-First Astronaut Health Monitoring and Medical Decision Support','version':'1.1.0','date':'2026-11-04','account':'GiaDiGr','repository':'https://github.com/GiaDiGr/ASTHRAL','visibility':'PRIVATE','branches':['main','feature/asthral-hybrid'],'full_owner_regression':full,'final_feature_regression':features,'test_only_portability_recheck':portable,'public_snapshot_regression':public,'public_skips':'Three optional historical/model-asset-dependent checks; not reported as passed.','new_hybrid_tests':67,'clinical_knowledge_and_four_core_modules_unchanged':True,'clinical_knowledge_hash':actual['knowledge_hash'],'implementation_hash':actual['implementation_hash'],'mission_semantics_equal_to_R2':actual['semantic_hash'],'new_mission_replays':{'clinical':50,'monitoring':26,'all_match':True},'historical_replays':{'R2':load('replay-R2.json'),'v1.0.1-UX':load('replay-v1.0.1-UX.json')},'online_provider':'PubMed ESearch/ESummary only','live_provider_verified':load('pubmed-live.json')['first']['delivery']=='LIVE','live_provider_documents':len(load('pubmed-live.json')['first']['documents']),'remote_content_scope':'TITLE_METADATA_ONLY_NOT_FULL_TEXT','local_ollama':{'model':http['model'],'actual_requests':http['cases'][0]['model_requests'],'accepted_English_sentences':http['cases'][0]['generated_sentences'],'configuration_changed':False,'existing_runtime_started':True},'voice':{'synthetic_SAPI_to_Vosk_verified':voice['automated_synthetic_SAPI_to_Vosk_test'],'observed_name_transcription':voice['raw_transcript'],'narrow_alias_result':voice['name_alias_result'],'human_microphone_acceptance':False,'human_listening_acceptance':False},'new_retrieval_comparison':{'cases':5,'local_lexical_topic_hit_rate':comparison['local_hit_rate'],'hybrid_fixture_lexical_topic_hit_rate':comparison['hybrid_hit_rate'],'scope':comparison['scope'],'independent_clinical_relevance_review':False,'old_reserved_bank_reused_as_new_independent_evaluation':False},'performance':{k:performance[k] for k in ['local_search_median_ms','cached_remote_median_ms','cpu_seconds','python_peak_tracemalloc_bytes','external_requests_during_profile','model_requests','energy_measured']},'clinical_execution':'BLOCKED','clinical_operational_flight_validation':False,'visual_acceptance':'PENDING_COMPUTER_USE_STOPPED_CANNOT_VERIFY_BROWSER_URL','physical_Internet_disconnect_test':'PENDING','project_license_added':False,'storage_encryption':'NONE','same_user_process_isolation':False}
(D/'verification-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
(D/'RELEASE.md').write_text('''# ASTHRAL 1.1.0 — implementation and verification

**Astronaut Support Tool for Health Risk Assessment and Logistics**

**Offline-First Astronaut Health Monitoring and Medical Decision Support**

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
''',encoding='utf8')
print(json.dumps({'owner_tests':full['tests'],'public_passed':int(public['tests'])-int(public['skipped']),'public_skipped':public['skipped'],'clinical_hash_unchanged':True,'source_semantic_hash':actual['semantic_hash']}))