"""Research-only computer-vision adapters for the existing ASTHRAL portal.

Uploaded media are held in memory, except for short-lived video decoder files
that are removed immediately after processing. No output is written to ASTHRAL
health-record storage.
"""
from __future__ import annotations

import base64
import binascii
import io
import json
import math
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from importlib import metadata, util
from pathlib import Path
from typing import Literal

try:
    import numpy as np
except ImportError:  # Optional vision runtime must not prevent the base portal from starting.
    np = None
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import Field, field_validator

from .models import Model

MODEL_ROOT = Path(__file__).resolve().parents[1] / "local_ai" / "computer-vision"
OCT_WEIGHTS = MODEL_ROOT / "oct" / "best_model.pth"
ECHO_WEIGHTS = MODEL_ROOT / "echo" / "deeplabv3_resnet50_random.pt"
HOLISTIC_ASSET = MODEL_ROOT / "motion" / "holistic_landmarker.task"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 9 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_VIDEO_FRAMES = 600
MAX_ANALYZED_FRAMES = 180
MAX_VIDEO_SECONDS = 20
MAX_EXPORT_VIDEO_BYTES = 24 * 1024 * 1024
ROTATIONS = (0, 90, 180, 270)


class ComputerVisionError(ValueError):
    def __init__(self, code: str, status_code: int = 422):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class OCTRequest(Model):
    image_data: str = Field(min_length=64, max_length=14_000_100)
    pixel_spacing_um: float | None = Field(default=None, gt=0, le=1000)

    @field_validator("image_data")
    @classmethod
    def image_url(cls, value):
        if not value.startswith(("data:image/jpeg;base64,", "data:image/png;base64,", "data:image/webp;base64,", "data:image/tiff;base64,")):
            raise ValueError("SUPPORTED_OCT_IMAGE_DATA_URL_REQUIRED")
        return value


class VideoRequest(Model):
    video_data: str = Field(min_length=64, max_length=12_800_100)
    filename: str = Field(min_length=1, max_length=180)
    rotation: Literal[0, 90, 180, 270] = 0
    mirror: bool = False
    frame_stride: int = Field(default=6, ge=1, le=30)
    confirm_a4c: bool = False
    exercise: Literal["knee_flexion", "arm_raise", "elbow_flexion", "squat", "balance"] = "knee_flexion"
    rep_prominence_degrees: float = Field(default=20, ge=5, le=90)

    @field_validator("video_data")
    @classmethod
    def video_url(cls, value):
        if not value.startswith(("data:video/mp4;base64,", "data:video/webm;base64,", "data:video/quicktime;base64,", "data:video/x-msvideo;base64,", "data:video/x-matroska;base64,")):
            raise ValueError("SUPPORTED_VIDEO_DATA_URL_REQUIRED")
        return value


