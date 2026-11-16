# ASTHRAL repository audit — 15 November 2026

## Scope and audited state

This audit checked the fetched `main` tree, tracked repository layout, the main README and secondary entry documents, release evidence, active NASA integration notes, Computer Vision code/status documents, Git branch ancestry, and root-level governance files. The audit began from a clean local `main` at `876a751b4cb7162e46d6014418851b647e90b257`, equal to `origin/main`. The source tree contains the existing Python engine, the `web-local/` browser application, and the four Computer Vision module adapters.

The release test report remains applicable to the integrated application code: the diff from the report's PR #6 integration commit to the audited `main` contained only README/report text and the two participant image assets. The tests were not rerun for this documentation cleanup.

## Reconciled statements

| Topic | Audited finding | Documentation rule |
|---|---|---|
| Product identity | The current product is ASTHRAL. `engine/vigile/`, Python imports, historical rule identifiers, and immutable source packages retain the original identifier for compatibility and provenance. | Do not present VIGILE as the current product; do not rename the internal package without a migration. |
| Computer Vision | `engine/vigile/computer_vision.py`, `skinguard.py`, `cv_unet.py`, and related tests exist on `main`. Model availability is separate from code presence. | Describe the four modules as integrated software and state each missing-model/license limitation. |
| NASA sources | The browser Radiation Explorer queries NASA OSDR RadLab historical records. DONKI is a separate contextual space-weather client. | Do not say ASTHRAL has no NASA API integration; do not call archive observations personal dosimetry or DONKI a clinical decision source. |
| PubMed | PubMed/NCBI E-utilities is the only online provider in the scientific-reference RAG pipeline. | Scope that statement to RAG, distinct from the RadLab and DONKI data integrations. |
| Current software results | The latest integrated report records 958 Python passes, 19 skips, 148 browser tests, and 3 palette regressions. The full mission-control acceptance remained incomplete, and CelesTrak returned HTTP 403. | Keep pass counts tied to the exact local report; do not claim full mission acceptance or live ISS availability. |
| AI/model assets | Model weights, local runtimes, voice assets, databases, and credentials are provisioned locally and excluded from Git. | Do not imply a model is uploaded merely because its adapter or manifest is in the repository. |

## Branch snapshot

After fetching `origin`, all **13 remote `feature/*` branch tips** were ancestors of `origin/main`; there were no commits unique to those branch tips at this snapshot. The branch refs are retained for contributor history. This ancestry check does not guarantee that every old file remains unchanged in the current tree. Before new work, fetch again and compare the actual branch and file trees. Create new topic work from current `origin/main`; do not merge stale feature refs just to make their names appear current. No remote branches were deleted.

## Repository structure and governance

- Current product entrypoint: root `README.md`; detailed current documents are indexed in this folder.
- Application code: `engine/` and `web-local/`; supporting scripts: `tools/`.
- Reproducibility and verification evidence: `artifacts/` and dated `docs/asthral/` reports.
- Original research lineage, archived release packages, and older instructions remain in the repository because release manifests and provenance records refer to them. They are historical material, not current setup guidance. Do not silently rewrite their hashes or historical claims.
- No root `LICENSE` is present, so no project-wide redistribution license is asserted.
- No `.github/workflows/` directory is present. The published test counts are local verification, not GitHub Actions results.

## Audit boundary

This is a repository orientation and consistency audit, not a line-by-line clinical, legal, security, or scientific validation of all historical records. Historical documents keep their dated scope. Clinical and operational review, model evaluation on valid held-out datasets, and flight qualification remain outstanding.
