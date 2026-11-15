import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

import pytest
from PIL import Image

from vigile.skinguard import (
    SkinGuardInputError,
    SkinGuardRequest,
    SkinGuardService,
    OnnxSkinDetector,
    assess_lighting,
    decode_image_data_url,
    load_local_detector,
    validate_detections,
    validate_model_manifest,
    MAX_UPLOAD_BYTES,
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


@pytest.mark.parametrize(
    ("color", "expected"),
    [((0, 0, 0), "POSSIBLY_TOO_DARK"), ((120, 120, 120), "NO_COARSE_BRIGHTNESS_WARNING"), ((255, 255, 255), "POSSIBLY_TOO_BRIGHT_OR_CLIPPED")],
)
def test_lighting_heuristic_labels_are_explicitly_coarse(color, expected):
    assert assess_lighting(Image.new("RGB", (80, 80), color))["state"] == expected


def test_detector_service_returns_only_validated_candidate_localizations():
    class Detector:
        model_id = "test-detector"

        def detect(self, image):
            assert image.mode == "RGB"
            return [{"label": "skin_lesion_candidate", "score": 0.91, "box_xyxy_normalized": [0.1, 0.2, 0.4, 0.6]}]

    result = SkinGuardService(detector=Detector()).analyze(request_for())
    assert result["analysis_performed"] is True
    assert result["model_id"] == "test-detector"
    assert result["detections"][0]["score"] == 0.91
    assert result["diagnosis"] is None
    assert result["radiation_causation"] is None


def test_detector_service_rejects_malformed_inference_output():
    class Detector:
        model_id = "bad-test-detector"

        def detect(self, image):
            return [{"label": "melanoma", "score": 0.99, "box_xyxy_normalized": [0, 0, 1, 1]}]

    with pytest.raises(ValueError, match="MODEL_OUTPUT_INVALID"):
        SkinGuardService(detector=Detector()).analyze(request_for())


@pytest.mark.parametrize("layout", ["XYXY_SCORE_CLASS_INPUT_PIXELS", "XYXY_SCORE_CLASS_NORMALIZED"])
def test_onnx_adapter_letterboxes_and_maps_predictions_back_to_source(layout, tmp_path):
    import numpy as np

    class Session:
        def get_inputs(self):
            return [type("Input", (), {"name": "images", "shape": [1, 3, 640, 640]})()]

        def get_outputs(self):
            return [type("Output", (), {"name": "detections"})()]

        def run(self, output_names, feed):
            assert output_names == ["detections"]
            tensor = feed["images"]
            assert tensor.shape == (1, 3, 640, 640)
            assert tensor.dtype == np.float32
            assert 0 <= float(tensor.min()) <= float(tensor.max()) <= 1
            if layout == "XYXY_SCORE_CLASS_NORMALIZED":
                row = [0.0, 0.25, 1.0, 0.75, 0.9, 0]
            else:
                row = [0.0, 160.0, 640.0, 480.0, 0.9, 0]
            return [np.asarray([[row, [0, 0, 1, 1, 0.1, 0], [0, 0, 1, 1, 0.9, 1]]], dtype=np.float32)]

    class Runtime:
        class InferenceSession:
            def __new__(cls, *_args, **_kwargs):
                return Session()

    manifest = valid_model_manifest()
    manifest["input"].update({"width": 640, "height": 640})
    manifest["output"]["layout"] = layout
    detector = OnnxSkinDetector(manifest, tmp_path / "fake.onnx", np, Runtime)
    found = detector.detect(Image.new("RGB", (128, 64), (30, 60, 90)))
    assert len(found) == 1
    assert found[0]["score"] == pytest.approx(0.9)
    assert found[0]["box_xyxy_normalized"] == pytest.approx([0, 0, 1, 1])


def test_onnx_adapter_rejects_incompatible_tensor_shape(tmp_path):
    import numpy as np

    class Session:
        def get_inputs(self):
            return [type("Input", (), {"name": "images", "shape": [1, 3, 320, 320]})()]

        def get_outputs(self):
            return [type("Output", (), {"name": "detections"})()]

    class Runtime:
        class InferenceSession:
            def __new__(cls, *_args, **_kwargs):
                return Session()

    with pytest.raises(ValueError, match="MODEL_INPUT_SHAPE_MISMATCH"):
        OnnxSkinDetector(valid_model_manifest(), tmp_path / "fake.onnx", np, Runtime)


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


def test_request_rejects_bad_data_url_and_future_longitudinal_date():
    with pytest.raises(ValueError, match="SUPPORTED_IMAGE_DATA_URL_REQUIRED"):
        SkinGuardRequest(image_data="data:image/bmp;base64," + "A" * 64, capture_date="2026-11-14", body_site="arm")
    with pytest.raises(ValueError, match="EARLIER_PHOTO_DATE_AFTER_CURRENT_PHOTO"):
        request_for(earlier_photo_date="2026-11-15")


def test_image_decode_rejects_corrupt_and_oversized_dimensions(tmp_path):
    with pytest.raises(SkinGuardInputError, match="INVALID_OR_UNSAFE_IMAGE"):
        SkinGuardService(tmp_path).analyze(request_for(b"not a valid image payload" * 4))
    image = Image.new("RGB", (8193, 64), "white")
    from io import BytesIO
    stream = BytesIO()
    image.save(stream, format="PNG")
    with pytest.raises(SkinGuardInputError, match="IMAGE_DIMENSIONS_EXCEED_LIMIT"):
        SkinGuardService(tmp_path).analyze(request_for(stream.getvalue()))


def test_service_enforces_upload_size_after_decode(monkeypatch, tmp_path):
    import vigile.skinguard as module
    oversized_valid_prefix = png_bytes() + b"x" * (MAX_UPLOAD_BYTES + 1)
    monkeypatch.setattr(module, "decode_image_data_url", lambda _value: ("image/png", oversized_valid_prefix))
    with pytest.raises(SkinGuardInputError, match="IMAGE_TOO_LARGE") as error:
        SkinGuardService(tmp_path).analyze(request_for())
    assert error.value.status_code == 413


def write_valid_model_bundle(folder: Path, *, report_override=None, weights=b"valid-test-weights"):
    folder.mkdir(parents=True, exist_ok=True)
    report = report_override or {
        "task": "SKIN_LESION_LOCALIZATION", "split": "SUBJECT_LEVEL_HELD_OUT",
        "dataset": "synthetic-test 1", "clinical_validation": False,
    }
    report_bytes = json.dumps(report).encode("utf-8")
    manifest = valid_model_manifest()
    manifest["weights_sha256"] = hashlib.sha256(weights).hexdigest()
    manifest["evaluation"]["metrics_report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    (folder / "model.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "evaluation.json").write_bytes(report_bytes)
    (folder / "model.onnx").write_bytes(weights)
    return manifest


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("remove_required", "INCOMPLETE_MODEL_MANIFEST"),
        ("schema", "MODEL_NOT_REVIEWED_FOR_RESEARCH_USE"),
        ("task", "MODEL_TASK_OR_MODALITY_NOT_SUPPORTED"),
        ("provenance", "MODEL_PROVENANCE_REQUIRED"),
        ("weight_hash", "MODEL_SHA256_REQUIRED"),
        ("license", "MODEL_AND_DATA_LICENSES_REQUIRED"),
        ("license_review", "LICENSE_REVIEW_REQUIRED"),
        ("training", "TRAINING_DATA_PROVENANCE_REQUIRED"),
        ("training_hash", "TRAINING_DATA_HASHES_REQUIRED"),
        ("evaluation", "EVALUATION_PROVENANCE_REQUIRED"),
        ("evaluation_hash", "HELD_OUT_METRICS_REPORT_HASH_REQUIRED"),
        ("split", "SUBJECT_LEVEL_HELD_OUT_EVALUATION_REQUIRED"),
        ("input", "UNSUPPORTED_MODEL_INPUT_CONTRACT"),
        ("output", "UNSUPPORTED_MODEL_OUTPUT_CONTRACT"),
        ("labels", "UNSUPPORTED_DETECTION_LABELS"),
        ("threshold", "INVALID_SCORE_THRESHOLD"),
    ],
)
def test_model_manifest_rejects_each_untrusted_contract(mutation, message):
    manifest = copy.deepcopy(valid_model_manifest())
    if mutation == "remove_required":
        del manifest["source_url"]
    elif mutation == "schema":
        manifest["schema_version"] = 2
    elif mutation == "task":
        manifest["task"] = "CLASSIFICATION"
    elif mutation == "provenance":
        manifest["source_url"] = "http://untrusted.example"
    elif mutation == "weight_hash":
        manifest["weights_sha256"] = "not-a-hash"
    elif mutation == "license":
        manifest["license"] = {"code": "MIT"}
    elif mutation == "license_review":
        manifest["license"]["reviewed"] = False
    elif mutation == "training":
        manifest["training_data"] = {"name": "test"}
    elif mutation == "training_hash":
        manifest["training_data"]["manifest_sha256"] = "bad"
    elif mutation == "evaluation":
        manifest["evaluation"] = {"dataset": "test"}
    elif mutation == "evaluation_hash":
        manifest["evaluation"]["metrics_report_sha256"] = "bad"
    elif mutation == "split":
        manifest["evaluation"]["split"] = "RANDOM_IMAGE_SPLIT"
    elif mutation == "input":
        manifest["input"]["resize"] = "STRETCH"
    elif mutation == "output":
        manifest["output"]["layout"] = "UNSUPPORTED"
    elif mutation == "labels":
        manifest["output"]["labels"] = ["melanoma"]
    elif mutation == "threshold":
        manifest["output"]["score_threshold"] = 1.5
    with pytest.raises(ValueError, match=message):
        validate_model_manifest(manifest)


