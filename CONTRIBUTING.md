# Contributing to ASTHRAL

## Keep every workstation's work

GitHub is the shared record for **committed work on each branch**. Uncommitted edits, untracked files, and local model assets do not travel with a pull. Start by checking the folder and the branch you are on:

```powershell
git status --short --branch
git branch --show-current
& .\engine\tools\sync_asthral.ps1 -FetchOnly
```

The Computer Vision modules and their reported results are maintained on `feature/asthral-computer-vision`. Browser release evidence is maintained separately on `main`. Choose the branch that contains the work you mean to continue; a newer commit on one branch does not replace the other branch's history.

For a new Computer Vision workstation, clone that branch directly:

```powershell
git clone --branch feature/asthral-computer-vision https://github.com/GiaDiGr/ASTHRAL.git
Set-Location ASTHRAL
& .\engine\tools\sync_asthral.ps1
```

For an existing checkout, run `sync_asthral.ps1` from any folder inside the repository. It fetches the current branch's configured remote, without pruning branches. It updates only by fast-forward, creates a local backup branch before moving the current branch, and refuses to proceed when it finds local/untracked changes, divergent history, or incoming file deletions. It does not switch branches, merge `main` into a feature branch, push, reset, or clean files. `-FetchOnly` refreshes the remote references without moving the local branch.

If it stops for local changes, review and commit them to a feature/checkpoint branch before trying again. Do not discard them to make the updater pass. If it reports a deletion or divergence, inspect `git diff --name-status HEAD..origin/<branch>` and preserve a backup branch before manually merging. Resolve only after checking that the result retains all intended work. A clean merge with unexpected changes can be cancelled with `git merge --abort`. Keep separate clones or Git worktrees for branches that have different file sets.

### Start and publish a change

For work based on the stable branch, create a feature branch from the fetched `origin/main`. For Computer Vision changes, branch from `origin/feature/asthral-computer-vision` so the modules and their tests stay in scope:

```powershell
git fetch origin --no-tags
git switch -c feature/your-change origin/main
# For a Computer Vision change, use this start point instead:
# git switch -c feature/your-change origin/feature/asthral-computer-vision
# Edit, run relevant tests, and inspect every staged path.
git add -- path/to/reviewed/files
git diff --cached
git commit -m "Describe the behavior change"
git push -u origin feature/your-change
```

Never force-push, rewrite another contributor's commits, run `git reset --hard` or `git clean` to synchronize, or include databases, WAL/SHM, backups, logs, secrets, DPAPI envelopes, runtime configurations, model weights, or nonredistributable source papers. Review staged files AND history; gitignore does not remove a committed secret. Do not paste access codes or tokens into issues, PR bodies, Actions, screenshots, fixtures, or prompts. Synthetic fixture credentials must be explicit and must never be usable against a real service.

For the current Computer Vision verification, see `docs/asthral/BENCHMARKS.md`. Run the full Python suite from `engine/` with `python -m pytest -q`; run `python -m pytest tests/test_sync_asthral.py -q` to check the four cross-workstation preservation scenarios. The report distinguishes software tests and local synthetic latency from clinical model evaluation.

A PR must explain the trigger and resulting behavior, actual tests/results, privacy effects, compatibility/migration, and limitations. Changes to clinical criteria, units, time windows, confirmation, doses, or safety restrictions require documented source justification and independent clinical review. A software role never grants mission treatment authority. Never promote remote references into rules or verified evidence automatically.

Local RAG remains the base. Online retrieval takes an approved public topic ID only, is opt-in under trusted configuration, and uses the actual operating mode. Keep unreviewed remote references out of the LLM and deterministic engine. Add transport-level privacy/mode/SSRF tests for every provider change. Retain original-language provenance and explicitly mark presentation translations; do not translate identifiers, numbers, units, or negations.

Run the new English/local/hybrid acceptance suite separately from historical retrieval benchmarks. Never describe a reused benchmark as a new independent test or software tests as clinical validation. Record visual and physical voice checks only when actually performed. No new project license, collaborator permissions, production deployment, or publication of private records without owner authorization.
