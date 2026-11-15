# ASTHRAL SkinGuard

SkinGuard is an authenticated, local portal module for documenting a skin photo and its context. The checked-in version is a research intake and model-loading scaffold. **This checkout has no dermatology weights or labeled dermatology images, so its default state is `MODEL_NOT_CONFIGURED`; it does not perform AI analysis or draw detections.** Image validation and report creation work without a model.

## Current behavior

- Accepts JPEG, PNG, and WebP images up to 10 MiB; dimensions are capped at 8,192 px per side and 20 megapixels.
- Includes a coarse mean-brightness/clipping heuristic. It is unvalidated and only warns about possible dark or clipped images; it does not establish that a photo is suitable for dermatologic assessment.
- Validates that the bytes decode as the declared image format. Pixel data is used in memory and is not written to the server or database. EXIF and other source metadata are omitted from the report.
- Up to five current-session photo references (30 MiB total) can be selected for side-by-side visual follow-up in the browser. They are not persisted across reloads and are not uploaded as a history. No automated pixel comparison or clinical change inference is performed.
- The JSON report contains entered dates and notes, never image bytes. An optional visual HTML report embeds the current and selected reference photos only after the user clicks its download button.
- UV exposure is a user-reported descriptive context. UV is non-ionizing and differs from ionizing space radiation. A photo cannot identify a radiation cause.
- No cancer classification, diagnosis, treatment recommendation, or clinical action is provided. If a local research detector is configured, it can only return candidate-region boxes. Its score is a model output score, not a calibrated probability.

## Local detector loading

The optional loader looks only in `engine/local_ai/skinguard/` for `model.onnx` and `model.manifest.json`. It will not download a model. Install the optional CPU runtime from `engine/` with:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[skinguard]"
```

Copy [skinguard-model-manifest.example.json](skinguard-model-manifest.example.json) to `engine/local_ai/skinguard/model.manifest.json`, then fill it with the exact model, dataset, license, evaluation, tensor names, and SHA-256 provenance. The example deliberately has `review_status: NOT_REVIEWED` and an empty hash, so it cannot load. Before using real weights, review the code, weight and training-data licenses, source, total-body-photo modality, subject-level split, independent held-out results, intended use, and safety limitations. Set `review_status` to `RESEARCH_REVIEWED` only after that review. This is a local research-use attestation, not clinical validation.

The required ONNX contract is a float32 RGB NCHW image scaled to 0–1, letterboxed with value 114 to the declared dimensions. The selected output tensor must be rows of `[x1,y1,x2,y2,score,class_id]`, in normalized coordinates or model-input pixels, with class `0` equal to `skin_lesion_candidate`. Boxes are mapped back to the original photo before display. No malignancy classes are accepted. A hash mismatch, unsupported task/modality/output, absent runtime, or incomplete manifest leaves analysis unavailable.

## Dataset preparation gate

No training dataset is included. Obtain and review dataset access terms yourself; do not add licensed images to Git. Create a local `manifest.json` beside your image/annotation tree:

```json
{
  "schema_version": 1,
  "dataset": {
    "name": "DATASET_NAME",
    "version": "VERSION",
    "source": "SOURCE_URL",
    "license": "LICENSE_OR_ACCESS_TERMS",
    "access_confirmed": true
  },
  "records": [
    {
      "image": "images/example.jpg",
      "annotation": "annotations/example.json",
      "subject_id": "PSEUDONYMOUS_SUBJECT_ID",
      "split": "train"
    }
  ]
}
```

Each annotation file has `{"boxes":[{"label":"skin_lesion_candidate","box_xyxy_normalized":[0.1,0.2,0.3,0.4]}]}`. Use pixel coordinates normalized to `[0,1]`; empty `boxes` means no candidate region was annotated. The validator rejects paths outside the dataset root, missing or malformed image/annotation files, unsupported labels/boxes, duplicate images, absent train/validation/test splits, and any subject that appears in multiple splits. It prints only aggregate counts and does not copy or modify images:

```powershell
Set-Location engine
.\.venv\Scripts\python.exe -m vigile.skinguard_data C:\path\to\licensed-dataset\manifest.json
```

The preparation gate checks all three splits and keeps each subject in only one split. It prints aggregate counts only. For the optional training pipeline, first review the current Ultralytics and base-weight licenses. Install Ultralytics separately in the local environment; it is deliberately not a project dependency:

```powershell
Set-Location engine
.\.venv\Scripts\python.exe -m pip install ultralytics
.\.venv\Scripts\python.exe tools\train_skinguard.py `
  --manifest C:\path\to\licensed-dataset\manifest.json `
  --base-weights C:\path\to\local\yolo11n.pt `
  --output data\skinguard_runs\yolo11n-experiment-01 `
  --model-id skinguard-yolo11n-experiment-01 `
  --code-license AGPL-3.0 `
  --base-weights-license "REVIEWED_WEIGHT_LICENSE" `
  --confirm-license-review
```

