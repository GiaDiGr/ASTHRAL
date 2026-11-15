# ASTHRAL teammate integration audit — 15 November 2026

## Scope and provenance

This review preserves the existing ASTHRAL project and integrates the identified `feature/asthral-computer-vision` contribution into an isolated branch, `feature/integrate-biomedical-contribution`, based on `origin/main` at `4187749f1ffd1964fcfedc283f399326b1c00fba`. The original `C:\Users\Gianni\Desktop\Vigile` checkout remains on `main` at `1084b76b2aae8129d8ea9f9c2bde72168e9f4890`; it was not checked out, merged, or edited.

The source branch tip is `84e2ea460e72e40e479bd19cc8ce1c2ee0605e1e`. It contains four commits by Fabian A. Nana on 14 November 2026:

- `50b3042d9bdde71dba86048ad3665bbb53d2f6f3` — multimodal CV modules and login background.
- `d109463d0a7a53153d36430badd98a06f3294b5d` — login overlay adjustment.
- `be7640ad64974df9cffd8bcb7ecfdb5f55b08212` — CV benchmarks and evaluation tooling.
- `84e2ea460e72e40e479bd19cc8ce1c2ee0605e1e` — test results and safe team sync documentation.

The source contribution is retained in Git history. The one README conflict was resolved by preserving both the repository map and the contributor's dated result section. The integration branch does not update `main`.

## Contribution inventory

The added modules are:

- **OcularVision:** OCT retinal inter-boundary region segmentation. Outputs pixel-region masks and optional user-scaled dimensions. It does not detect SANS or emit a diagnosis.
- **EchoVision:** frame-wise left-ventricle mask adapter for A4C echocardiography. It does not calculate ejection fraction. **Execution and download are blocked** pending written permission and verified checkpoint rights.
- **MotionGuard:** MediaPipe landmarks and descriptive projected 2D angles, angular velocity, range of motion, and repetition heuristics. These are not calibrated 3D measurements or clinical assessments.
- **SkinGuard:** local image intake, quality heuristics, report generation, and a provenance-gated single-class candidate localizer. No compatible lesion detector, weights, or labeled image set is installed. The module does not classify malignancy, diagnose, or infer radiation causation.
- Evaluation metrics, synthetic benchmark and training-data tooling, model manifests, portal/UI adapters, tests, and integration documents.

The modules use the existing authenticated local FastAPI reader portal. They are not integrated into the static Cloudflare PWA/Pyodide runtime. The visual page's user-facing labels, including SkinGuard, were translated into English. The internal Python package remains `vigile` for compatibility; product/portal branding remains ASTHRAL.

## Integration changes

- Updated the portal's route-scoped upload budget to 15 MiB for SkinGuard and CV analyze requests, while retaining smaller defaults for unrelated POSTs and the existing voice budget. This covers the documented base64-encoded 10 MiB images and 9 MiB videos plus JSON overhead. A regression test verifies that a 20 KiB request reaches request validation instead of being rejected by the generic 16 KiB limit.
- Preserved existing session, same-origin, Trusted Host, CSRF, rate-admission, Content-Security-Policy, and `camera=(self)` controls. Analysis routes remain session-protected. Uploaded images/results remain in request/browser memory; video decode files use temporary storage and cleanup in `finally`.
- Added `LICENSE_REVIEW_REQUIRED` and `execution_enabled: false` for EchoVision. `analyze_echo`, `_load_echo`, the HTTP endpoint, and the model installer fail closed with `ECHONET_PERMISSION_NOT_VERIFIED`. The `all` installer selection does not include EchoNet. The browser disables EchoVision submit until an API status explicitly says execution is enabled.
- Pinned runtime SHA-256 checks for the OCT checkpoint and MediaPipe task asset; mismatched files are rejected before loading. PyTorch checkpoint deserialization uses `weights_only=True` to avoid unrestricted pickle loading.
- Updated README and Computer Vision documentation to separate this run from historical contributor benchmark/test reports, and to describe EchoNet as unavailable until rights review.

## Security and operational boundaries

No credentials, local database, health records, model weights, or medical images were added. Model assets and virtual environments remain ignored/local-only. SQLite encryption is not provided by this CV contribution or by the existing engine; the broader project limitation remains documented elsewhere. A same-user process is not isolated from the portal. A hard process crash can leave a temporary video file before Python cleanup runs; OS permissions and scheduled cleanup/containment remain deployment responsibilities. The audit chain protects against ordinary app-level edits but cannot prove integrity against an attacker who can modify the underlying storage.

The model download and load SHA-256 checks protect against accidental substitution relative to the reviewed pins; they do not establish author authenticity, licensing rights, model correctness, or clinical validity. EchoNet source code has a restrictive permission statement and the checkpoint's separate license was not verified. No written permission was found, so EchoVision is unavailable regardless of whether a local file is manually placed.

## Verification

The full test suite was run from `engine/` in the isolated worktree with Python 3.13.17, a fresh virtual environment, project base/test dependencies, and NumPy 2.5.4 (the pinned optional vision stack is not compatible with this Python version as declared). It used synthetic software inputs only; no clinical data or images were used.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Final result: **882 passed, 17 skipped, 0 failed, 261.90 seconds**, with one Starlette/httpx deprecation warning. The skips were 13 tests requiring the absent OpenCV runtime, two requiring absent PyTorch, and two requiring local voice dependencies. The focused CV, installer, and portal suite after adding hash validation passed **58 passed, 15 skipped, 0 failed, 9.10 seconds**, with the same warning. The full console log and JUnit XML are stored in `artifacts/integration/`.

The contributor's branch separately reports 894 passed / 2 skipped and its historical synthetic benchmarks; these figures are not the integration run. A passing synthetic/software suite is not clinical, operational, or flight validation. Model-backed behavior remains untested here because optional weights and model runtimes are absent.

## Independent review still required

Before any astronaut-facing use, a separate professional and organizational review is required for image modality suitability, clinical measurement interpretation, task applicability, human-factors/UI wording, model/dataset licensing, validation cohorts, bias, and mission-specific operational procedures. No condition thresholds or deterministic biomedical rules are changed by this contribution. OcularVision, MotionGuard, and SkinGuard outputs remain research-only. EchoVision must remain blocked until legal rights and permission are documented and the change receives a separate review.
