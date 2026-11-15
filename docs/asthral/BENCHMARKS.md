# ASTHRAL Computer Vision: Tests and Benchmarks

## What these results measure

ASTHRAL separates three kinds of evidence:

1. **Software tests** check inputs, transformations, exports, limits, and expected errors.
2. **Local runtime** measures loading and inference on this computer using reproducible synthetic patterns.
3. **Biomedical performance** requires authorized, clinically valid labeled data, person-level held-out partitions, comparable protocols, and independent bias review. Results in the first two categories do not establish the third.

No artificial target such as “over 90% on everything” is applied. Optimizing a score on synthetic pixels, thresholds selected after observing results, or reused data can inflate a number without improving validity. Metrics remain undefined when labels or required classes are absent.

## Reproduction commands

From `engine/` on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest tests/test_computer_vision_metrics.py -q --cov=vigile.computer_vision_metrics --cov-report=term-missing --cov-fail-under=90
.\.venv\Scripts\python.exe -m pytest tests/test_computer_vision.py tests/test_skinguard.py tests/test_computer_vision_metrics.py tests/test_benchmark_computer_vision.py -q --cov=vigile.computer_vision --cov=vigile.skinguard --cov=vigile.computer_vision_metrics --cov-fail-under=90
.\.venv\Scripts\python.exe tools/benchmark_computer_vision.py --warmup 1 --repeats 5 --output ..\artifacts\benchmarks\asthral-cv-benchmark.json
```

The benchmark creates deterministic gradients and geometric patterns. It does not use photographs, OCT scans, or echocardiograms from people. It records versions, hashes for installed weights, model load time, median/mean/p95 latency, throughput, and output shapes. Class counts or mask occupancy on those patterns describe only the observed output; they are not accuracy, Dice, IoU, or clinical evidence. SkinGuard reports `MODEL_NOT_CONFIGURED` when it has no compatible weights.

## Contributor benchmark report — 14 November 2026 (historical)

The contribution branch reports two warmups and ten measurements per model, CPU with four threads, and synthetic inputs. Full machine output is in [`artifacts/benchmarks/asthral-cv-benchmark-2026-11-14.json`](../../artifacts/benchmarks/asthral-cv-benchmark-2026-11-14.json).

| Module | Model loading | Median / p95 latency | Throughput at median |
|---|---:|---:|---:|
| OcularVision | 0.068 s | 0.839 / 0.855 s per synthetic image | 1.192 images/s |
| EchoVision | 1.686 s | 0.093 / 0.100 s per synthetic frame | 10.771 frames/s |
| MotionGuard | 1.001 s | 0.021 / 0.023 s per synthetic frame | 48.074 frames/s |
| SkinGuard | Not run | No weights configured | Not available |

These are contributor-reported measurements from before this integration. EchoVision is currently blocked by this branch until written permission and checkpoint rights are verified; the historic benchmark is not an assertion that EchoVision is available or authorized. On the synthetic pattern, MotionGuard found no landmarks, EchoVision produced a mask, and OcularVision emitted labels for a gradient. None of these outputs is an accuracy comparison.

The contributor reported **130/130** directed CV, SkinGuard, metrics, and benchmark tests; 34/34 metric-calculator tests and 99% line coverage; and a prior full run of 894 passed / 2 skipped in 264.86 seconds. Those are retained as upstream-reported historical evidence, not as independently reproduced results or current coverage claims.

## Integration verification — 15 November 2026

The full Python suite on `feature/integrate-biomedical-contribution` completed with **881 passed, 17 skipped, 0 failed** in **326.30 s**. It ran under a dedicated Python 3.13 environment with base/test dependencies and NumPy. Optional vision runtimes and model assets were not installed, so model-backed smoke tests were skipped. One Starlette/httpx deprecation warning was reported. No clinical images or data were used.

A regression test now confirms EchoVision API execution is blocked with `ECHONET_PERMISSION_NOT_VERIFIED`, and the installer refuses the EchoNet asset before creating a destination. The full run exercises that license gate and the rest of the software suite. This verifies software behavior only; it does not validate any model clinically.

## Metrics and published research context

`vigile.computer_vision_metrics` calculates Dice, IoU, pixel accuracy, precision, sensitivity, specificity, F1, AUROC, mAP@.50, and mAP@.50:.95 from supplied predictions and references. Model evaluation requires a documented held-out partition. The calculator does not create reference labels or validate a model. Its detector metric is single-class, includes negative images, and is not a replacement for a full COCO evaluation.

| Area | Result reported by the cited source | Comparison limit |
|---|---:|---|
| OCT retinal U-Net | Mean Dice 83.28%, mean IoU 72.33%, pixel accuracy 97.11% | Upstream repository result on a small dataset; not an independent evaluation or ASTHRAL result. Labels and split must be reviewed before comparison. |
| Skin lesions | At MICCAI 2026 ISIC/TBP benchmark, the cited best result is mAP@.50 67.4%, precision 70.7%, sensitivity 58.3%, F1 64.0% | Different benchmark, annotations, and model. ASTHRAL has no compatible SkinGuard detector installed; the numbers do not transfer. |
| Echocardiography | EchoNet-Dynamic paper reports LV Dice 0.92, EF mean absolute error 4.1 points, and AUC 0.97 for its evaluated tasks | Results of that study, data, protocol, and models. ASTHRAL has not been evaluated on its labeled partition and does not calculate EF. EchoVision is presently blocked pending rights review. |
| Movement | MediaPipe Holistic documents pose, face, and hand landmarks | Its technical documentation does not provide clinical rehabilitation accuracy applicable to ASTHRAL exercises. ASTHRAL angles are 2D projections, not calibrated clinical measurements. |

Sources: [OCT repository and author metrics](https://github.com/Strange-Philip/oct-retinal-layer-segmentation), [MICCAI 2026 ISIC benchmark](https://papers.miccai.org/miccai-2026-sat/ISIC_016.html), [EchoNet-Dynamic paper](https://www.nature.com/articles/s41586-020-2145-8), [official MediaPipe Holistic Landmarker documentation](https://developers.google.com/edge/mediapipe/solutions/vision/holistic_landmarker).

## Interpretation

A 100% unit-test pass means that the code matched the control cases written for those tests. 99% metric-module line coverage means tests executed 99% of that Python file's lines. Neither number measures cancer classification, retinal abnormality detection, valid echocardiographic segmentation, or rehabilitation efficacy. ASTHRAL clinical performance remains unevaluated until suitable authorized datasets, labels, and an independent protocol are available.
