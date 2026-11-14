# ASTHRAL 1.2 integration candidate

Use a fresh synthetic directory. An account has an immutable random ID and one unique subject binding, one mission and an independently scoped backend reader token. The portal checks the backend's declared scopes against the account before using that credential. The backend applies its existing record authorization, including frame scope and evaluation relationships. The browser supplies selectors only. The portal derives write ownership from the session. Backend denial and missing resource responses are both returned as 404 in personal mode. Personal mode discards browser-supplied chat history and reserves changes to the process-wide power mode for the operator. No private conversation archive, public registration or new export endpoint is exposed.

## Run the English synthetic demo

From PowerShell in the project directory:

```powershell
Set-Location engine
$py = '.\.venv\Scripts\python.exe'
& $py -m pip install -e '.[test,integration,voice,personal]'
& $py tools/setup_asthral.py
& $py tools/demo_asthral.py prepare --personal --output data/asthral-personal-demo --backend-port 8931
& $py tools/demo_asthral.py serve --output data/asthral-personal-demo --backend-port 8931 --portal-port 8932
```

Enter distinct synthetic passphrases of at least 14 characters when prompted. Open http://127.0.0.1:8932 and sign in as `crew-alpha` or `crew-bravo`. In **Assistant**, select **Record health observation**, opt in to automatic saving and use **Talk / stop**. Try “Record my exercise duration as twenty minutes in the past twenty four hours.” If the recorder produces a draft, review and correct the transcription before saving. Try “My heart rate is eighty two beats per minute” for a review-only example. Use **Refresh self-reported history** to select an entry for correction or removal. The Overview displays a separate timeline of these reports. Restart the serve command, sign in again and check history. Use separate browser profiles to exercise both accounts simultaneously. Ordinary voice questions use the existing assistant mode. The legacy shared-code demo is a separate compatibility path for synthetic data.

## Provision locally

Create an exact-scope reader in the trusted backend credential map with role `reader`, one subject and one mission. Use a distinct high-entropy reader token for each account and store its SHA-256 verifier in the backend map. Provision from the portal's Windows identity with the backend running:

```powershell
& $py -m vigile.personal_accounts --database data/asthral-personal-demo/personal.sqlite3 create astronaut-one --subject SUBJECT --mission MISSION --backend http://127.0.0.1:8931
& $py -m vigile.personal_accounts --database data/asthral-personal-demo/personal.sqlite3 reset astronaut-one
& $py -m vigile.personal_accounts --database data/asthral-personal-demo/personal.sqlite3 disable astronaut-one
```

The CLI prompts for secrets. Administration is a trusted local filesystem operation. It grants no portal session or clinical role. Put the database in a restricted directory. The personal portal accepts `accounts_db` instead of the legacy reader token and access code. Passwords use salted Argon2id, 64 MiB, three iterations and parallelism two. Login admission is capped per process. Sessions hold SHA-256 verifiers of random 256-bit tokens in memory, with explicit rotation, idle and absolute expiry, logout, and generation checks on reset or disable. Cookies are HttpOnly and SameSite Strict. POST requests require the same Origin. The launcher binds to literal loopback and disables access logging. Network deployment requires a separately reviewed HTTPS and process isolation design.

## Voice provenance and limits

The grammar accepts explicit English expressions for heart rate in beats per minute, blood pressure as systolic over diastolic in mmHg, temperature in degrees Celsius, body mass in kilograms, blood glucose in mg/dL, oxygen saturation in percent, sleep in hours, exercise in minutes and pain or fatigue scores out of ten. It accepts English number words and digit strings with decimals. First-person statements beginning with “I feel,” “I have,” or “I've been feeling” can become free-text symptom drafts. Missing or unrecognized units and ambiguous values require correction. An explicit “right now” is recorded relative to submission, and a “past twenty four hours” period preserves its relative meaning. “I slept six hours last night” preserves the relative period in a review-only draft. Other timing remains unspecified. Voice recognition transcribes words. The authenticated session supplies identity.

Automatic saving requires an explicit recording request, affirmative opt-in, a valid sleep or exercise duration in the past 24 hours, complete matching per-word metadata and minimum transcription confidence 0.95. This is a software admission threshold. Physiological readings and symptoms always require review. No voice reading is fed into sensor-derived trends or treated as a verified input to clinical assessment. The private history provides a separate chronological view. The current implementation provides a visible mission medical support reminder and retains the existing engine emergency display. Automated escalation of newly reported danger and an approved clinical handoff remain pending.