@pytest.mark.parametrize(
    ("report", "expected_state"),
    [
        ({"task": "WRONG", "split": "SUBJECT_LEVEL_HELD_OUT", "dataset": "synthetic-test 1", "clinical_validation": False}, "MODEL_EVALUATION_REPORT_INVALID"),
        ({"task": "SKIN_LESION_LOCALIZATION", "split": "SUBJECT_LEVEL_HELD_OUT", "dataset": "synthetic-test 1", "clinical_validation": True}, "MODEL_EVALUATION_REPORT_INVALID"),
    ],
)
def test_model_loader_rejects_inconsistent_or_clinical_claim_report(tmp_path, report, expected_state):
    write_valid_model_bundle(tmp_path, report_override=report)
    detector, state = load_local_detector(tmp_path)
    assert detector is None and state == expected_state


def test_model_loader_rejects_weight_hash_mismatch(tmp_path):
    write_valid_model_bundle(tmp_path)
    (tmp_path / "model.onnx").write_bytes(b"changed after manifest review")
    detector, state = load_local_detector(tmp_path)
    assert detector is None and state == "MODEL_HASH_MISMATCH"


def test_model_loader_reports_missing_onnx_runtime_without_failing_portal(tmp_path, monkeypatch):
    write_valid_model_bundle(tmp_path)
    monkeypatch.setitem(sys.modules, "onnxruntime", None)
    detector, state = load_local_detector(tmp_path)
    assert detector is None and state == "OPTIONAL_ONNX_RUNTIME_NOT_INSTALLED"


