import base64
from io import BytesIO
import itertools

import pytest
from PIL import Image

from vigile.computer_vision import (
    ComputerVisionService,
    ComputerVisionError,
    MAX_EXPORT_VIDEO_BYTES,
    OCTRequest,
    VideoRequest,
    count_repetitions,
    decode_data_url,
    decode_oct_image,
    angles_for_pose,
    add_angles,
    draw_holistic_overlay,
    extract_region_boundaries,
    jpeg_base64,
    landmarks_to_rows,
    motion_summary,
    oct_input,
    projected_angle,
    pose_quality,
    render_mask_overlay,
    transform_frame,
    inverse_transform_frame,
    unletterbox_mask,
    video_base64,
)


def data_url(image: Image.Image) -> str:
    stream = BytesIO()
    image.save(stream, format="PNG")
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode("ascii")


def test_registry_reports_missing_weights_without_faking_availability(tmp_path):
    modules = ComputerVisionService(tmp_path).get_model_status()["modules"]
    assert set(modules) == {"skinguard", "ocularvision", "echovision", "motionguard"}
    assert modules["skinguard"]["state"] == "MODEL_NOT_CONFIGURED"
    assert modules["echovision"]["state"] == "LICENSE_REVIEW_REQUIRED"
    assert modules["echovision"]["execution_enabled"] is False
    assert modules["echovision"]["analysis_available"] is False
    for name in ("ocularvision", "motionguard"):
        assert modules[name]["state"] == "MODEL_NOT_AVAILABLE"
        assert modules[name]["analysis_available"] is False


def test_data_url_limits_and_corrupt_input_are_explicit():
    raw = b"valid bytes"
    encoded = base64.b64encode(raw).decode("ascii")
    assert decode_data_url(f"data:image/png;base64,{encoded}", "image", 20) == raw
    with pytest.raises(ComputerVisionError, match="INVALID_IMAGE_DATA_URL"):
        decode_data_url("data:image/png;base64,not*base64", "image", 20)
    with pytest.raises(ComputerVisionError, match="IMAGE_TOO_LARGE"):
        decode_data_url("data:image/png;base64," + base64.b64encode(b"x" * 21).decode(), "image", 20)


def test_oct_validation_orientation_preprocessing_and_scale():
    np = pytest.importorskip("numpy")
    image = Image.new("L", (80, 100), 120)
    exif = Image.Exif()
    exif[274] = 6
    stream = BytesIO()
    image.save(stream, format="TIFF", exif=exif)
    decoded, details = decode_oct_image(stream.getvalue())
    assert decoded.size == (100, 80)
    assert details["exif_orientation"] == 6
    tensor = oct_input(decoded)
    assert tensor.shape == (1, 496, 768)
    assert tensor.dtype == np.float32 and 0 <= tensor.min() <= tensor.max() <= 1
    restored = unletterbox_mask(np.ones((496, 768), dtype=np.uint8), decoded.size)
    assert restored.shape == (80, 100) and restored.all()


def test_region_boundaries_use_source_pixel_coordinates():
    np = pytest.importorskip("numpy")
    mask = np.zeros((9, 4), dtype=np.uint8)
    mask[2:5, :,] = 1
    region = extract_region_boundaries(mask)[0]
    assert region["upper_px_by_column"] == [2, 2, 2, 2]
    assert region["lower_exclusive_px_by_column"] == [5, 5, 5, 5]
    assert extract_region_boundaries(mask)[1]["upper_px_by_column"] == [None] * 4


def test_projected_joint_angle_and_configurable_repetition_counter():
    points = [
        {"x": 0.5, "y": 0.0, "visibility": 1.0},
        {"x": 0.5, "y": 0.5, "visibility": 1.0},
        {"x": 1.0, "y": 0.5, "visibility": 1.0},
    ]
    assert projected_angle(*points, 100, 100) == pytest.approx(90.0)
    assert count_repetitions([0, 10, 30, 10, 0, 5, 32, 10, 0], 20) == 2
    assert count_repetitions([0, 5, 10, 4, 0], 20) == 0