Events are owner-bound, revisioned and include the source `SELF_REPORTED_VOICE`, record and audit identifiers, transcript, parsed and reported values, unit, recording/submission times and transcription confidence where available. Raw audio remains in memory. Corrections append an event. Removal appends a tombstone, with prior encrypted events still retained. Draft access is tied to the originating session. Capture IDs make retries idempotent within that session. Repeat attempts after a session change require a new explicit submission.

## Vector model and recovery

Use the official Ollama [all-minilm:l12-v2 package](https://ollama.com/library/all-minilm%3Al12-v2), Apache 2.0, 33M parameters, F16, 384 dimensions. Keep model weights out of Git. The Windows machine pulled and verified the package through the existing Ollama runtime. The observed manifest digest is:

```text
4f5da3bd944d9ad1cd3acc7d065ee54367a4c703f51fb6295bd8bc5007ed0c4a
```

```powershell
$env:OLLAMA_HOST = '127.0.0.1:8891'
.\local_ai\ollama-v0.40.6\ollama.exe pull all-minilm:l12-v2
$digest = ((Invoke-RestMethod http://127.0.0.1:8891/api/tags).models |
  Where-Object name -eq 'all-minilm:l12-v2').digest
& $py tools/demo_asthral.py prepare --personal --output data/asthral-hybrid-demo --backend-port 8931 --vector-digest $digest --enable-hybrid
& $py -m vigile.vector_evaluation --manifest data/asthral-hybrid-demo/library.json --index data/asthral-hybrid-demo/vectors.db --url http://127.0.0.1:8891 --digest $digest
& $py tools/demo_asthral.py serve --output data/asthral-hybrid-demo --backend-port 8931 --portal-port 8932
```

For a released environment, compare the reported digest against the reviewed digest before build. The system stores normalized float32 vectors and chunk provenance in ordinary SQLite. The CLI rebuilds in one transaction and the runtime performs exact cosine search. It validates the live corpus and checks index version, coverage, metadata and each vector checksum. Hybrid uses reciprocal rank fusion among existing lexical candidates, keeping the existing citation authority. The index is limited to shared verified source excerpts. Query vectors are computed at the local CPU endpoint in memory. No personal vector corpus, private chunk cache or cloud embedding service is used. Set `hybrid_enabled` to false for lexical-only, which is the default. Missing model, corrupt index or version mismatch falls back to lexical. LOW_POWER and CRITICAL use lexical search without embeddings. Existing optional PubMed egress remains restricted to explicit public topics in FULL.

To rebuild a healthy database in place, stop the portal and run `python -m vigile.vector_library --manifest PATH --index PATH --url http://127.0.0.1:8891 --digest DIGEST`. For a physically corrupt SQLite file, build to a fresh path, verify with the evaluation CLI, then point the stopped portal's configuration to that file.

The six-chunk portal corpus returned a relevant excerpt in the top two for 8/8 held-out documentary checks in each of lexical, vector and hybrid modes. Mean per-query wall time was 45 ms, 704 ms and 521 ms respectively in one local CPU-requested run including cold startup. SQLite index size was 40,960 bytes. A separate build successfully indexed 560 chunks from the existing full research manifest. The benchmark is small, single-machine and documentary. It does not establish clinical relevance for arbitrary queries or quantify peak RAM. Use lexical as the default.

## Security and acceptance boundaries

DPAPI protects backend reader token blobs and voice payloads under the portal's current Windows identity. The SQLite structure, account and event metadata, clinical database, its WAL and historical backups remain plaintext. SQLCipher supports encrypted SQLite pages and WAL, but a safe driver migration across current and archived runtimes with verified restore and key recovery has not been completed. Treat voice history and accounts as synthetic-only, restrict the data directory and avoid copying files into Git. DPAPI recovery across another Windows profile or system is not established. Same-user processes, memory inspection, arbitrary storage rollback/deletion and stolen local account credentials remain in scope for deployment review. The voice event log is append-only through the app, with DPAPI payload binding checks. It lacks an independent external integrity anchor.

Run the Python regression and simulated JavaScript lifecycle checks:

```powershell
& $py -m pytest -q
node --test tests/voice_ui_unit.cjs
& $py tools/smoke_personal_v120.py --output data/asthral-personal-smoke
```

The smoke tool requires the installed English Vosk model and SAPI. It synthesizes test audio in memory, checks both accounts through real HTTP processes, and restarts the portal. To exercise local Qwen with the shared semantic index, append `--vector-digest $digest` and choose a fresh output directory.

Use the original byte-matching runtime with isolated backups for archived replay. Validate new records with a fresh v1.2 dataset. Independent clinical, live browser, physical microphone and listening, process isolation, credential recovery and security acceptance are separate gates.