def test_model_loader_accepts_hashed_bundle_and_builds_onnx_detector(tmp_path, monkeypatch):
    import numpy as np

    class Session:
        def get_inputs(self):
            return [type("Input", (), {"name": "images", "shape": [1, 3, 640, 640]})()]

        def get_outputs(self):
            return [type("Output", (), {"name": "detections"})()]

        def run(self, *_args, **_kwargs):
            return [np.empty((0, 6), dtype=np.float32)]

    runtime = types.ModuleType("onnxruntime")
    runtime.InferenceSession = lambda *_args, **_kwargs: Session()
    monkeypatch.setitem(sys.modules, "onnxruntime", runtime)
    write_valid_model_bundle(tmp_path)
    detector, state = load_local_detector(tmp_path)
    assert state == "READY"
    assert detector is not None and detector.model_id == "test-detector-v1"
    assert detector.detect(Image.new("RGB", (80, 60), "white")) == []


def test_lighting_clipped_fraction_warning_and_detection_validation_edges():
    pixels = Image.new("L", (100, 100), 120)
    for x in range(40):
        for y in range(100):
            pixels.putpixel((x, y), 255)
    assert assess_lighting(pixels)["state"] == "POSSIBLY_TOO_BRIGHT_OR_CLIPPED"
    bad_rows = [
        None,
        {"label": "skin_lesion_candidate", "score": float("nan"), "box_xyxy_normalized": [0, 0, 1, 1]},
        {"label": "skin_lesion_candidate", "score": 0.7, "box_xyxy_normalized": [0, 0, 1]},
        {"label": "skin_lesion_candidate", "score": 0.7, "box_xyxy_normalized": [0.5, 0.5, 0.5, 0.9]},
    ]
    for row in bad_rows:
        with pytest.raises(ValueError, match="MODEL_OUTPUT_INVALID"):
            validate_detections([row])
    with pytest.raises(ValueError, match="MODEL_OUTPUT_INVALID"):
        validate_detections([{"label": "skin_lesion_candidate", "score": 0.7, "box_xyxy_normalized": [0, 0, 1, 1]}] * 501)