def test_rotation_and_mirror_are_reversible():
    np = pytest.importorskip("numpy")
    pytest.importorskip("cv2")
    frame = np.arange(4 * 7 * 3, dtype=np.uint8).reshape(4, 7, 3)
    transformed = transform_frame(frame, 90, True)
    assert transformed.shape == (7, 4, 3)
    assert (inverse_transform_frame(transformed, 90, True) == frame).all()


@pytest.mark.parametrize("rotation,mirror", list(itertools.product((0, 90, 180, 270), (False, True))))
def test_all_rotation_mirror_combinations_preserve_frame_pixels(rotation, mirror):
    np = pytest.importorskip("numpy")
    pytest.importorskip("cv2")
    frame = np.arange(5 * 9 * 3, dtype=np.uint8).reshape(5, 9, 3)
    transformed = transform_frame(frame, rotation, mirror)
    restored = inverse_transform_frame(transformed, rotation, mirror)
    assert restored.shape == frame.shape
    assert np.array_equal(restored, frame)


@pytest.mark.parametrize("size", [(64, 64), (200, 64), (64, 200), (777, 493)])
def test_oct_letterbox_and_unletterbox_preserve_size_and_label_set(size):
    np = pytest.importorskip("numpy")
    image = Image.new("L", size, color=128)
    tensor = oct_input(image)
    assert tensor.shape == (1, 496, 768)
    assert tensor.dtype == np.float32
    assert 0 <= float(tensor.min()) <= float(tensor.max()) <= 1
    source_mask = np.zeros((496, 768), dtype=np.uint8)
    source_mask[100:300, 200:500] = 7
    restored = unletterbox_mask(source_mask, size)
    assert restored.shape == (size[1], size[0])
    assert set(np.unique(restored)).issubset({0, 7})


@pytest.mark.parametrize("raw", [b"", b"not an image", b"\x00" * 100])
def test_oct_decoder_rejects_corrupt_image_bytes(raw):
    with pytest.raises(ComputerVisionError, match="INVALID_OR_CORRUPT_OCT_IMAGE"):
        decode_oct_image(raw)


@pytest.mark.parametrize("size", [(63, 100), (100, 63), (5001, 5001)])
def test_oct_decoder_rejects_too_small_or_excessive_images(size):
    image = Image.new("L", size, color=100)
    stream = BytesIO()
    image.save(stream, format="PNG")
    with pytest.raises(ComputerVisionError, match="OCT_IMAGE_DIMENSIONS_INVALID"):
        decode_oct_image(stream.getvalue())


def test_mask_visualization_is_deterministic_and_keeps_background_unchanged():
    np = pytest.importorskip("numpy")
    original = Image.new("RGB", (4, 3), (20, 40, 60))
    mask = np.zeros((3, 4), dtype=np.uint8)
    mask[1, 2] = 1
    overlay = render_mask_overlay(original, mask)
    assert overlay.size == original.size
    assert overlay.getpixel((0, 0)) == (20, 40, 60)
    assert overlay.getpixel((2, 1)) != original.getpixel((2, 1))


def test_pose_quality_and_projected_angles_cover_missing_and_low_confidence():
    assert pose_quality([])["tracking_lost"] is True
    low = [{"visibility": 0.2} for _ in range(33)]
    assert pose_quality(low)["tracking_lost"] is True
    assert projected_angle(low[0], low[0], low[0], 100, 100) is None
    visible = [{"x": 0.5, "y": 0.5, "visibility": 1.0} for _ in range(33)]
    assert set(angles_for_pose(visible[:10], 100, 100).values()) == {None}
    assert set(angles_for_pose(visible, 100, 100)) == {
        "knee_left", "knee_right", "elbow_left", "elbow_right", "hip_left", "hip_right",
        "shoulder_left", "shoulder_right", "trunk_inclination",
    }
    assert pose_quality(visible)["visible_fraction"] == 1


