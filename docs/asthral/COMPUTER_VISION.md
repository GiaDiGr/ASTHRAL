# ASTHRAL Computer Vision

## Integration

Computer Vision is added to the existing authenticated FastAPI reader portal and its current `engine/vigile/web` navigation. The SLM, deterministic clinical routes, SQLite health records, and existing session flow remain separate and unchanged. Endpoints are protected by the existing portal session and same-origin checks:

- `GET /api/computer-vision/status`
- `POST /api/computer-vision/ocular/analyze`
- `POST /api/computer-vision/echo/analyze`
- `POST /api/computer-vision/motion/analyze`
- SkinGuard remains at `GET /api/skinguard/status` and `POST /api/skinguard/analyze`.

Uploads are bounded, held in memory, and excluded from SQLite. Video decoders use temporary files that are deleted when processing ends. The browser keeps selected previews and longitudinal summaries only for the current page session. Webcam recording is explicit and uses the browser's camera permission.

## Install the runtime

Run from `engine/` in PowerShell. The 4 GB laptop GPU is not selected; inference uses CPU.

```powershell
.\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
.\.venv\Scripts\python.exe -m pip install -e ".[vision]"
```

The optional extra pins MediaPipe 0.10.21 (modern Tasks Holistic Landmarker), NumPy 1.26.4, OpenCV-contrib 4.11.0.86, PyTorch 2.5.1 and Torchvision 0.20.1. The versioned API uses `HolisticLandmarker` in `VIDEO` mode; it does not mix legacy `solutions.holistic` classes.

## Install model assets

Model weights and the Holistic `.task` file are local-only and excluded by `.gitignore`. Select a model explicitly; `echo` is about 303 MiB. The script checks SHA-256 and will not replace a mismatched local file.

```powershell
.\.venv\Scripts\python.exe tools\install_computer_vision_models.py --model oct
.\.venv\Scripts\python.exe tools\install_computer_vision_models.py --model echo
.\.venv\Scripts\python.exe tools\install_computer_vision_models.py --model motion
```

| Module | Local model | Provenance | SHA-256 | Current scope |
|---|---|---|---|---|
| SkinGuard | None installed | Candidate code/data audited; no verified compatible total-body lesion detector weights | — | Image intake and local previews work. No boxes, lesion classifications, malignancy probabilities, or model metrics are generated. |
| OcularVision | `engine/local_ai/computer-vision/oct/best_model.pth` | [MIT OCT retinal-region U-Net](https://github.com/Strange-Philip/oct-retinal-layer-segmentation); trained on 10 subjects / 110 manually annotated Duke/Chiu 2015 B-scans per its project README | `e085d37bc04f716ee3417bbd768fa4aa392a24fb62c0371e066279e6dd7d314a` | Real 8-class inference: background plus seven inter-boundary retinal regions. Aspect-preserving fit to 768×496; pixel widths by default. Optional user-supplied µm/px only. No SANS detection or ASTHRAL external validation. |
| EchoVision | `engine/local_ai/computer-vision/echo/deeplabv3_resnet50_random.pt` | [EchoNet-Dynamic v1.0.0 release](https://github.com/echonet/dynamic/releases/tag/v1.0.0) | `b32ea45b8200e11298ff4021166ff8d187204fb0c27a937bcdb4c518ffcbe1ed` | Real frame-wise LV mask on user-confirmed A4C clips. Experimental per-frame RGB normalization and 112×112 resize are documented in each report. No EF prediction. The upstream code license restricts redistribution; checkpoint has no separate license statement located. Keep local and confirm research-use rights before sharing. |
| MotionGuard | `engine/local_ai/computer-vision/motion/holistic_landmarker.task` | [Google AI Edge Holistic Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/holistic_landmarker), modern Tasks API | `e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8` | Real pose, face and hand landmark inference; projected 2D angles, angular velocity, ROM, descriptive bilateral ROM, configurable excursion-based repetition counts, tracking-loss markers. No physical displacement, forces, moments, or clinical state. |

The EchoNet dataset is not installed or distributed. Its access terms are separate and restrict use to non-commercial research. This prototype does not load or distribute the dataset. See [EchoNet's input description](https://github.com/echonet/dynamic/blob/master/README.md), [software license](https://github.com/echonet/dynamic/blob/master/LICENSE.txt), and [Stanford dataset use terms](https://echonet.github.io/dynamic/).

## Processing limits and outputs

- Images: JPEG, PNG, WebP, or TIFF up to 10 MiB and 20 megapixels. EXIF orientation is applied. The OCT report states source dimensions, conversion, scale and inference parameters.
- Videos: MP4, WebM, MOV, AVI or MKV up to 9 MiB, 20 seconds, 600 frames, and 12 megapixels per decoded frame. Inference samples every configurable Nth frame (maximum 180 analyzed frames). Rotation and mirror transforms are recorded and reversed in video overlays.
- EchoVision requires a user confirmation of A4C view. It does not accept an arbitrary ultrasound as an echo study and does not estimate ejection fraction.
- MotionGuard exports normalized landmark coordinates (pose, face, both hands, and world pose) in JSON/CSV. Angles are calculated in the rotated/mirrored image plane and labelled projected 2D.
- Reports and overlay images/videos are downloaded by the user. Longitudinal summaries are compared only in the current browser session and only when relevant model, dimensions, scale or view conditions match.
- Input errors, absent files, corrupt decoders, busy inference, and model-load failures return explicit error codes. No fallback produces fabricated results.

## Validation boundary

ASTHRAL has no valid held-out dermatology, OCT, or echo evaluation set installed. It has therefore not calculated or claimed SkinGuard mAP/sensitivity/precision, OCT Dice/IoU, Echo Dice/IoU, classification AUROC/sensitivity/specificity, or clinical performance. Model-provider metrics in upstream material are not ASTHRAL results. The installed OCT and EchoNet checkpoints are demonstration/research models, not clinically validated ASTHRAL models.

No sample medical images or videos are bundled. The model loaders and tensor input/output contracts can be smoke-tested locally, but sample-based end-to-end validation requires a legally obtained, compatible input file. Do not use example outputs or synthetic test tensors as clinical results.

## Start the integrated portal

Use the repository's normal launcher from `engine/` after preparing/verifying its existing demo dataset:

```powershell
.\.venv\Scripts\python.exe tools\demo_asthral.py serve --output data\asthral-demo
```

The portal remains at `http://127.0.0.1:8922/`. If an older portal process is already open, close it from the terminal/supervisor that started it, then run the launcher again; the supervisor intentionally refuses occupied ports rather than replacing processes it does not own.
