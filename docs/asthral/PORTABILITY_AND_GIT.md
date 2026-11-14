# ASTHRAL repository portability and Git policy

The GitHub repository `GiaDiGr/ASTHRAL` is private. The repository is intended to carry ASTHRAL source, scientific documentation, historical project records, tests, synthetic fixtures and browser deployment assets so a teammate can continue work from another checkout.

ASTHRAL is the product name. `vigile` remains the Python package and engine namespace for compatibility; old VIGILE documents and original biomedical evidence remain unchanged so that their hashes, authorship and provenance remain traceable. New product-facing material should say ASTHRAL.

## What Git contains

- Deterministic biomedical engine source, schemas, clinical evidence manifests and tests.
- Frontend/browser static distribution and integration documentation.
- Synthetic regression fixtures and review reports that contain no real patient data or credentials.
- Original scientific inputs in their original form, plus clearly labeled project-authored summaries.

## What stays local

The focused `.gitignore` excludes per-machine environments and private or very large generated runtime state: Python/Node caches, SQLite databases and WAL files, access tokens and portal configuration, DPAPI material, downloaded Ollama/llama.cpp/Vosk/Piper model weights, and the installed local inference runtimes. These files are not source code; the included manifests, licenses, lockfiles and setup documentation let the second computer recreate or download them. GitHub rejects individual files at 100 MiB, so multi-gigabyte model weights cannot be pushed as ordinary Git objects.

Do not commit real astronaut or personal medical records, API keys, authentication tokens, passwords, private keys, local profile databases or unredacted access logs, even to a private repository. Private GitHub visibility does not encrypt repository contents or remove the need for credential hygiene.

## On a second Windows computer

1. Clone the private repository and review `README.md`, `SECURITY.md`, `THIRD_PARTY_NOTICES.md` and this file.
2. Install Python 3.13 x64 and recreate the engine environment from the checked-in requirements/wheelhouse instructions. Run the synthetic-only engine suite before configuring any local records.
3. For voice or local AI, download only the documented model and runtime from the official source, verify the SHA-256 values in the manifests, and keep them outside Git.
4. Create a new local data directory and fresh local credentials. Never copy another user's SQLite database or private profile into the checkout.
5. For the browser release, serve the checked-in `web-local/dist` from a local static server or deploy it through the documented Pages workflow. The browser vault is origin-scoped; its encrypted records are not part of Git.

The product's clinical and operational limitations remain unchanged: passing software tests is not independent clinical validation, mission certification or proof that every physical device works offline.