def test_pose_angles_velocities_motion_summary_and_balance_limitation():
    pose = [{"x": 0.5, "y": 0.5, "z": 0, "visibility": 1.0} for _ in range(33)]
    pose[23] = {"x": 0.4, "y": 0.7, "z": 0, "visibility": 1.0}
    pose[24] = {"x": 0.6, "y": 0.7, "z": 0, "visibility": 1.0}
    pose[25] = {"x": 0.4, "y": 0.8, "z": 0, "visibility": 1.0}
    pose[26] = {"x": 0.6, "y": 0.8, "z": 0, "visibility": 1.0}
    frames = [
        {"time_seconds": 0.0, "pose_landmarks": pose, "tracking_quality": {"visible_fraction": 1, "tracking_lost": False}},
        {"time_seconds": 1.0, "pose_landmarks": pose, "tracking_quality": {"visible_fraction": 1, "tracking_lost": False}},
    ]
    add_angles(frames, 640, 480)
    assert frames[0]["angular_velocity_degrees_per_second"]["knee_left"] is None
    assert frames[1]["angular_velocity_degrees_per_second"]["knee_left"] == 0
    summary = motion_summary(frames, "balance", 20)
    assert summary["processed_frames"] == 2
    assert summary["repetitions"] is None
    assert "normalized image coordinates" in summary["balance_note"]
    assert len(summary["pelvis_trajectory_normalized"]) == 2


def test_landmark_rows_and_holistic_overlay_handle_optional_groups():
    np = pytest.importorskip("numpy")
    pytest.importorskip("cv2")
    from types import SimpleNamespace
    rows = landmarks_to_rows([SimpleNamespace(x=0.2, y=0.3, z=-0.1, visibility=0.8, presence=0.7)])
    assert rows == [{"x": 0.2, "y": 0.3, "z": -0.1, "visibility": 0.8, "presence": 0.7}]
    frame = np.zeros((80, 120, 3), dtype=np.uint8)
    pose = [{"x": index / 33, "y": 0.5} for index in range(33)]
    overlay = draw_holistic_overlay(frame, pose, [{"x": 0.5, "y": 0.4}], [], [])
    assert overlay.shape == frame.shape
    assert np.any(overlay)


def test_jpeg_export_is_decodable_and_data_url_type_validation_is_strict():
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    payload = base64.b64decode(jpeg_base64(np.zeros((24, 32, 3), dtype=np.uint8)))
    decoded = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape == (24, 32, 3)
    with pytest.raises(ComputerVisionError, match="INVALID_IMAGE_DATA_URL"):
        decode_data_url("data:text/plain;base64," + base64.b64encode(b"x").decode(), "image", 10)


def test_motion_summary_ignores_missing_angles_and_reports_tracking_loss():
    frames = [
        {"time_seconds": 0, "tracking_quality": {"visible_fraction": 0.2, "tracking_lost": True},
         "angles_2d": {"knee_left": 20, "knee_right": 20}, "pose_landmarks": []},
        {"time_seconds": 1, "tracking_quality": {"visible_fraction": 0.8, "tracking_lost": False},
         "angles_2d": {"knee_left": 50, "knee_right": 40}, "angular_velocity_degrees_per_second": {"knee_left": 5},
         "pose_landmarks": []},
    ]
    result = motion_summary(frames, "squat", 20)
    assert result["tracking_loss_frames"] == 1
    assert result["range_of_motion_degrees_2d"]["knee_left"] == 30
    assert result["angular_velocity_degrees_per_second_2d"]["knee_left"]["max_abs_degrees_per_second"] == 5
    assert result["bilateral_rom_symmetry_percent"]["knee"] == pytest.approx(66.67)