The script requires a pre-existing local detection checkpoint, never downloads weights/data, stages a copy of the labeled data under the ignored `engine/data/` folder, trains with a fixed seed, evaluates on the untouched subject-level test split at the predeclared score threshold, exports ONNX, and writes an evaluation report plus a model manifest marked `NOT_REVIEWED`. It does not perform malignancy classification or calibration, and it does not report subgroup performance unless a separately reviewed extension adds valid subgroup data. Test metrics are produced only when the user runs this script on their licensed data; none are claimed in this repository.

The ONNX, manifest, and hashed held-out `evaluation.json` are saved under the run output (the exported ONNX is in `training/weights/`). To test local inference, install ONNX Runtime with `pip install -e ".[skinguard]"`, copy the ONNX to `engine/local_ai/skinguard/model.onnx`, the manifest to `engine/local_ai/skinguard/model.manifest.json`, and the matching `evaluation.json` to `engine/local_ai/skinguard/evaluation.json`. The loader checks both hashes. Then have a qualified reviewer inspect and explicitly update the manifest review fields. Do not copy any image data into Git. No training or evaluation was run in this checkout because the licensed dataset and base weights are absent.

## Source audit and model choice

No code, data, or weights from the repositories below are bundled. Their current task and licensing do not provide a drop-in, verified total-body detector:

| Source | Relevance | SkinGuard decision |
| --- | --- | --- |
| [iToBoS Lesion Detection Challenge](https://github.com/iToBoS/Lesion-Detection-Challange) | Total-body photography detection benchmark tooling; data are obtained separately through [Kaggle](https://www.kaggle.com/competitions/itobos-2024-detection). | Potential research data source, subject to current access terms; the repository license reference was not verifiable in the audit. No model weights bundled. |
| [CIRS-Girona/tbp_lesion_detection](https://github.com/CIRS-Girona/tbp_lesion_detection) | MIT-licensed benchmark code for lesion detection on total-body photography. | Research reference, not a ready checkpoint; requires licensed data and training. |
| [uts58/yolov8-ham10000](https://github.com/uts58/yolov8-ham10000) | Image-level class prediction using dermoscopic HAM10000/ISIC data. | Not a total-body-photo detector; no default use. |
| [hadeeralkady/Skin-Lesion-Detection-using-YOLOv8](https://github.com/hadeeralkady/Skin-Lesion-Detection-using-YOLOv8) | Detection/classification workflow centered on ISIC dermoscopy. | No verified, licensed checkpoint selected. |
| [ilyanovo/isic-2024](https://github.com/ilyanovo/isic-2024) | Apache-2.0 challenge code for image-level ISIC malignant classification. | Different task and modality; code license does not grant rights to weights/data. |
| [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) | General detector framework. | Not installed by default; review its [AGPL-3.0/Enterprise terms](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) before any use. |

NASA's [human-system standard](https://standards.nasa.gov/standard/NASA/NASA-STD-3001_VOL_1) and the [NASA spaceflight dermatitis case report](https://ntrs.nasa.gov/citations/20220014684) are context only. SkinGuard does not claim NASA compliance, attribute lesions to radiation, or replace astronaut medical care.

## Tests

Run the focused SkinGuard tests from `engine/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_skinguard.py -q
```
