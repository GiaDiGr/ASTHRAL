"""Train and hold out an experimental YOLO detector on a local licensed dataset.

This script never downloads base weights or data. It requires explicit license
review acknowledgement because Ultralytics is AGPL-3.0/Enterprise dual licensed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vigile.skinguard_data import validate_dataset_manifest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_yolo_dataset(manifest_path: Path, target: Path) -> tuple[Path, dict, str]:
    validate_dataset_manifest(manifest_path)
    root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = hashlib.sha256()
    image_root, label_root = target / "images", target / "labels"
    for split in ("train", "validation", "test"):
        (image_root / split).mkdir(parents=True)
        (label_root / split).mkdir(parents=True)
    for index, row in enumerate(manifest["records"]):
        image_path = (root / row["image"]).resolve()
        annotation_path = (root / row["annotation"]).resolve()
        suffix = image_path.suffix.lower()
        if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
            raise ValueError("IMAGE_EXTENSION_UNSUPPORTED_FOR_YOLO")
        stem = f"{index:08d}"
        split = row["split"]
        shutil.copyfile(image_path, image_root / split / f"{stem}{suffix}")
        annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
        label_lines = []
        for box in annotation["boxes"]:
            x1, y1, x2, y2 = box["box_xyxy_normalized"]
            cx, cy, width, height = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
            label_lines.append(f"0 {cx:.8f} {cy:.8f} {width:.8f} {height:.8f}")
        (label_root / split / f"{stem}.txt").write_text("\n".join(label_lines), encoding="utf-8")
        for local_path, source_path in ((row["image"], image_path), (row["annotation"], annotation_path)):
            snapshot.update(local_path.encode("utf-8"));snapshot.update(bytes.fromhex(sha256_file(source_path)))

    yaml_path = target / "dataset.yaml"
    root_text = target.resolve().as_posix()
    yaml_path.write_text(
        f'path: {json.dumps(root_text)}\n'
        'train: images/train\n'
        'val: images/validation\n'
        'test: images/test\n'
        'names:\n  0: skin_lesion_candidate\n',
        encoding="utf-8",
    )
    return yaml_path, manifest, snapshot.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--base-weights", required=True, type=Path, help="Existing local YOLOv8/YOLO11 detection checkpoint")
    parser.add_argument("--output", required=True, type=Path, help="New output folder inside engine/data")
    parser.add_argument("--model-id", required=True, help="Short non-identifying model version label")
    parser.add_argument("--code-license", required=True, choices=("AGPL-3.0", "Ultralytics-Enterprise"))
    parser.add_argument("--base-weights-license", required=True)
    parser.add_argument("--score-threshold", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="cpu", help="cpu or a local device such as 0")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--confirm-license-review", action="store_true", help="Confirm code, base-weight, and dataset terms were reviewed")
    args = parser.parse_args(argv)

    try:
        manifest_path = args.manifest.resolve()
        weights_path = args.base_weights.resolve()
        output = args.output.resolve()
        data_root = (ROOT / "data").resolve()
        if not output.is_relative_to(data_root) or output == data_root:
            raise ValueError("OUTPUT_MUST_BE_NEW_FOLDER_UNDER_ENGINE_DATA")
        if output.exists():
            raise ValueError("OUTPUT_FOLDER_ALREADY_EXISTS")
        if not weights_path.is_file():
            raise ValueError("LOCAL_BASE_WEIGHTS_REQUIRED; no weights were downloaded")
        if not args.confirm_license_review:
            raise ValueError("REVIEW_CODE_WEIGHT_AND_DATA_LICENSES_FIRST")
        if not 0 <= args.score_threshold <= 1 or not math.isfinite(args.score_threshold):
            raise ValueError("INVALID_SCORE_THRESHOLD")
        validate_dataset_manifest(manifest_path)
        try:
            from ultralytics import YOLO
            import onnxruntime as ort
        except ImportError as exc:
            raise ValueError("Install the separately reviewed Ultralytics package and optional ONNX Runtime first") from exc

        output.mkdir(parents=True)
        dataset_yaml, dataset_manifest, dataset_hash = prepare_yolo_dataset(manifest_path, output / "dataset")
        config = {
            "model_id": args.model_id,
            "task": "SKIN_LESION_LOCALIZATION",
            "dataset": dataset_manifest["dataset"],
            "dataset_manifest_sha256": sha256_file(manifest_path),
            "dataset_content_snapshot_sha256": dataset_hash,
            "base_weights_sha256": sha256_file(weights_path),
            "ultralytics_version": importlib.metadata.version("ultralytics"),
            "onnxruntime_version": importlib.metadata.version("onnxruntime"),
            "code_license_reviewed_as": args.code_license,
            "base_weights_license_reviewed_as": args.base_weights_license,
            "seed": args.seed,
            "image_size": args.imgsz,
            "epochs": args.epochs,
            "batch": args.batch,
            "device": args.device,
            "test_score_threshold": args.score_threshold,
            "test_split_used_for_model_selection": False,
        }
        (output / "training_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

        model = YOLO(str(weights_path), task="detect")
        model.train(
            data=str(dataset_yaml), imgsz=args.imgsz, epochs=args.epochs, batch=args.batch,
            device=args.device, seed=args.seed, deterministic=True, workers=0,
            project=str(output), name="training", exist_ok=False,
        )
        best_path = Path(model.trainer.save_dir) / "weights" / "best.pt"
        if not best_path.is_file():
            raise ValueError("TRAINING_DID_NOT_PRODUCE_BEST_CHECKPOINT")

        best = YOLO(str(best_path), task="detect")
        evaluation = best.val(
            data=str(dataset_yaml), split="test", imgsz=args.imgsz,
            conf=args.score_threshold, device=args.device, plots=True,
            project=str(output), name="heldout-test", exist_ok=False,
        )
        metrics = {}
        for key, value in evaluation.results_dict.items():
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                metrics[key] = number
        evaluation_report = {
            "task": "SKIN_LESION_LOCALIZATION",
            "split": "SUBJECT_LEVEL_HELD_OUT",
            "dataset": dataset_manifest["dataset"]["name"],
            "dataset_version": dataset_manifest["dataset"]["version"],
            "score_threshold_fixed_before_test": args.score_threshold,
            "metrics": metrics,
            "malignancy_classification_performed": False,
            "clinical_validation": False,
        }
        (output / "evaluation.json").write_text(json.dumps(evaluation_report, indent=2), encoding="utf-8")
        evaluation_hash = sha256_file(output / "evaluation.json")

        exported_path = best.export(format="onnx", imgsz=args.imgsz, batch=1, nms=True, dynamic=False, simplify=False)
        onnx_path = Path(exported_path).resolve()
        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        inputs, outputs = session.get_inputs(), session.get_outputs()
        if len(inputs) != 1 or len(inputs[0].shape) != 4 or not outputs:
            raise ValueError("EXPORTED_ONNX_CONTRACT_UNSUPPORTED")
        manifest_out = {
            "schema_version": 1,
            "review_status": "NOT_REVIEWED",
            "model_id": args.model_id,
            "task": "SKIN_LESION_LOCALIZATION",
            "input_modality": "TOTAL_BODY_PHOTOGRAPH",
            "license": {
                "code": args.code_license,
                "weights": args.base_weights_license,
                "training_data": dataset_manifest["dataset"]["license"],
                "reviewed": True,
            },
            "source_url": "https://github.com/ultralytics/ultralytics",
            "training_data": {
                "name": dataset_manifest["dataset"]["name"],
                "version": dataset_manifest["dataset"]["version"],
                "source": dataset_manifest["dataset"]["source"],
                "license": dataset_manifest["dataset"]["license"],
                "subject_split_method": "Patient/subject identifiers are isolated across train, validation, and test; checked by vigile.skinguard_data.",
                "manifest_sha256": config["dataset_manifest_sha256"],
                "content_snapshot_sha256": dataset_hash,
            },
            "evaluation": {
                "dataset": f"{dataset_manifest['dataset']['name']} {dataset_manifest['dataset']['version']}",
                "split": "SUBJECT_LEVEL_HELD_OUT",
                "metrics_report": "evaluation.json",
                "metrics_report_sha256": evaluation_hash,
            },
            "weights_sha256": sha256_file(onnx_path),
            "input": {"width": args.imgsz, "height": args.imgsz, "layout": "NCHW_RGB_FLOAT_0_1", "resize": "LETTERBOX_114"},
            "output": {
                "tensor_name": outputs[0].name,
                "layout": "XYXY_SCORE_CLASS_INPUT_PIXELS",
                "labels": ["skin_lesion_candidate"],
                "score_threshold": args.score_threshold,
            },
        }
        (output / "model.manifest.json").write_text(json.dumps(manifest_out, indent=2), encoding="utf-8")
        print(json.dumps({"state": "TRAINING_AND_HELDOUT_EVALUATION_COMPLETE", "output": str(output), "test_metrics": metrics, "model_manifest_review_status": "NOT_REVIEWED", "clinical_validation": False}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({"state": "TRAINING_OR_EVALUATION_FAILED", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