def test_missing_model_assets_and_cached_model_lifecycles(tmp_path):
    from vigile.computer_vision import ComputerVisionError

    service = ComputerVisionService(tmp_path)
    for loader, code in (
        (service._load_oct, "OCT_MODEL_NOT_AVAILABLE"),
        (service._load_echo, "ECHONET_PERMISSION_NOT_VERIFIED"),
        (service._load_motion, "HOLISTIC_MODEL_ASSET_NOT_AVAILABLE"),
    ):
        with pytest.raises(ComputerVisionError, match=code):
            loader()
    oct_model = object()
    motion = (object(), type("Landmarker", (), {"close": lambda self: None})())
    service._models.update({"ocularvision": oct_model, "echovision": object(), "motionguard": motion})
    assert service._load_oct() is oct_model
    with pytest.raises(ComputerVisionError, match="ECHONET_PERMISSION_NOT_VERIFIED"):
        service._load_echo()
    assert service._load_motion() is motion
    service.close()
    assert "motionguard" not in service._models


def test_local_model_assets_must_match_pinned_hashes_before_loading(tmp_path):
    from vigile.computer_vision import ComputerVisionError

    oct_path = tmp_path / "oct" / "best_model.pth"
    motion_path = tmp_path / "motion" / "holistic_landmarker.task"
    oct_path.parent.mkdir(parents=True)
    motion_path.parent.mkdir(parents=True)
    oct_path.write_bytes(b"untrusted checkpoint")
    motion_path.write_bytes(b"untrusted task asset")
    service = ComputerVisionService(tmp_path)
    with pytest.raises(ComputerVisionError, match="OCT_MODEL_CHECKSUM_MISMATCH"):
        service._load_oct()
    with pytest.raises(ComputerVisionError, match="HOLISTIC_MODEL_CHECKSUM_MISMATCH"):
        service._load_motion()


def test_motion_model_close_failure_is_contained(tmp_path):
    class BadCloser:
        def close(self):
            raise RuntimeError("close failed")

    service = ComputerVisionService(tmp_path)
    service._models["motionguard"] = (None, BadCloser())
    service.close()
    assert "motionguard" not in service._models


def test_motion_status_covers_missing_dependency_and_last_error(tmp_path, monkeypatch):
    import vigile.computer_vision as module

    asset = tmp_path / "motion" / "holistic_landmarker.task"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"synthetic asset placeholder")
    service = ComputerVisionService(tmp_path)
    monkeypatch.setattr(module.util, "find_spec", lambda _name: None)
    assert service._mediapipe_status()["state"] == "DEPENDENCY_MISSING"
    monkeypatch.setattr(module.util, "find_spec", lambda _name: object())
    service._last_error["motionguard"] = "MODEL_LOAD_ERROR"
    assert service._mediapipe_status()["state"] == "MODEL_LOAD_ERROR"
    monkeypatch.setattr(module.metadata, "version", lambda _name: (_ for _ in ()).throw(module.metadata.PackageNotFoundError()))
    status = service._mediapipe_status()
    assert status["version"] == "0.10.21 (pinned)"


def test_oct_request_fails_fast_without_numpy_and_checks_declared_mime():
    import vigile.computer_vision as module

    valid = OCTRequest(image_data="data:image/png;base64," + base64.b64encode(b"x" * 64).decode())
    service = ComputerVisionService()
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(module, "np", None)
        with pytest.raises(ComputerVisionError, match="NUMPY_DEPENDENCY_MISSING"):
            service.analyze_oct(valid)

    stream = BytesIO()
    Image.new("RGB", (80, 80), "white").save(stream, format="JPEG")
    wrong_mime = OCTRequest(image_data="data:image/png;base64," + base64.b64encode(stream.getvalue()).decode())
    with pytest.raises(ComputerVisionError, match="OCT_IMAGE_MIME_FORMAT_MISMATCH"):
        service.analyze_oct(wrong_mime)


