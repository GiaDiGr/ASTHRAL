"""Measure local computer-vision model latency on deterministic synthetic inputs.

This is an engineering smoke/performance benchmark. It does not evaluate
medical accuracy, sensitivity, specificity, Dice, IoU, AUROC, or mAP.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import math
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vigile.computer_vision import (  # noqa: E402
    ECHO_WEIGHTS,
    HOLISTIC_ASSET,
    OCT_WEIGHTS,
    ComputerVisionService,
    predict_echo_frame,
)


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize(samples: list[float], units: str = "seconds") -> dict:
    ordered = sorted(samples)
    p95 = ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)]
    median = statistics.median(samples)
    return {
        "samples": len(samples),
        "units": units,
        "min": round(min(samples), 6),
        "median": round(median, 6),
        "mean": round(statistics.mean(samples), 6),
        "p95_nearest_rank": round(p95, 6),
        "max": round(max(samples), 6),
        "throughput_per_second_at_median": round(1 / median, 3) if median > 0 else None,
    }


def timed_inference(infer, warmup: int, repeats: int) -> tuple[dict, object]:
    last = None
    for _ in range(warmup):
        last = infer()
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        last = infer()
        samples.append(time.perf_counter() - started)
    return summarize(samples), last


def make_synthetic_inputs():
    x = np.linspace(0, 1, 768, dtype=np.float32)
    y = np.linspace(0, 1, 496, dtype=np.float32)[:, None]
    oct_pattern = ((0.6 * x[None, :] + 0.4 * y) * 255).astype(np.uint8)
    rows, cols = np.indices((240, 320))
    checker = ((rows // 12 + cols // 12) % 2).astype(np.uint8)
    frame = np.stack((checker * 220, ((cols * 3) % 256).astype(np.uint8), ((rows * 5) % 256).astype(np.uint8)), axis=-1)
    return oct_pattern, frame


def run_benchmark(warmup: int, repeats: int) -> dict:
    import torch

    torch.set_num_threads(min(4, torch.get_num_threads()))
    service = ComputerVisionService()
    oct_pattern, synthetic_frame = make_synthetic_inputs()
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "CPU load/inference latency and input/output smoke checks on deterministic, nonmedical synthetic patterns",
        "clinical_accuracy_evaluated": False,
        "synthetic_data_has_clinical_meaning": False,
        "configuration": {"warmup_runs_per_model": warmup, "measured_runs_per_model": repeats, "torch_cpu_threads": torch.get_num_threads()},
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor() or "not reported by operating system",
            "numpy": importlib.metadata.version("numpy"),
            "torch": importlib.metadata.version("torch"),
            "torchvision": importlib.metadata.version("torchvision"),
            "opencv": importlib.metadata.version("opencv-contrib-python"),
            "mediapipe": importlib.metadata.version("mediapipe"),
        },
        "models": {},
        "notes": [
            "Latency depends on this machine and the local model files; it is not a cross-machine performance claim.",
            "Synthetic output shape, class counts, or mask occupancy are not accuracy or clinical validity metrics.",
            "No patient data or images are read or saved by this benchmark.",
        ],
    }
    try:
        if OCT_WEIGHTS.is_file():
            entry = {"state": "WEIGHTS_PRESENT", "weight_sha256": sha256(OCT_WEIGHTS), "input": "synthetic 1x1x496x768 grayscale gradient"}
            started = time.perf_counter()
            model = service._load_oct()
            entry["load_seconds"] = round(time.perf_counter() - started, 6)
            tensor = torch.from_numpy(oct_pattern.astype(np.float32) / 255).unsqueeze(0).unsqueeze(0)

            def infer_oct():
                with torch.inference_mode():
                    logits = model(tensor)
                    mask = torch.argmax(logits, dim=1)
                return {"logits_shape": list(logits.shape), "mask_shape": list(mask.shape), "synthetic_output_labels": torch.unique(mask).cpu().tolist()}

            entry["inference"], output = timed_inference(infer_oct, warmup, repeats)
            entry["output"] = output
            result["models"]["ocularvision"] = entry
        else:
            result["models"]["ocularvision"] = {"state": "MODEL_NOT_AVAILABLE", "weights_path": str(OCT_WEIGHTS)}

        if ECHO_WEIGHTS.is_file():
            entry = {"state": "WEIGHTS_PRESENT", "weight_sha256": sha256(ECHO_WEIGHTS), "input": "synthetic 240x320 RGB checker/gradient frame"}
            started = time.perf_counter()
            model = service._load_echo()
            entry["load_seconds"] = round(time.perf_counter() - started, 6)

            def infer_echo():
                mask, overlay = predict_echo_frame(model, synthetic_frame)
                return {"mask_shape": list(mask.shape), "overlay_shape": list(overlay.shape), "synthetic_mask_occupancy_fraction": round(float(np.count_nonzero(mask) / mask.size), 6)}

            entry["inference"], output = timed_inference(infer_echo, warmup, repeats)
            entry["output"] = output
            result["models"]["echovision"] = entry
        else:
            result["models"]["echovision"] = {"state": "MODEL_NOT_AVAILABLE", "weights_path": str(ECHO_WEIGHTS)}

        if HOLISTIC_ASSET.is_file():
            entry = {"state": "WEIGHTS_PRESENT", "weight_sha256": sha256(HOLISTIC_ASSET), "input": "synthetic 240x320 RGB checker/gradient frame"}
            started = time.perf_counter()
            mp, landmarker = service._load_motion()
            entry["load_seconds"] = round(time.perf_counter() - started, 6)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=synthetic_frame)
            frame_number = 0

            def infer_motion():
                nonlocal frame_number
                frame_number += 1
                detected = landmarker.detect_for_video(mp_image, frame_number * 1000)
                return {
                    "pose_landmark_count": len(detected.pose_landmarks[0]) if detected.pose_landmarks else 0,
                    "face_landmark_count": len(detected.face_landmarks[0]) if detected.face_landmarks else 0,
                    "left_hand_landmark_count": len(detected.left_hand_landmarks[0]) if detected.left_hand_landmarks else 0,
                    "right_hand_landmark_count": len(detected.right_hand_landmarks[0]) if detected.right_hand_landmarks else 0,
                }

            entry["inference"], output = timed_inference(infer_motion, warmup, repeats)
            entry["synthetic_frame_detection"] = output
            result["models"]["motionguard"] = entry
        else:
            result["models"]["motionguard"] = {"state": "MODEL_NOT_AVAILABLE", "weights_path": str(HOLISTIC_ASSET)}

        result["models"]["skinguard"] = {
            "state": "MODEL_NOT_CONFIGURED",
            "accuracy_or_latency": None,
            "reason": "No compatible detector weights are installed; no SkinGuard inference was run.",
        }
    finally:
        service.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmup", type=int, default=1, choices=range(0, 11))
    parser.add_argument("--repeats", type=int, default=5, choices=range(1, 101))
    parser.add_argument("--output", type=Path, help="Optional path for the JSON result")
    args = parser.parse_args()
    try:
        result = run_benchmark(args.warmup, args.repeats)
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, indent=2), file=sys.stderr)
        return 1
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
