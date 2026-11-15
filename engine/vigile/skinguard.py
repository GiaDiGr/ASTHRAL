"""Local SkinGuard intake and explicitly gated lesion-localization adapter.

This module does not diagnose skin disease or infer radiation causation. No
model is bundled; inference is enabled only for a locally supplied ONNX
detector whose hash and research provenance pass the manifest checks below.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import re
import warnings
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal, Protocol
import uuid

from PIL import Image, UnidentifiedImageError
from pydantic import Field, field_validator, model_validator

from .models import Model

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_IMAGE_SIDE = 8192
MAX_DATA_URL_CHARS = 14_000_100
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
MODEL_DIRECTORY = Path(__file__).resolve().parents[1] / "local_ai" / "skinguard"


class SkinGuardRequest(Model):
    image_data: str = Field(min_length=64, max_length=MAX_DATA_URL_CHARS)
    capture_date: date
    body_site: str = Field(min_length=2, max_length=80)
    case_reference: str | None = Field(default=None, max_length=80)
    earlier_photo_date: date | None = None
    user_observation: str = Field(default="", max_length=800)
    uv_context: Literal["UNKNOWN", "NONE_REPORTED", "OCCASIONAL", "FREQUENT"] = "UNKNOWN"

    @field_validator("body_site", "case_reference", "user_observation", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("image_data")
    @classmethod
    def valid_data_url_shape(cls, value):
        if not re.match(r"^data:image/(?:jpeg|png|webp);base64,", value):
            raise ValueError("SUPPORTED_IMAGE_DATA_URL_REQUIRED")
        return value

    @model_validator(mode="after")
    def earlier_date_precedes_capture(self):
        if self.earlier_photo_date and self.earlier_photo_date > self.capture_date:
            raise ValueError("EARLIER_PHOTO_DATE_AFTER_CURRENT_PHOTO")
        return self


class SkinDetector(Protocol):
    model_id: str

    def detect(self, image: Image.Image) -> list[dict]: ...


class SkinGuardInputError(ValueError):
    def __init__(self, code: str, status_code: int = 422):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class SkinGuardService:
    def __init__(self, model_directory: Path = MODEL_DIRECTORY, detector: SkinDetector | None = None):
        self.model_directory = Path(model_directory)
        self.detector = detector
        self.model_state = "MODEL_NOT_CONFIGURED"
        if detector is None:
            self.detector, self.model_state = load_local_detector(self.model_directory)

    def status(self) -> dict:
        return {
            "module": "ASTHRAL SkinGuard",
            "state": "READY" if self.detector else self.model_state,
            "analysis_available": self.detector is not None,
            "model_id": self.detector.model_id if self.detector else None,
            "task": "SKIN_LESION_LOCALIZATION" if self.detector else None,
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "max_image_pixels": MAX_IMAGE_PIXELS,
            "accepted_formats": ["JPEG", "PNG", "WEBP"],
            "image_retention": "IN_MEMORY_ONLY; not written to disk or database",
            "clinical_scope": "Research prototype; no diagnosis or radiation-cause inference",
        }

    def analyze(self, request: SkinGuardRequest) -> dict:
        mime, raw = decode_image_data_url(request.image_data)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            try:
                with Image.open(io.BytesIO(raw)) as source:
                    actual_format = source.format
                    width, height = source.size
                    if actual_format not in ALLOWED_FORMATS or ALLOWED_FORMATS[actual_format] != mime:
                        raise SkinGuardInputError("IMAGE_FORMAT_MISMATCH")
                    if width < 64 or height < 64:
                        raise SkinGuardInputError("IMAGE_TOO_SMALL")
                    if width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE or width * height > MAX_IMAGE_PIXELS:
                        raise SkinGuardInputError("IMAGE_DIMENSIONS_EXCEED_LIMIT")
                    source.verify()
                with Image.open(io.BytesIO(raw)) as source:
                    source.load()
                    image = source.convert("RGB")
            except SkinGuardInputError:
                raise
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
                    Image.DecompressionBombWarning) as exc:
                raise SkinGuardInputError("INVALID_OR_UNSAFE_IMAGE") from exc
        if len(raw) > MAX_UPLOAD_BYTES:
            raise SkinGuardInputError("IMAGE_TOO_LARGE", 413)

        base = {
            "analysis_id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "capture_date": request.capture_date.isoformat(),
            "body_site": request.body_site,
            "case_reference": request.case_reference or None,
            "earlier_photo_date": request.earlier_photo_date.isoformat() if request.earlier_photo_date else None,
            "user_observation": request.user_observation,
            "uv_context": request.uv_context,
            "image": {"format": actual_format, "width": width, "height": height},
            "quality_checks": assess_lighting(image),
            "detections": [],
            "diagnosis": None,
            "radiation_causation": None,
            "limitations": [
                "A photograph cannot establish the cause of a skin finding.",
                "Ultraviolet (UV) exposure is non-ionizing and is distinct from ionizing space radiation.",
                "A photo comparison is not performed by this service unless a verified detector is configured.",
                "This research prototype does not provide diagnosis or treatment advice.",
            ],
        }
        if self.detector is None:
            image.close()
            return {
                **base,
                "state": self.model_state,
                "analysis_performed": False,
                "message": "No AI analysis was performed. No model is configured; no boxes, scores, or predictions were generated.",
            }
        try:
            detections = validate_detections(self.detector.detect(image))
        finally:
            image.close()
        return {
            **base,
            "state": "MODEL_ANALYSIS_COMPLETED",
            "analysis_performed": True,
            "message": "Research-only localization results. These are not diagnoses or calibrated probabilities.",
            "model_id": self.detector.model_id,
            "detections": detections,
        }


def decode_image_data_url(data_url: str) -> tuple[str, bytes]:
    match = re.match(r"^data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$", data_url)
    if not match:
        raise SkinGuardInputError("SUPPORTED_IMAGE_DATA_URL_REQUIRED")
    mime, encoded = match.groups()
    if len(encoded) > ((MAX_UPLOAD_BYTES + 2) // 3) * 4:
        raise SkinGuardInputError("IMAGE_TOO_LARGE", 413)
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise SkinGuardInputError("INVALID_BASE64_IMAGE") from exc
    if len(raw) > MAX_UPLOAD_BYTES:
        raise SkinGuardInputError("IMAGE_TOO_LARGE", 413)
    return mime, raw


def load_local_detector(folder: Path) -> tuple[SkinDetector | None, str]:
    """Load a hash-checked, provenance-documented ONNX localization model."""
    manifest_path, weights_path = folder / "model.manifest.json", folder / "model.onnx"
    if not manifest_path.is_file() or not weights_path.is_file():
        return None, "MODEL_NOT_CONFIGURED"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_model_manifest(manifest)
        evaluation = manifest["evaluation"]
        report_path = folder / "evaluation.json"
        report_bytes = report_path.read_bytes()
        if hashlib.sha256(report_bytes).hexdigest() != evaluation["metrics_report_sha256"].lower():
            return None, "MODEL_EVALUATION_HASH_MISMATCH"
        report = json.loads(report_bytes)
        if report.get("task") != "SKIN_LESION_LOCALIZATION" or report.get("split") != evaluation["split"] or report.get("dataset") != evaluation["dataset"] or report.get("clinical_validation") is not False:
            return None, "MODEL_EVALUATION_REPORT_INVALID"
        weights = weights_path.read_bytes()
        if hashlib.sha256(weights).hexdigest() != manifest["weights_sha256"].lower():
            return None, "MODEL_HASH_MISMATCH"
        try:
            import numpy as np
            import onnxruntime as ort
        except ImportError:
            return None, "OPTIONAL_ONNX_RUNTIME_NOT_INSTALLED"
        return OnnxSkinDetector(manifest, weights_path, np, ort), "READY"
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, AttributeError, json.JSONDecodeError):
        return None, "MODEL_MANIFEST_INVALID"


def validate_model_manifest(manifest: dict) -> None:
    required = {
        "schema_version", "review_status", "model_id", "task", "input_modality", "license",
        "source_url", "training_data", "evaluation", "weights_sha256", "input", "output",
    }
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise ValueError("INCOMPLETE_MODEL_MANIFEST")
    if manifest["schema_version"] != 1 or manifest["review_status"] != "RESEARCH_REVIEWED":
        raise ValueError("MODEL_NOT_REVIEWED_FOR_RESEARCH_USE")
    if manifest["task"] != "SKIN_LESION_LOCALIZATION" or manifest["input_modality"] != "TOTAL_BODY_PHOTOGRAPH":
        raise ValueError("MODEL_TASK_OR_MODALITY_NOT_SUPPORTED")
    if not isinstance(manifest["model_id"], str) or not manifest["model_id"].strip() or len(manifest["model_id"]) > 120 or not isinstance(manifest["source_url"], str) or len(manifest["source_url"]) > 2048 or not manifest["source_url"].startswith("https://"):
        raise ValueError("MODEL_PROVENANCE_REQUIRED")
    if not isinstance(manifest["weights_sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", manifest["weights_sha256"]):
        raise ValueError("MODEL_SHA256_REQUIRED")
    license_info, training, evaluation = manifest["license"], manifest["training_data"], manifest["evaluation"]
    if not isinstance(license_info, dict) or not all(str(license_info.get(k, "")).strip() for k in ("code", "weights", "training_data")):
        raise ValueError("MODEL_AND_DATA_LICENSES_REQUIRED")
    if license_info.get("reviewed") is not True:
        raise ValueError("LICENSE_REVIEW_REQUIRED")
    if not isinstance(training, dict) or not all(str(training.get(k, "")).strip() for k in ("name", "version", "source", "license", "subject_split_method")):
        raise ValueError("TRAINING_DATA_PROVENANCE_REQUIRED")
    if any(not isinstance(training.get(k), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", training[k]) for k in ("manifest_sha256", "content_snapshot_sha256")):
        raise ValueError("TRAINING_DATA_HASHES_REQUIRED")
    if not isinstance(evaluation, dict) or not all(str(evaluation.get(k, "")).strip() for k in ("dataset", "split", "metrics_report")):
        raise ValueError("EVALUATION_PROVENANCE_REQUIRED")
    if evaluation.get("metrics_report") != "evaluation.json" or not isinstance(evaluation.get("metrics_report_sha256"), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", evaluation["metrics_report_sha256"]):
        raise ValueError("HELD_OUT_METRICS_REPORT_HASH_REQUIRED")
    if evaluation["split"] not in ("SUBJECT_LEVEL_HELD_OUT", "PATIENT_LEVEL_HELD_OUT"):
        raise ValueError("SUBJECT_LEVEL_HELD_OUT_EVALUATION_REQUIRED")
    inp, out = manifest["input"], manifest["output"]
    if not isinstance(inp, dict) or inp.get("layout") != "NCHW_RGB_FLOAT_0_1" or inp.get("resize") != "LETTERBOX_114" or not all(isinstance(inp.get(k), int) and 64 <= inp[k] <= 2048 for k in ("width", "height")):
        raise ValueError("UNSUPPORTED_MODEL_INPUT_CONTRACT")
    if not isinstance(out, dict) or out.get("layout") not in ("XYXY_SCORE_CLASS_NORMALIZED", "XYXY_SCORE_CLASS_INPUT_PIXELS") or not isinstance(out.get("tensor_name"), str):
        raise ValueError("UNSUPPORTED_MODEL_OUTPUT_CONTRACT")
    if out.get("labels") != ["skin_lesion_candidate"]:
        raise ValueError("UNSUPPORTED_DETECTION_LABELS")
    threshold = out.get("score_threshold")
    if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
        raise ValueError("INVALID_SCORE_THRESHOLD")


class OnnxSkinDetector:
    def __init__(self, manifest: dict, weights_path: Path, np, ort):
        self.manifest = manifest
        self.model_id = manifest["model_id"]
        self.np = np
        self.session = ort.InferenceSession(str(weights_path), providers=["CPUExecutionProvider"])
        inputs = self.session.get_inputs()
        if len(inputs) != 1 or manifest["output"]["tensor_name"] not in {row.name for row in self.session.get_outputs()}:
            raise ValueError("MODEL_TENSOR_CONTRACT_MISMATCH")
        self.input_name = inputs[0].name
        shape = inputs[0].shape
        expected = [1, 3, manifest["input"]["height"], manifest["input"]["width"]]
        if len(shape) != 4 or any(isinstance(actual, int) and actual != target for actual, target in zip(shape, expected)):
            raise ValueError("MODEL_INPUT_SHAPE_MISMATCH")

    def detect(self, image: Image.Image) -> list[dict]:
        np, contract = self.np, self.manifest
        width, height = contract["input"]["width"], contract["input"]["height"]
        original_width, original_height = image.size
        ratio = min(width / original_width, height / original_height)
        resized_width = max(1, round(original_width * ratio))
        resized_height = max(1, round(original_height * ratio))
        left, top = (width - resized_width) // 2, (height - resized_height) // 2
        resized = image.resize((resized_width, resized_height), Image.Resampling.BILINEAR)
        padded = Image.new("RGB", (width, height), (114, 114, 114))
        padded.paste(resized, (left, top))
        tensor = np.asarray(padded, dtype=np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))[None, ...]
        rows = np.asarray(self.session.run([contract["output"]["tensor_name"]], {self.input_name: tensor})[0])
        if rows.ndim == 3 and rows.shape[0] == 1:
            rows = rows[0]
        if rows.ndim != 2 or rows.shape[1] != 6 or rows.shape[0] > 10000:
            raise ValueError("MODEL_OUTPUT_SHAPE_INVALID")
        threshold = float(contract["output"]["score_threshold"])
        found = []
        for x1, y1, x2, y2, score, class_id in rows.tolist():
            vals = (x1, y1, x2, y2, score, class_id)
            if not all(math.isfinite(float(v)) for v in vals):
                continue
            if int(class_id) != 0 or float(class_id) != 0 or not threshold <= score <= 1:
                continue
            if contract["output"]["layout"] == "XYXY_SCORE_CLASS_NORMALIZED":
                x1, x2, y1, y2 = x1 * width, x2 * width, y1 * height, y2 * height
            x1, x2 = (x1 - left) / resized_width, (x2 - left) / resized_width
            y1, y2 = (y1 - top) / resized_height, (y2 - top) / resized_height
            x1, x2, y1, y2 = (max(0.0, min(1.0, value)) for value in (x1, x2, y1, y2))
            if x2 <= x1 or y2 <= y1:
                continue
            found.append({"label": "skin_lesion_candidate", "score": float(score), "box_xyxy_normalized": [float(x1), float(y1), float(x2), float(y2)]})
        return found


def assess_lighting(image: Image.Image) -> dict:
    """A coarse brightness heuristic, not an image adequacy or diagnostic test."""
    preview = image.convert("L")
    preview.thumbnail((512, 512), Image.Resampling.BILINEAR)
    values = preview.tobytes()
    mean = sum(values) / max(1, len(values))
    clipped = sum(value <= 8 or value >= 247 for value in values) / max(1, len(values))
    if mean < 40:
        state = "POSSIBLY_TOO_DARK"
    elif mean > 215 or clipped > 0.35:
        state = "POSSIBLY_TOO_BRIGHT_OR_CLIPPED"
    else:
        state = "NO_COARSE_BRIGHTNESS_WARNING"
    return {
        "state": state,
        "mean_luminance_0_255": round(mean, 1),
        "clipped_pixel_fraction": round(clipped, 3),
        "method": "simple image-wide brightness heuristic; not validated for skin-photo adequacy",
    }


def validate_detections(detections: list[dict]) -> list[dict]:
    if not isinstance(detections, list) or len(detections) > 500:
        raise ValueError("MODEL_OUTPUT_INVALID")
    safe = []
    for detection in detections:
        if not isinstance(detection, dict) or detection.get("label") != "skin_lesion_candidate":
            raise ValueError("MODEL_OUTPUT_INVALID")
        score, box = detection.get("score"), detection.get("box_xyxy_normalized")
        if not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("MODEL_OUTPUT_INVALID")
        if not isinstance(box, list) or len(box) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in box):
            raise ValueError("MODEL_OUTPUT_INVALID")
        x1, y1, x2, y2 = box
        if x2 <= x1 or y2 <= y1:
            raise ValueError("MODEL_OUTPUT_INVALID")
        safe.append({"label": "skin_lesion_candidate", "score": float(score), "box_xyxy_normalized": [float(v) for v in box]})
    return safe
