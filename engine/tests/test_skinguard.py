import base64
import json
from pathlib import Path

import pytest
from PIL import Image

from vigile.skinguard import (
    SkinGuardInputError,
    SkinGuardRequest,
    SkinGuardService,
    decode_image_data_url,
    load_local_detector,
    validate_detections,
    validate_model_manifest,
)
from vigile.skinguard_data import validate_dataset_manifest
from tools.train_skinguard import prepare_yolo_dataset


def png_bytes(size=(128, 96)):
    from io import BytesIO
    stream = BytesIO()
    Image.new("RGB", size, "white").save(stream, format="PNG")
    return stream.getvalue()


def request_for(raw=None, **changes):
    raw = raw or png_bytes()
    fields = {
        "image_data": "data:image/png;base64," + base64.b64encode(raw).decode("ascii"),
        "capture_date": "2026-11-14",
        "body_site": "left forearm",
        "uv_context": "UNKNOWN",
    }
    fields.update(changes)
    return SkinGuardRequest(**fields)


def test_no_configured_model_never_emits_synthetic_findings(tmp_path):
    service = SkinGuardService(model_directory=tmp_path)
    assert service.status()["state"] == "MODEL_NOT_CONFIGURED"
    result = service.analyze(request_for())
    assert result["analysis_performed"] is False
    assert result["detections"] == []
    assert result["diagnosis"] is None
    assert "No AI analysis was performed" in result["message"]
    assert "image_data" not in result
    assert result["quality_checks"]["method"].startswith("simple image-wide brightness heuristic")


@pytest.mark.parametrize("data_url", [
    "data:image/gif;base64,R0lGODlhAQABAAAAACw=",
    "data:image/jpeg;base64,not-base64!",
])
def test_rejects_unsupported_or_malformed_image_payload(data_url):
    with pytest.raises((ValueError, SkinGuardInputError)):
        decode_image_data_url(data_url)


def test_rejects_declared_format_that_does_not_match_image_bytes(tmp_path):
    request = request_for()
    request = request.model_copy(update={
        "image_data": "data:image/jpeg;base64," + base64.b64encode(png_bytes()).decode("ascii")
    })
    with pytest.raises(SkinGuardInputError, match="IMAGE_FORMAT_MISMATCH"):
        SkinGuardService(model_directory=tmp_path).analyze(request)


def test_rejects_small_images(tmp_path):
    service = SkinGuardService(model_directory=tmp_path)
    with pytest.raises(SkinGuardInputError, match="IMAGE_TOO_SMALL"):
        service.analyze(request_for(png_bytes((32, 32))))


def test_rejects_unsafe_detector_output():
    with pytest.raises(ValueError):
        validate_detections([{"label": "melanoma", "score": 0.9, "box_xyxy_normalized": [0, 0, 1, 1]}])
    with pytest.raises(ValueError):
        validate_detections([{"label": "skin_lesion_candidate", "score": 0.9, "box_xyxy_normalized": [0.8, 0.2, 0.1, 0.9]}])


def test_accepts_multiple_candidate_regions_without_diagnosing_them():
    found = validate_detections([
        {"label": "skin_lesion_candidate", "score": 0.7, "box_xyxy_normalized": [0.1, 0.1, 0.2, 0.2]},
        {"label": "skin_lesion_candidate", "score": 0.8, "box_xyxy_normalized": [0.5, 0.4, 0.7, 0.6]},
    ])
    assert len(found) == 2
    assert all(row["label"] == "skin_lesion_candidate" for row in found)


def valid_model_manifest():
    return {
        "schema_version": 1,
        "review_status": "RESEARCH_REVIEWED",
        "model_id": "test-detector-v1",
        "task": "SKIN_LESION_LOCALIZATION",
        "input_modality": "TOTAL_BODY_PHOTOGRAPH",
        "license": {"code": "reviewed", "weights": "reviewed", "training_data": "reviewed", "reviewed": True},
        "source_url": "https://example.org/model",
        "training_data": {
            "name": "synthetic-test", "version": "1", "source": "https://example.org/data",
            "license": "synthetic", "subject_split_method": "subject-wise",
            "manifest_sha256": "a" * 64, "content_snapshot_sha256": "b" * 64,
        },
        "evaluation": {
            "dataset": "synthetic-test 1", "split": "SUBJECT_LEVEL_HELD_OUT",
            "metrics_report": "evaluation.json", "metrics_report_sha256": "c" * 64,
        },
        "weights_sha256": "d" * 64,
        "input": {"width": 640, "height": 640, "layout": "NCHW_RGB_FLOAT_0_1", "resize": "LETTERBOX_114"},
        "output": {
            "tensor_name": "detections", "layout": "XYXY_SCORE_CLASS_INPUT_PIXELS",
            "labels": ["skin_lesion_candidate"], "score_threshold": 0.25,
        },
    }