def test_video_request_validation_and_rejects_unsupported_filename_before_loading_model():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="SUPPORTED_VIDEO_DATA_URL_REQUIRED"):
        VideoRequest(video_data="data:text/plain;base64," + base64.b64encode(b"x" * 64).decode(), filename="clip.mp4")
    payload = "data:video/mp4;base64," + base64.b64encode(b"not a real video" * 5).decode()
    request = VideoRequest(video_data=payload, filename="clip.txt")
    with pytest.raises(ComputerVisionError, match="UNSUPPORTED_VIDEO_EXTENSION"):
        ComputerVisionService().analyze_motion(request)
    with pytest.raises(ComputerVisionError, match="ECHONET_PERMISSION_NOT_VERIFIED"):
        ComputerVisionService().analyze_echo(VideoRequest(video_data=payload, filename="clip.mp4"))


def test_data_url_empty_and_oct_unsupported_format_paths():
    with pytest.raises(ComputerVisionError, match="EMPTY_IMAGE_FILE"):
        decode_data_url("data:image/png;base64,", "image", 20)
    stream = BytesIO()
    Image.new("RGB", (80, 80), "white").save(stream, format="GIF")
    with pytest.raises(ComputerVisionError, match="UNSUPPORTED_OCT_IMAGE_FORMAT"):
        decode_oct_image(stream.getvalue())


def test_16_bit_oct_intensity_scaling_and_constant_range_rejection():
    np = pytest.importorskip("numpy")
    values = np.arange(64 * 80, dtype=np.uint16).reshape((64, 80))
    stream = BytesIO()
    Image.fromarray(values).save(stream, format="PNG")
    decoded, details = decode_oct_image(stream.getvalue())
    assert decoded.mode == "L"
    assert details["intensity"]["conversion"].startswith("16-bit grayscale")

    constant = BytesIO()
    Image.fromarray(np.full((64, 80), 1000, dtype=np.uint16)).save(constant, format="PNG")
    with pytest.raises(ComputerVisionError, match="OCT_IMAGE_INTENSITY_RANGE_INVALID"):
        decode_oct_image(constant.getvalue())


def test_jpeg_encoding_failure_and_video_export_size_guards(tmp_path, monkeypatch):
    import vigile.computer_vision as module
    np = pytest.importorskip("numpy")

    class BadEncoder:
        IMWRITE_JPEG_QUALITY = 1

        @staticmethod
        def imencode(*_args):
            return False, None

    monkeypatch.setattr(module, "cv2_module", lambda: BadEncoder)
    with pytest.raises(ComputerVisionError, match="RESULT_IMAGE_ENCODING_FAILED"):
        jpeg_base64(np.zeros((2, 2, 3), dtype=np.uint8))
    assert video_base64(None) is None
    assert video_base64(tmp_path / "missing.mp4") is None
    large = tmp_path / "large.mp4"
    with large.open("wb") as target:
        target.seek(MAX_EXPORT_VIDEO_BYTES)
        target.write(b"x")
    assert video_base64(large) is None


def test_holistic_overlay_draws_face_and_both_hands_and_low_confidence_trunk():
    np = pytest.importorskip("numpy")
    pytest.importorskip("cv2")
    from types import SimpleNamespace

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    face = [{"x": 0.5, "y": 0.5} for _ in range(292)]
    hand = [SimpleNamespace(x=0.25, y=0.75)]
    overlay = draw_holistic_overlay(frame, [], face, hand, hand)
    assert np.any(overlay)
    invisible = [{"x": 0.5, "y": 0.5, "visibility": 0.1} for _ in range(33)]
    assert angles_for_pose(invisible, 100, 100)["trunk_inclination"] is None