class ComputerVisionService:
    """One lazy-loaded registry and contract for all four portal modules."""

    def __init__(self, model_root: Path = MODEL_ROOT):
        self.model_root = Path(model_root)
        self._models: dict[str, object] = {}
        self._last_error: dict[str, str] = {}
        self._lock = threading.RLock()
        self._inference_lock = threading.Lock()

    def get_model_status(self) -> dict:
        return {
            "modules": {
                "skinguard": {
                    "name": "ASTHRAL SkinGuard",
                    "model": "No compatible total-body lesion detector configured",
                    "version": None,
                    "provenance": "Candidate repositories audited; none provides verified compatible weights in this installation.",
                    "license": "Candidate code/data terms vary; no candidate weights are installed.",
                    "input": ["JPEG", "PNG", "WebP"],
                    "output": "No AI output until compatible detection weights and validation provenance are configured.",
                    "state": "MODEL_NOT_CONFIGURED",
                    "loaded": False,
                    "analysis_available": False,
                    "last_error": self._last_error.get("skinguard"),
                },
                "ocularvision": self._torch_status(
                    "ocularvision", "Retinal region segmentation U-Net", self.model_root / "oct" / "best_model.pth",
                    "Strange-Philip/oct-retinal-layer-segmentation · best_model.pth",
                    "MIT code; Duke/Chiu dataset has separate terms; weights are local and are not redistributed.",
                    ["JPEG", "PNG", "WebP", "TIFF"], "Background plus seven inter-boundary regions.",
                ),
                "echovision": self._torch_status(
                    "echovision", "EchoNet-Dynamic DeepLabV3 ResNet-50 LV segmenter", self.model_root / "echo" / "deeplabv3_resnet50_random.pt",
                    "EchoNet-Dynamic release v1.0.0 · deeplabv3_resnet50_random.pt",
                    "Checkpoint has no separate license statement located; local research-only use. EchoNet source code license prohibits redistribution without written permission; no source code is bundled.",
                    ["MP4", "WebM", "MOV", "AVI", "MKV"], "Frame-wise left-ventricle mask; no ejection-fraction output.",
                ),
                "motionguard": self._mediapipe_status(),
            },
            "storage": "Uploads and generated results remain in request/browser memory; temporary video files are deleted after processing.",
            "clinical_scope": "Experimental research computation only; not a diagnosis, validated measurement, or treatment recommendation.",
        }

    def close(self) -> None:
        with self._lock:
            model = self._models.pop("motionguard", None)
            if model:
                try:
                    model[1].close()
                except Exception:
                    pass

    def _torch_status(self, key, name, weights, provenance, license_text, inputs, outputs):
        present = weights.is_file()
        torch_ready = util.find_spec("torch") is not None and util.find_spec("torchvision") is not None
        loaded = key in self._models
        state = self._last_error.get(key) or ("MODEL_NOT_AVAILABLE" if not present else "DEPENDENCY_MISSING" if not torch_ready else "MODEL_OPERATIVE" if loaded else "MODEL_INSTALLED_NOT_LOADED")
        return {
            "name": name, "version": "research checkpoint", "provenance": provenance,
            "license": license_text, "input": inputs, "output": outputs,
            "weights_path": str(weights), "weights_installed": present, "loaded": loaded,
            "analysis_available": present and torch_ready, "state": state,
            "runtime": "CPU (bounded local inference)", "last_error": self._last_error.get(key),
        }

    def _mediapipe_status(self):
        installed = util.find_spec("mediapipe") is not None
        present = (self.model_root / "motion" / "holistic_landmarker.task").is_file()
        loaded = "motionguard" in self._models
        if self._last_error.get("motionguard"):
            state = self._last_error["motionguard"]
        elif not present:
            state = "MODEL_NOT_AVAILABLE"
        elif not installed:
            state = "DEPENDENCY_MISSING"
        else:
            state = "MODEL_OPERATIVE" if loaded else "MODEL_INSTALLED_NOT_LOADED"
        try:
            version = metadata.version("mediapipe") if installed else None
        except metadata.PackageNotFoundError:
            version = None
        return {
            "name": "MediaPipe Holistic Landmarker", "version": version or "0.10.21 (pinned)",
            "provenance": "Google AI Edge official Holistic Landmarker task model.",
            "license": "MediaPipe Apache-2.0; official model asset, locally installed.",
            "input": ["MP4", "WebM", "MOV", "AVI", "MKV"],
            "output": "Face, pose, and hand landmarks; projected 2D angles and descriptive movement summaries.",
            "asset_path": str(self.model_root / "motion" / "holistic_landmarker.task"),
            "weights_installed": present, "loaded": loaded,
            "analysis_available": installed and present, "state": state,
            "runtime": "CPU, video mode", "last_error": self._last_error.get("motionguard"),
        }

    def analyze_oct(self, request: OCTRequest) -> dict:
        started = time.perf_counter()
        if np is None:
            raise ComputerVisionError("NUMPY_DEPENDENCY_MISSING", 503)
        raw = decode_data_url(request.image_data, "image", MAX_IMAGE_BYTES)
        image, details = decode_oct_image(raw)
        declared = request.image_data.split(",", 1)[0][5:].split(";", 1)[0]
        expected_format = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP", "image/tiff": "TIFF"}.get(declared)
        if expected_format != details["format"]:
            image.close()
            raise ComputerVisionError("OCT_IMAGE_MIME_FORMAT_MISMATCH")
        try:
            model = self._load_oct()
            try:
                import torch
                with self._inference_lock, torch.inference_mode():
                    logits = model(torch.from_numpy(oct_input(image)).float().unsqueeze(0))
                    mask_net = torch.argmax(logits, dim=1)[0].cpu().numpy().astype(np.uint8)
            except Exception as exc:
                self._last_error["ocularvision"] = "INFERENCE_ERROR"
                raise ComputerVisionError("OCT_INFERENCE_FAILED", 503) from exc
            source_mask = unletterbox_mask(mask_net, image.size)
            overlay = render_mask_overlay(image, source_mask)
            h, w = source_mask.shape
            layer_stats = []
            for region in range(1, 8):
                per_column = np.count_nonzero(source_mask == region, axis=0)
                valid_columns = per_column[per_column > 0]
                average = float(valid_columns.mean()) if len(valid_columns) else 0.0
                layer_stats.append({"id": f"region_{region}", "label": f"Inter-boundary region {region}",
                                    "mean_thickness_px": round(average, 3), "covered_columns": int(len(valid_columns)),
                                    "mean_thickness_um": round(average * request.pixel_spacing_um, 3) if request.pixel_spacing_um else None})
            retinal_profile = np.count_nonzero(source_mask > 0, axis=0).astype(int).tolist()
            self._last_error.pop("ocularvision", None)
            return {
                "analysis_id": uuid.uuid4().hex,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "module": "ASTHRAL OcularVision",
                "state": "MODEL_ANALYSIS_COMPLETED",
                "analysis_performed": True,
                "model": "Strange-Philip OCT retinal-layer U-Net · best_model.pth",
                "model_task": "Research segmentation of seven regions between eight annotated retinal boundaries; not an SANS detector.",
                "image": {**details, "width": w, "height": h, "pixel_spacing_um": request.pixel_spacing_um,
                          "orientation_handling": "EXIF orientation applied before analysis; source dimensions retained in report."},
                "mask_png_base64": png_base64(Image.fromarray(source_mask.astype(np.uint8))),
                "overlay_png_base64": png_base64(overlay),
                "layers": layer_stats,
                "boundaries_px": extract_region_boundaries(source_mask),
                "retinal_span_profile_px": retinal_profile,
                "retinal_span_profile_um": [round(x * request.pixel_spacing_um, 3) for x in retinal_profile] if request.pixel_spacing_um else None,
                "parameters": {"input_shape": [496, 768], "normalization": "grayscale uint8 scaled to [0,1], aspect-preserving letterbox", "device": "CPU"},
                "processing_seconds": round(time.perf_counter() - started, 3),
                "limitations": [
                    "Research segmentation trained on a small Duke/Chiu 2015 sample; ASTHRAL has not externally validated it.",
                    "The output labels are inter-boundary regions, not a clinical diagnosis or calibrated probability.",
                    "No SANS, optic-disc edema, optic-nerve disorder, or clinical finding is detected by this model.",
                    "Thickness in micrometres is emitted only when the user provides pixel spacing; otherwise results remain in pixels.",
                ],
            }
        finally:
            image.close()

    def _load_oct(self):
        with self._lock:
            if "ocularvision" in self._models:
                return self._models["ocularvision"]
            weights = self.model_root / "oct" / "best_model.pth"
            if not weights.is_file():
                raise ComputerVisionError("OCT_MODEL_NOT_AVAILABLE", 503)
            try:
                import torch
                from .cv_unet import RetinalRegionUNet
                model = RetinalRegionUNet()
                checkpoint = torch.load(weights, map_location="cpu", weights_only=False)
                state = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
                if state and all(str(k).startswith("module.") for k in state):
                    state = {str(k)[7:]: v for k, v in state.items()}
                model.load_state_dict(state, strict=True)
                model.eval()
                self._models["ocularvision"] = model
                return model
            except Exception as exc:
                self._last_error["ocularvision"] = "MODEL_LOAD_ERROR"
                raise ComputerVisionError("OCT_MODEL_LOAD_FAILED", 503) from exc

    def analyze_echo(self, request: VideoRequest) -> dict:
        if not request.confirm_a4c:
            raise ComputerVisionError("ECHOVISION_REQUIRES_USER_CONFIRMATION_OF_APICAL_4_CHAMBER_VIEW")
        return self._analyze_video(request, "echo")

    def analyze_motion(self, request: VideoRequest) -> dict:
        return self._analyze_video(request, "motionguard")

    def _load_echo(self):
        with self._lock:
            if "echovision" in self._models:
                return self._models["echovision"]
            weights = self.model_root / "echo" / "deeplabv3_resnet50_random.pt"
            if not weights.is_file():
                raise ComputerVisionError("ECHONET_SEGMENTATION_WEIGHTS_NOT_AVAILABLE", 503)
            try:
                import torch
                import torchvision
                model = torchvision.models.segmentation.deeplabv3_resnet50(weights=None, weights_backbone=None, aux_loss=False)
                model.classifier[-1] = torch.nn.Conv2d(model.classifier[-1].in_channels, 1, kernel_size=model.classifier[-1].kernel_size)
                checkpoint = torch.load(weights, map_location="cpu", weights_only=False)
                state = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
                if state and all(str(k).startswith("module.") for k in state):
                    state = {str(k)[7:]: v for k, v in state.items()}
                model.load_state_dict(state, strict=True)
                model.eval()
                self._models["echovision"] = model
                return model
            except Exception as exc:
                self._last_error["echovision"] = "MODEL_LOAD_ERROR"
                raise ComputerVisionError("ECHONET_MODEL_LOAD_FAILED", 503) from exc

    def _load_motion(self):
        with self._lock:
            if "motionguard" in self._models:
                return self._models["motionguard"]
            asset = self.model_root / "motion" / "holistic_landmarker.task"
            if not asset.is_file():
                raise ComputerVisionError("HOLISTIC_MODEL_ASSET_NOT_AVAILABLE", 503)
            try:
                import mediapipe as mp
                options = mp.tasks.vision.HolisticLandmarkerOptions(
                    base_options=mp.tasks.BaseOptions(model_asset_path=str(asset)),
                    running_mode=mp.tasks.vision.RunningMode.VIDEO,
                    min_face_detection_confidence=0.5,
                    min_pose_detection_confidence=0.5,
                )
                # MediaPipe Tasks landmarker is context-managed; retain it until process shutdown.
                landmarker = mp.tasks.vision.HolisticLandmarker.create_from_options(options)
                self._models["motionguard"] = (mp, landmarker)
                return self._models["motionguard"]
            except Exception as exc:
                self._last_error["motionguard"] = "MODEL_LOAD_ERROR"
                raise ComputerVisionError("HOLISTIC_MODEL_LOAD_FAILED", 503) from exc

    def _analyze_video(self, request: VideoRequest, mode: str) -> dict:
        started = time.perf_counter()
        raw = decode_data_url(request.video_data, "video", MAX_VIDEO_BYTES)
        extension = Path(request.filename).suffix.lower()
        allowed = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
        if extension not in allowed:
            raise ComputerVisionError("UNSUPPORTED_VIDEO_EXTENSION")
        if mode == "echo":
            model = self._load_echo()
        else:
            mp, landmarker = self._load_motion()
        inference_lock_acquired = self._inference_lock.acquire(blocking=False)
        if not inference_lock_acquired:
            raise ComputerVisionError("COMPUTER_VISION_BUSY", 429)
        temp_path = None
        output_path = None
        capture = None
        writer = None
        try:
            with tempfile.NamedTemporaryFile(prefix="asthral-cv-in-", suffix=extension, delete=False) as temp:
                temp.write(raw)
                temp_path = Path(temp.name)
            capture = cv2_module().VideoCapture(str(temp_path))
            if not capture.isOpened():
                raise ComputerVisionError("VIDEO_DECODER_CANNOT_OPEN_FILE")
            fps = float(capture.get(cv2_module().CAP_PROP_FPS) or 0)
            width = int(capture.get(cv2_module().CAP_PROP_FRAME_WIDTH) or 0)
            height = int(capture.get(cv2_module().CAP_PROP_FRAME_HEIGHT) or 0)
            expected_frames = int(capture.get(cv2_module().CAP_PROP_FRAME_COUNT) or 0)
            if width <= 0 or height <= 0 or expected_frames <= 0:
                raise ComputerVisionError("VIDEO_HAS_NO_VALID_FRAMES")
            if expected_frames > MAX_VIDEO_FRAMES or (fps > 0 and expected_frames / fps > MAX_VIDEO_SECONDS):
                raise ComputerVisionError("VIDEO_DURATION_OR_FRAME_LIMIT_EXCEEDED", 413)
            if expected_frames > MAX_ANALYZED_FRAMES * request.frame_stride:
                raise ComputerVisionError("REDUCE_VIDEO_LENGTH_OR_INCREASE_FRAME_STRIDE", 413)
            fps = fps if math.isfinite(fps) and 1 <= fps <= 120 else 30.0
            if width * height > 12_000_000:
                raise ComputerVisionError("VIDEO_FRAME_DIMENSIONS_EXCEED_LIMIT", 413)
            cv2 = cv2_module()
            with tempfile.NamedTemporaryFile(prefix="asthral-cv-out-", suffix=".mp4", delete=False) as temp_out:
                output_path = Path(temp_out.name)
            writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            if not writer.isOpened():
                writer.release(); writer = None
                output_path.unlink(missing_ok=True); output_path = None

            frames = []
            first_overlay = None
            first_mask = None
            frame_index = 0
            last_timestamp = -1
            while True:
                ok, frame_bgr = capture.read()
                if not ok:
                    break
                if frame_index >= MAX_VIDEO_FRAMES:
                    raise ComputerVisionError("VIDEO_FRAME_LIMIT_EXCEEDED", 413)
                original = frame_bgr.copy()
                if frame_index % request.frame_stride == 0:
                    transformed_bgr = transform_frame(frame_bgr, request.rotation, request.mirror)
                    if mode == "echo":
                        mask, overlay_bgr = predict_echo_frame(model, transformed_bgr)
                        if first_mask is None:
                            first_mask = mask.copy()
                        record = {"frame": frame_index, "time_seconds": round(frame_index / fps, 4),
                                  "lv_area_pixels_transformed": int(np.count_nonzero(mask)),
                                  "mask_shape": list(mask.shape), "model_output_threshold": "logit > 0"}
                        frames.append(record)
                    else:
                        transformed_rgb = cv2.cvtColor(transformed_bgr, cv2.COLOR_BGR2RGB)
                        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=transformed_rgb)
                        timestamp = max(0, round(frame_index * 1000 / fps))
                        timestamp = max(timestamp, last_timestamp + 1)
                        last_timestamp = timestamp
                        result = landmarker.detect_for_video(mp_image, timestamp)
                        pose = landmarks_to_rows(getattr(result, "pose_landmarks", []) or [])
                        face = landmarks_to_rows(getattr(result, "face_landmarks", []) or [])
                        overlay_bgr = draw_holistic_overlay(transformed_bgr, pose, face,
                            getattr(result, "left_hand_landmarks", []) or [], getattr(result, "right_hand_landmarks", []) or [])
                        frames.append({
                            "frame": frame_index, "time_seconds": round(frame_index / fps, 4),
                            "pose_landmarks": pose,
                            "pose_world_landmarks": landmarks_to_rows(getattr(result, "pose_world_landmarks", []) or [], world=True),
                            "face_landmarks": face,
                            "left_hand_landmarks": landmarks_to_rows(getattr(result, "left_hand_landmarks", []) or []),
                            "right_hand_landmarks": landmarks_to_rows(getattr(result, "right_hand_landmarks", []) or []),
                            "tracking_quality": pose_quality(pose),
                        })
                    if first_overlay is None:
                        first_overlay = overlay_bgr.copy()
                    display_bgr = inverse_transform_frame(overlay_bgr, request.rotation, request.mirror)
                    if writer:
                        writer.write(display_bgr)
                elif writer:
                    writer.write(original)
                frame_index += 1
            if capture:
                capture.release(); capture = None
            if writer:
                writer.release(); writer = None
            if not frame_index:
                raise ComputerVisionError("VIDEO_HAS_NO_VALID_FRAMES")
            if expected_frames > 0 and frame_index < max(1, expected_frames // 2):
                raise ComputerVisionError("VIDEO_DECODE_FAILED_OR_TRUNCATED")
            if first_overlay is None:
                raise ComputerVisionError("NO_FRAMES_SELECTED_FOR_ANALYSIS")
            encoded_video = video_base64(output_path)
            if mode == "echo":
                result = {
                    "analysis_id": uuid.uuid4().hex, "created_at": datetime.now(timezone.utc).isoformat(),
                    "module": "ASTHRAL EchoVision", "state": "MODEL_ANALYSIS_COMPLETED", "analysis_performed": True,
                    "model": "EchoNet-Dynamic DeepLabV3 ResNet-50 · segmentation checkpoint v1.0.0",
                    "video": {"filename": Path(request.filename).name, "width": width, "height": height, "fps": fps,
                              "decoded_frames": frame_index, "duration_seconds": round(frame_index / fps, 3),
                              "user_confirmed_apical_4_chamber": True, "rotation_degrees": request.rotation, "mirrored_for_inference": request.mirror},
                    "sampled_frames": frames,
                    "overlay_frame_jpeg_base64": jpeg_base64(first_overlay),
                    "mask_png_base64": png_base64(Image.fromarray(first_mask * 255, mode="L")) if first_mask is not None else None,
                    "overlay_video_base64": encoded_video,
                    "overlay_video_exported": encoded_video is not None,
                    "parameters": {"input_size": [112, 112], "frame_stride": request.frame_stride,
                                   "normalization": "per-frame RGB z-score adaptation; not the official training-set statistic", "threshold": "logit > 0", "device": "CPU"},
                    "processing_seconds": round(time.perf_counter() - started, 3),
                    "limitations": [
                        "The checkpoint was trained for apical four-chamber (A4C) echocardiograms; the user must confirm the view.",
                        "Only LV segmentation is implemented. No ejection fraction or other cardiac measurement is computed.",
                        "Input is resized to 112 × 112; masks are qualitative contours, with no physical scale.",
                        "The per-frame normalization is an explicitly experimental deployment adaptation, not the EchoNet training pipeline.",
                        "ASTHRAL has not evaluated Dice, IoU, or clinical performance on a held-out dataset.",
                    ],
                }
                self._last_error.pop("echovision", None)
            else:
                add_angles(frames, width, height)
                summary = motion_summary(frames, request.exercise, request.rep_prominence_degrees)
                result = {
                    "analysis_id": uuid.uuid4().hex, "created_at": datetime.now(timezone.utc).isoformat(),
                    "module": "ASTHRAL MotionGuard", "state": "MODEL_ANALYSIS_COMPLETED", "analysis_performed": True,
                    "model": f"MediaPipe Holistic Landmarker {metadata.version('mediapipe')}",
                    "video": {"filename": Path(request.filename).name, "width": width, "height": height, "fps": fps,
                              "decoded_frames": frame_index, "duration_seconds": round(frame_index / fps, 3),
                              "rotation_degrees": request.rotation, "mirrored_for_inference": request.mirror},
                    "exercise": request.exercise, "frame_stride": request.frame_stride,
                    "summary": summary, "frames": frames,
                    "overlay_frame_jpeg_base64": jpeg_base64(first_overlay),
                    "overlay_video_base64": encoded_video,
                    "overlay_video_exported": encoded_video is not None,
                    "processing_seconds": round(time.perf_counter() - started, 3),
                    "limitations": [
                        "Angles are projected 2D image-plane estimates from normalized MediaPipe landmarks, not calibrated clinical measurements.",
                        "World landmarks are model outputs and are not force, moment, muscle-activation, bone-density, or muscle-mass measurements.",
                        "Repetition counting uses a configurable angular excursion threshold; it is descriptive and not clinically validated.",
                        "Tracking quality is the fraction of pose landmarks with visibility at least 0.5; it is not a clinical quality score.",
                        "This prototype does not infer muscle loss, osteoporosis, neurological disease, or treatment readiness.",
                    ],
                }
                self._last_error.pop("motionguard", None)
            return result
        except ComputerVisionError:
            raise
        except MemoryError as exc:
            self._last_error["echovision" if mode == "echo" else "motionguard"] = "INFERENCE_ERROR"
            raise ComputerVisionError("INFERENCE_MEMORY_LIMIT_EXCEEDED", 503) from exc
        except Exception as exc:
            self._last_error["echovision" if mode == "echo" else "motionguard"] = "INFERENCE_ERROR"
            raise ComputerVisionError("VIDEO_INFERENCE_FAILED", 503) from exc
        finally:
            if capture:
                capture.release()
            if writer:
                writer.release()
            if temp_path:
                temp_path.unlink(missing_ok=True)
            if output_path:
                output_path.unlink(missing_ok=True)
            if inference_lock_acquired:
                self._inference_lock.release()


def cv2_module():
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise ComputerVisionError("OPENCV_DEPENDENCY_MISSING", 503) from exc


def decode_data_url(value: str, kind: str, maximum: int) -> bytes:
    try:
        prefix, encoded = value.split(",", 1)
        if ";base64" not in prefix or not prefix.startswith(f"data:{kind}/"):
            raise ValueError
        if len(encoded) > ((maximum + 2) // 3) * 4 + 8:
            raise ComputerVisionError(f"{kind.upper()}_TOO_LARGE", 413)
        raw = base64.b64decode(encoded, validate=True)
    except ComputerVisionError:
        raise
    except (ValueError, binascii.Error) as exc:
        raise ComputerVisionError(f"INVALID_{kind.upper()}_DATA_URL") from exc
    if not raw:
        raise ComputerVisionError(f"EMPTY_{kind.upper()}_FILE")
    if len(raw) > maximum:
        raise ComputerVisionError(f"{kind.upper()}_TOO_LARGE", 413)
    return raw


def decode_oct_image(raw: bytes) -> tuple[Image.Image, dict]:
    try:
        with Image.open(io.BytesIO(raw)) as source:
            image_format = source.format
            if image_format not in {"JPEG", "PNG", "WEBP", "TIFF"}:
                raise ComputerVisionError("UNSUPPORTED_OCT_IMAGE_FORMAT")
            raw_width, raw_height = source.size
            if raw_width < 64 or raw_height < 64 or raw_width * raw_height > MAX_IMAGE_PIXELS:
                raise ComputerVisionError("OCT_IMAGE_DIMENSIONS_INVALID")
            orientation = source.getexif().get(274, 1)
            source.seek(0)
            oriented = ImageOps.exif_transpose(source)
            if oriented.mode.startswith("I;16") or oriented.mode == "I":
                pixels = np.asarray(oriented, dtype=np.float32)
                lo, hi = np.percentile(pixels, [0.5, 99.5])
                if not math.isfinite(float(lo)) or not math.isfinite(float(hi)) or hi <= lo:
                    raise ComputerVisionError("OCT_IMAGE_INTENSITY_RANGE_INVALID")
                pixels = np.clip((pixels - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
                image = Image.fromarray(pixels, mode="L")
                intensity = {"conversion": "16-bit grayscale clipped to 0.5-99.5 percentiles then scaled to uint8", "source_range": [float(lo), float(hi)]}
            else:
                image = oriented.convert("L")
                intensity = {"conversion": "grayscale converted to uint8"}
            image.load()
            return image, {"format": image_format, "source_width": raw_width, "source_height": raw_height,
                           "exif_orientation": orientation, "intensity": intensity}
    except ComputerVisionError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ComputerVisionError("INVALID_OR_CORRUPT_OCT_IMAGE") from exc


def oct_input(image: Image.Image) -> np.ndarray:
    """Preserve the B-scan aspect ratio while fitting the checkpoint's 768×496 input."""
    target_w, target_h = 768, 496
    width, height = image.size
    scale = min(target_w / width, target_h / height)
    new_w, new_h = max(1, round(width * scale)), max(1, round(height * scale))
    resized = image.resize((new_w, new_h), Image.Resampling.BILINEAR)
    canvas = Image.new("L", (target_w, target_h), 0)
    left, top = (target_w - new_w) // 2, (target_h - new_h) // 2
    canvas.paste(resized, (left, top))
    tensor = np.asarray(canvas, dtype=np.float32) / 255.0
    return tensor[None, ...]


def unletterbox_mask(mask: np.ndarray, original_size: tuple[int, int]) -> np.ndarray:
    target_w, target_h = 768, 496
    width, height = original_size
    scale = min(target_w / width, target_h / height)
    new_w, new_h = max(1, round(width * scale)), max(1, round(height * scale))
    left, top = (target_w - new_w) // 2, (target_h - new_h) // 2
    region = mask[top:top + new_h, left:left + new_w]
    output = Image.fromarray(region.astype(np.uint8), mode="L").resize((width, height), Image.Resampling.NEAREST)
    return np.asarray(output, dtype=np.uint8)


def render_mask_overlay(image: Image.Image, mask: np.ndarray) -> Image.Image:
    original = np.asarray(image.convert("RGB"), dtype=np.uint8)
    colors = np.asarray([[0, 0, 0], [230, 75, 75], [250, 155, 60], [230, 205, 65], [80, 180, 110], [65, 170, 210], [95, 110, 230], [180, 95, 205]], dtype=np.uint8)
    colored = colors[np.clip(mask, 0, len(colors) - 1)]
    active = mask > 0
    output = original.copy()
    output[active] = (0.55 * original[active] + 0.45 * colored[active]).astype(np.uint8)
    return Image.fromarray(output, mode="RGB")


def extract_region_boundaries(mask: np.ndarray) -> list[dict]:
    height, width = mask.shape
    boundaries = []
    for region in range(1, 8):
        upper, lower = [], []
        for x in range(width):
            rows = np.flatnonzero(mask[:, x] == region)
            upper.append(int(rows[0]) if len(rows) else None)
            lower.append(int(rows[-1] + 1) if len(rows) else None)
        boundaries.append({"region": region, "upper_px_by_column": upper, "lower_exclusive_px_by_column": lower})
    return boundaries


def png_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def jpeg_base64(image_bgr: np.ndarray) -> str:
    ok, encoded = cv2_module().imencode(".jpg", image_bgr, [cv2_module().IMWRITE_JPEG_QUALITY, 84])
    if not ok:
        raise ComputerVisionError("RESULT_IMAGE_ENCODING_FAILED", 503)
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def video_base64(path: Path | None) -> str | None:
    if path is None or not path.is_file() or path.stat().st_size > MAX_EXPORT_VIDEO_BYTES:
        return None
    return base64.b64encode(path.read_bytes()).decode("ascii")


def transform_frame(frame: np.ndarray, rotation: int, mirror: bool) -> np.ndarray:
    cv2 = cv2_module()
    if rotation == 90:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation == 270:
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if mirror:
        frame = cv2.flip(frame, 1)
    return frame


def inverse_transform_frame(frame: np.ndarray, rotation: int, mirror: bool) -> np.ndarray:
    cv2 = cv2_module()
    if mirror:
        frame = cv2.flip(frame, 1)
    if rotation == 90:
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rotation == 180:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation == 270:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame


def predict_echo_frame(model, frame_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    import torch
    cv2 = cv2_module()
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    model_image = cv2.resize(frame_rgb, (112, 112), interpolation=cv2.INTER_AREA).astype(np.float32)
    mean = model_image.mean(axis=(0, 1), keepdims=True)
    std = model_image.std(axis=(0, 1), keepdims=True)
    normalized = (model_image - mean) / np.maximum(std, 1e-6)
    tensor = torch.from_numpy(normalized.transpose(2, 0, 1)[None]).float()
    with torch.inference_mode():
        logits = model(tensor)["out"][0, 0].cpu().numpy()
    mask = (logits > 0).astype(np.uint8)
    height, width = frame_bgr.shape[:2]
    full_mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST)
    overlay = frame_bgr.copy()
    contours, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cv2.drawContours(overlay, contours, -1, (60, 220, 90), 2)
        tint = overlay[full_mask > 0].astype(np.float32)
        original = frame_bgr[full_mask > 0].astype(np.float32)
        overlay[full_mask > 0] = (0.65 * original + 0.35 * tint).astype(np.uint8)
    return full_mask, overlay


def landmarks_to_rows(items, world: bool = False) -> list[dict]:
    output = []
    for item in items:
        row = {"x": round(float(item.x), 6), "y": round(float(item.y), 6), "z": round(float(item.z), 6)}
        visibility = getattr(item, "visibility", None)
        presence = getattr(item, "presence", None)
        if visibility is not None:
            row["visibility"] = round(float(visibility), 5)
        if presence is not None:
            row["presence"] = round(float(presence), 5)
        output.append(row)
    return output


POSE_EDGES = ((11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24),
              (23, 25), (25, 27), (24, 26), (26, 28), (27, 31), (28, 32))


def draw_holistic_overlay(frame: np.ndarray, pose: list[dict], face: list[dict], left_hand, right_hand) -> np.ndarray:
    cv2 = cv2_module()
    output = frame.copy()
    h, w = output.shape[:2]
    for start, end in POSE_EDGES:
        if start < len(pose) and end < len(pose):
            a, b = pose[start], pose[end]
            cv2.line(output, (int(a["x"] * w), int(a["y"] * h)), (int(b["x"] * w), int(b["y"] * h)), (125, 230, 180), 2, cv2.LINE_AA)
    for point in pose:
        cv2.circle(output, (int(point["x"] * w), int(point["y"] * h)), 3, (70, 140, 255), -1, cv2.LINE_AA)
    for index in (1, 10, 33, 61, 152, 263, 291):
        if index < len(face):
            point = face[index]
            cv2.circle(output, (int(point["x"] * w), int(point["y"] * h)), 3, (220, 110, 210), -1, cv2.LINE_AA)
    for hand in (left_hand, right_hand):
        for point in hand:
            cv2.circle(output, (int(point.x * w), int(point.y * h)), 2, (245, 210, 65), -1, cv2.LINE_AA)
    return output


def pose_quality(pose: list[dict]) -> dict:
    if not pose:
        return {"visible_pose_landmarks": 0, "total_pose_landmarks": 33, "visible_fraction": 0.0, "tracking_lost": True}
    visible = sum(float(point.get("visibility", point.get("presence", 0))) >= 0.5 for point in pose)
    fraction = visible / 33
    return {"visible_pose_landmarks": visible, "total_pose_landmarks": 33,
            "visible_fraction": round(fraction, 4), "tracking_lost": len(pose) < 33 or fraction < 0.5}


def projected_angle(a: dict, b: dict, c: dict, width: int, height: int) -> float | None:
    if min(float(a.get("visibility", 0)), float(b.get("visibility", 0)), float(c.get("visibility", 0))) < 0.35:
        return None
    pa = np.asarray([float(a["x"]) * width, float(a["y"]) * height], dtype=np.float64)
    pb = np.asarray([float(b["x"]) * width, float(b["y"]) * height], dtype=np.float64)
    pc = np.asarray([float(c["x"]) * width, float(c["y"]) * height], dtype=np.float64)
    first, second = pa - pb, pc - pb
    denom = float(np.linalg.norm(first) * np.linalg.norm(second))
    if not math.isfinite(denom) or denom <= 1e-8:
        return None
    cosine = float(np.clip(np.dot(first, second) / denom, -1, 1))
    return round(math.degrees(math.acos(cosine)), 3)


def angles_for_pose(pose: list[dict], width: int, height: int) -> dict:
    if len(pose) < 33:
        return {key: None for key in ("knee_left", "knee_right", "elbow_left", "elbow_right", "hip_left", "hip_right", "shoulder_left", "shoulder_right")}
    indices = {"knee_left": (23, 25, 27), "knee_right": (24, 26, 28),
               "elbow_left": (11, 13, 15), "elbow_right": (12, 14, 16),
               "hip_left": (11, 23, 25), "hip_right": (12, 24, 26),
               "shoulder_left": (13, 11, 23), "shoulder_right": (14, 12, 24)}
    result = {name: projected_angle(*(pose[i] for i in triple), width, height) for name, triple in indices.items()}
    if all(float(pose[i].get("visibility", 0)) >= 0.35 for i in (11, 12, 23, 24)):
        shoulders = np.mean([[pose[i]["x"] * width, pose[i]["y"] * height] for i in (11, 12)], axis=0)
        hips = np.mean([[pose[i]["x"] * width, pose[i]["y"] * height] for i in (23, 24)], axis=0)
        delta = shoulders - hips
        result["trunk_inclination"] = round(math.degrees(math.atan2(float(delta[0]), -float(delta[1]))), 3)
    else:
        result["trunk_inclination"] = None
    return result


def motion_summary(frames: list[dict], exercise: str, prominence: float) -> dict:
    quality = [frame.get("tracking_quality", {}).get("visible_fraction", 0) for frame in frames]
    missing = sum(frame.get("tracking_quality", {}).get("tracking_lost", True) for frame in frames)
    angle_series = [frame.get("angles_2d", {}) for frame in frames]
    values = {name: [row.get(name) for row in angle_series if row.get(name) is not None]
              for name in ("knee_left", "knee_right", "elbow_left", "elbow_right", "hip_left", "hip_right", "shoulder_left", "shoulder_right", "trunk_inclination")}
    rom = {name: round(max(nums) - min(nums), 3) if nums else None for name, nums in values.items()}
    velocities = {name: [abs(float(frame.get("angular_velocity_degrees_per_second", {}).get(name)))
                         for frame in frames
                         if frame.get("angular_velocity_degrees_per_second", {}).get(name) is not None]
                  for name in values}
    velocity_summary = {name: {"mean_abs_degrees_per_second": round(float(np.mean(nums)), 3),
                               "max_abs_degrees_per_second": round(float(max(nums)), 3)} if nums else None
                        for name, nums in velocities.items()}
    bilateral = {}
    for group in ("knee", "elbow", "hip", "shoulder"):
        left, right = rom.get(f"{group}_left"), rom.get(f"{group}_right")
        bilateral[group] = round(max(0.0, 100 * (1 - abs(left - right) / max(left, right))), 2) if left is not None and right is not None and max(left, right) > 0 else None
    selected = {"knee_flexion": "knee", "squat": "knee", "elbow_flexion": "elbow", "arm_raise": "shoulder"}.get(exercise)
    rep_series = []
    if selected:
        for frame in frames:
            row = frame.get("angles_2d", {})
            available = [row.get(f"{selected}_left"), row.get(f"{selected}_right")]
            available = [float(v) for v in available if v is not None]
            rep_series.append(sum(available) / len(available) if available else None)
    repetition_count = count_repetitions(rep_series, prominence) if selected else None
    pelvis = []
    for frame in frames:
        pose = frame.get("pose_landmarks", [])
        if len(pose) >= 25 and pose[23].get("visibility", 0) >= 0.35 and pose[24].get("visibility", 0) >= 0.35:
            pelvis.append({"time_seconds": frame["time_seconds"], "x_normalized": round((pose[23]["x"] + pose[24]["x"]) / 2, 6),
                           "y_normalized": round((pose[23]["y"] + pose[24]["y"]) / 2, 6)})
    summary = {
        "exercise": exercise,
        "repetitions": repetition_count,
        "repetition_rule": f"Local angular peaks above the session minimum by {prominence:g} projected degrees; descriptive and configurable, not a clinical target." if selected else "No repetition count for static balance.",
        "range_of_motion_degrees_2d": rom,
        "angular_velocity_degrees_per_second_2d": velocity_summary,
        "bilateral_rom_symmetry_percent": bilateral,
        "mean_pose_tracking_visibility_fraction": round(float(np.mean(quality)), 4) if quality else None,
        "tracking_loss_frames": int(missing),
        "processed_frames": len(frames),
        "pelvis_trajectory_normalized": pelvis,
    }
    if exercise == "balance":
        summary["balance_note"] = "Pelvis trajectory is in normalized image coordinates only; no force, sway velocity, or physical displacement is inferred."
    return summary


def count_repetitions(values: list[float | None], prominence_degrees: float = 20.0) -> int:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if len(clean) < 3 or max(clean) - min(clean) < prominence_degrees:
        return 0
    peak_threshold = min(clean) + prominence_degrees
    peaks = [i for i in range(1, len(values) - 1)
             if values[i] is not None and values[i] >= peak_threshold
             and values[i] >= (values[i - 1] if values[i - 1] is not None else -math.inf)
             and values[i] > (values[i + 1] if values[i + 1] is not None else -math.inf)]
    return len(peaks)


def add_angles(frames: list[dict], width: int, height: int) -> None:
    previous: dict[str, tuple[float, float]] = {}
    for frame in frames:
        frame["angles_2d"] = angles_for_pose(frame.get("pose_landmarks", []), width, height)
        velocity = {}
        timestamp = float(frame["time_seconds"])
        for name, value in frame["angles_2d"].items():
            if value is None:
                previous.pop(name, None)
                velocity[name] = None
                continue
            if name in previous and timestamp > previous[name][0]:
                dt = timestamp - previous[name][0]
                velocity[name] = round((float(value) - previous[name][1]) / dt, 3)
            else:
                velocity[name] = None
            previous[name] = (timestamp, float(value))
        frame["angular_velocity_degrees_per_second"] = velocity