def test_model_manifest_requires_review_and_hash_provenance():
    manifest = valid_model_manifest()
    validate_model_manifest(manifest)
    manifest["review_status"] = "NOT_REVIEWED"
    with pytest.raises(ValueError, match="MODEL_NOT_REVIEWED_FOR_RESEARCH_USE"):
        validate_model_manifest(manifest)


def test_model_loader_checks_hashed_heldout_report(tmp_path):
    manifest = valid_model_manifest()
    (tmp_path / "model.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "model.onnx").write_bytes(b"local-test-weight")
    (tmp_path / "evaluation.json").write_text(json.dumps({
        "task": "SKIN_LESION_LOCALIZATION", "split": "SUBJECT_LEVEL_HELD_OUT",
        "dataset": "synthetic-test 1", "clinical_validation": False,
    }), encoding="utf-8")
    detector, state = load_local_detector(tmp_path)
    assert detector is None and state == "MODEL_EVALUATION_HASH_MISMATCH"


def make_dataset(root: Path):
    rows = []
    for split, subject in (("train", "subj-a"), ("validation", "subj-b"), ("test", "subj-c")):
        image_path = root / "images" / f"{split}.png"
        annotation_path = root / "annotations" / f"{split}.json"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        annotation_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (80, 80), "white").save(image_path)
        annotation_path.write_text(json.dumps({"boxes": [{
            "label": "skin_lesion_candidate",
            "box_xyxy_normalized": [0.1, 0.1, 0.5, 0.5],
        }]}), encoding="utf-8")
        rows.append({"image": image_path.relative_to(root).as_posix(), "annotation": annotation_path.relative_to(root).as_posix(), "subject_id": subject, "split": split})
    manifest = {
        "schema_version": 1,
        "dataset": {"name": "synthetic-unit-fixture", "version": "1", "source": "unit-test", "license": "synthetic", "access_confirmed": True},
        "records": rows,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, manifest


def test_dataset_manifest_checks_subject_level_splits_and_boxes(tmp_path):
    path, _ = make_dataset(tmp_path)
    result = validate_dataset_manifest(path)
    assert result["state"] == "DATASET_MANIFEST_VALID"
    assert result["records"] == 3
    assert result["subject_overlap"] is False
    assert result["images_copied_or_modified"] is False


def test_yolo_preparation_converts_boxes_and_copies_source_data(tmp_path):
    manifest_path, _ = make_dataset(tmp_path / "licensed-data")
    source_before = (tmp_path / "licensed-data" / "annotations" / "train.json").read_bytes()
    yaml_path, _, snapshot_hash = prepare_yolo_dataset(manifest_path, tmp_path / "prepared")
    train_label = (tmp_path / "prepared" / "labels" / "train" / "00000000.txt").read_text(encoding="utf-8")
    assert train_label == "0 0.30000000 0.30000000 0.40000000 0.40000000"
    assert "test: images/test" in yaml_path.read_text(encoding="utf-8")
    assert len(snapshot_hash) == 64
    assert (tmp_path / "licensed-data" / "annotations" / "train.json").read_bytes() == source_before


def test_dataset_manifest_rejects_subject_leakage(tmp_path):
    path, manifest = make_dataset(tmp_path)
    manifest["records"][1]["subject_id"] = manifest["records"][0]["subject_id"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="SUBJECT_LEAKAGE_ACROSS_SPLITS"):
        validate_dataset_manifest(path)


def test_dataset_manifest_rejects_paths_outside_root(tmp_path):
    path, manifest = make_dataset(tmp_path)
    manifest["records"][0]["image"] = "../outside.png"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="DATASET_PATH_ESCAPES_ROOT"):
        validate_dataset_manifest(path)