def test_permitted_real_checkpoints_load_and_accept_expected_tensor_shapes():
    torch = pytest.importorskip("torch")
    pytest.importorskip("mediapipe")
    from vigile.computer_vision import OCT_WEIGHTS, HOLISTIC_ASSET, ComputerVisionError
    if not (OCT_WEIGHTS.is_file() and HOLISTIC_ASSET.is_file()):
        pytest.skip("local model assets were not explicitly installed")
    torch.set_num_threads(min(4, torch.get_num_threads()))
    service = ComputerVisionService()
    try:
        oct_model = service._load_oct()
        with pytest.raises(ComputerVisionError, match="ECHONET_PERMISSION_NOT_VERIFIED"):
            service._load_echo()
        mp, landmarker = service._load_motion()
        with torch.inference_mode():
            oct_output = oct_model(torch.zeros(1, 1, 496, 768))
        assert tuple(oct_output.shape) == (1, 8, 496, 768)
        assert service.get_model_status()["modules"]["echovision"]["execution_enabled"] is False
        blank_rgb = np.zeros((120, 160, 3), dtype=np.uint8)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=blank_rgb)
        result = landmarker.detect_for_video(mp_image, 0)
        assert result is not None
    finally:
        service.close()


def test_real_holistic_video_pipeline_reports_tracking_loss_on_blank_clip(tmp_path):
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    pytest.importorskip("mediapipe")
    from vigile.computer_vision import HOLISTIC_ASSET, VideoRequest
    if not HOLISTIC_ASSET.is_file():
        pytest.skip("local Holistic model asset was not explicitly installed")
    input_path = tmp_path / "blank.mp4"
    writer = cv2.VideoWriter(str(input_path), cv2.VideoWriter_fourcc(*"mp4v"), 6, (160, 120))
    if not writer.isOpened():
        pytest.skip("this OpenCV build has no MP4 video encoder")
    for _ in range(4):
        writer.write(np.zeros((120, 160, 3), dtype=np.uint8))
    writer.release()
    encoded = base64.b64encode(input_path.read_bytes()).decode("ascii")
    request = VideoRequest(video_data="data:video/mp4;base64," + encoded, filename="blank.mp4", frame_stride=1)
    service = ComputerVisionService()
    try:
        result = service.analyze_motion(request)
    finally:
        service.close()
    assert result["analysis_performed"] is True
    assert result["summary"]["processed_frames"] == 4
    assert result["summary"]["tracking_loss_frames"] == 4
    assert result["summary"]["repetitions"] == 0
    assert result["overlay_video_exported"] is True
    assert result["overlay_video_base64"]


def test_echo_pipeline_is_blocked_until_rights_are_verified():
    from vigile.computer_vision import VideoRequest, ComputerVisionError
    encoded = base64.b64encode(b"x" * 64).decode("ascii")
    request = VideoRequest(video_data="data:video/mp4;base64," + encoded, filename="synthetic.mp4", confirm_a4c=True)
    service = ComputerVisionService()
    with pytest.raises(ComputerVisionError, match="ECHONET_PERMISSION_NOT_VERIFIED"):
        service.analyze_echo(request)


def test_real_oct_inference_export_smoke_uses_synthetic_nonmedical_pixels():
    pytest.importorskip("numpy")
    pytest.importorskip("torch")
    pytest.importorskip("torchvision")
    from vigile.computer_vision import OCT_WEIGHTS, OCTRequest
    if not OCT_WEIGHTS.is_file():
        pytest.skip("local OCT checkpoint was not explicitly installed")
    # A deterministic grayscale gradient verifies the real checkpoint's IO path;
    # this is not an OCT sample and has no clinical meaning.
    import numpy as np
    pixels = np.tile(np.arange(768, dtype=np.uint8), (496, 1))
    request = OCTRequest(image_data=data_url(Image.fromarray(pixels, mode="L")), pixel_spacing_um=None)
    result = ComputerVisionService().analyze_oct(request)
    assert result["analysis_performed"] is True
    assert len(result["layers"]) == 7
    assert len(result["boundaries_px"]) == 7
    assert len(result["retinal_span_profile_px"]) == 768
    assert result["image"]["pixel_spacing_um"] is None
    assert result["mask_png_base64"] and result["overlay_png_base64"]
