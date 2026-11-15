"""Validate a locally licensed SkinGuard detection dataset manifest."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ALLOWED_SPLITS = {"train", "validation", "test"}


def _inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("DATASET_PATH_REQUIRED")
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("DATASET_PATH_ESCAPES_ROOT")
    return target


def validate_dataset_manifest(manifest_path: Path) -> dict:
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent.resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("DATASET_MANIFEST_UNREADABLE") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("DATASET_MANIFEST_SCHEMA_UNSUPPORTED")
    dataset = manifest.get("dataset")
    if not isinstance(dataset, dict) or not all(str(dataset.get(k, "")).strip() for k in ("name", "version", "source", "license")):
        raise ValueError("DATASET_PROVENANCE_REQUIRED")
    if dataset.get("access_confirmed") is not True:
        raise ValueError("DATASET_ACCESS_TERMS_NOT_CONFIRMED")
    records = manifest.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("DATASET_RECORDS_REQUIRED")

    image_paths: set[str] = set()
    subject_splits: dict[str, set[str]] = {}
    split_counts = {split: 0 for split in sorted(ALLOWED_SPLITS)}
    box_counts = {split: 0 for split in sorted(ALLOWED_SPLITS)}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("DATASET_RECORD_INVALID")
        split, subject = row.get("split"), row.get("subject_id")
        if split not in ALLOWED_SPLITS or not isinstance(subject, str) or not subject.strip():
            raise ValueError("DATASET_SPLIT_OR_SUBJECT_ID_INVALID")
        image_rel = row.get("image")
        image_path = _inside(root, image_rel)
        annotation_path = _inside(root, row.get("annotation"))
        image_key = image_path.relative_to(root).as_posix().casefold()
        if image_key in image_paths:
            raise ValueError("DUPLICATE_IMAGE_PATH")
        image_paths.add(image_key)
        subject_splits.setdefault(subject, set()).add(split)
        if not image_path.is_file() or not annotation_path.is_file():
            raise ValueError("DATASET_FILE_MISSING")
        try:
            with Image.open(image_path) as image:
                if image.format not in ("JPEG", "PNG", "WEBP") or image.width < 64 or image.height < 64 or image.width * image.height > 20_000_000:
                    raise ValueError("DATASET_IMAGE_UNSUPPORTED")
                image.verify()
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError("DATASET_IMAGE_INVALID") from exc
        try:
            annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("DATASET_ANNOTATION_UNREADABLE") from exc
        boxes = annotation.get("boxes") if isinstance(annotation, dict) else None
        if not isinstance(boxes, list):
            raise ValueError("DATASET_ANNOTATION_SCHEMA_INVALID")
        for box in boxes:
            if not isinstance(box, dict) or box.get("label") != "skin_lesion_candidate":
                raise ValueError("DATASET_LABEL_NOT_SUPPORTED")
            coords = box.get("box_xyxy_normalized")
            if not isinstance(coords, list) or len(coords) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in coords):
                raise ValueError("DATASET_BOX_INVALID")
            x1, y1, x2, y2 = coords
            if x2 <= x1 or y2 <= y1:
                raise ValueError("DATASET_BOX_INVALID")
        split_counts[split] += 1
        box_counts[split] += len(boxes)

    if any(len(splits) != 1 for splits in subject_splits.values()):
        raise ValueError("SUBJECT_LEAKAGE_ACROSS_SPLITS")
    missing = sorted(split for split, count in split_counts.items() if count == 0)
    if missing:
        raise ValueError("TRAIN_VALIDATION_TEST_SPLITS_REQUIRED")
    return {
        "state": "DATASET_MANIFEST_VALID",
        "dataset": dataset["name"],
        "records": len(records),
        "subjects": len(subject_splits),
        "split_counts": split_counts,
        "box_counts": box_counts,
        "subject_overlap": False,
        "images_copied_or_modified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to the local dataset manifest.json")
    args = parser.parse_args(argv)
    try:
        summary = validate_dataset_manifest(args.manifest)
    except ValueError as exc:
        print(json.dumps({"state": "DATASET_REJECTED", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