@pytest.mark.parametrize("case", ["wrong_shape", "too_many", "invalid_rows"])
def test_onnx_detector_skips_corrupt_rows_and_rejects_output_shape(tmp_path, case):
    import numpy as np

    if case == "wrong_shape":
        rows = np.array([1, 2, 3])
    elif case == "too_many":
        rows = np.ones((10001, 6), dtype=np.float32)
    else:
        rows = np.array([[0, 80, 640, 560, 0.9, 0], [float("nan"), 0, 1, 1, 0.9, 0], [0.5, 0.2, 0.4, 0.9, 0.9, 0]], dtype=np.float32)

    class Session:
        def get_inputs(self):
            return [type("Input", (), {"name": "images", "shape": [1, 3, 640, 640]})()]

        def get_outputs(self):
            return [type("Output", (), {"name": "detections"})()]

        def run(self, *_args, **_kwargs):
            return [rows]

    class Runtime:
        InferenceSession = lambda *_args, **_kwargs: Session()

    detector = OnnxSkinDetector(valid_model_manifest(), tmp_path / "model.onnx", np, Runtime)
    if case in {"wrong_shape", "too_many"}:
        with pytest.raises(ValueError, match="MODEL_OUTPUT_SHAPE_INVALID"):
            detector.detect(Image.new("RGB", (80, 60), "white"))
    else:
        found = detector.detect(Image.new("RGB", (80, 60), "white"))
        assert len(found) == 1
        assert found[0]["label"] == "skin_lesion_candidate"
        assert found[0]["score"] == pytest.approx(0.9)
        assert found[0]["box_xyxy_normalized"] == pytest.approx([0.0, 0.0, 1.0, 1.0])


def test_data_url_rejects_payload_over_byte_limit():
    encoded = base64.b64encode(b"x" * (MAX_UPLOAD_BYTES + 1)).decode("ascii")
    with pytest.raises(SkinGuardInputError, match="IMAGE_TOO_LARGE"):
        decode_image_data_url("data:image/png;base64," + encoded)
    encoded_beyond_encoded_limit = "A" * (((MAX_UPLOAD_BYTES + 2) // 3) * 4 + 1)
    with pytest.raises(SkinGuardInputError, match="IMAGE_TOO_LARGE"):
        decode_image_data_url("data:image/png;base64," + encoded_beyond_encoded_limit)
    with pytest.raises(SkinGuardInputError, match="INVALID_BASE64_IMAGE"):
        decode_image_data_url("data:image/png;base64," + "A" * 65)


def test_local_detector_reports_corrupt_manifest_and_tensor_name_mismatch(tmp_path):
    (tmp_path / "model.manifest.json").write_text("{broken", encoding="utf-8")
    (tmp_path / "model.onnx").write_bytes(b"weights")
    detector, state = load_local_detector(tmp_path)
    assert detector is None and state == "MODEL_MANIFEST_INVALID"

    class Session:
        def get_inputs(self):
            return [type("Input", (), {"name": "images", "shape": [1, 3, 640, 640]})()]

        def get_outputs(self):
            return [type("Output", (), {"name": "wrong-name"})()]

    class Runtime:
        InferenceSession = lambda *_args, **_kwargs: Session()

    with pytest.raises(ValueError, match="MODEL_TENSOR_CONTRACT_MISMATCH"):
        OnnxSkinDetector(valid_model_manifest(), tmp_path / "fake.onnx", __import__("numpy"), Runtime)
