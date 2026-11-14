# Contributing to ASTHRAL

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

For v1.2 changes, run the personal account and voice isolation tests, the full suite and the held-out retrieval CLI in the [integration guide](docs/asthral/PERSONAL_V120.md). Use a fresh synthetic database and byte-matching archived runtimes for replay. Stage neither vector databases nor generated private material.
