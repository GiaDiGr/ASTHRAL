import base64
from io import BytesIO

import pytest
from PIL import Image

from vigile.computer_vision import (
    ComputerVisionService,
    ComputerVisionError,
    count_repetitions,
    decode_data_url,
    decode_oct_image,
    extract_region_boundaries,
    oct_input,
    projected_angle,
    transform_frame,
    inverse_transform_frame,
    unletterbox_mask,
)


def data_url(image: Image.Image) -> str:
    stream = BytesIO()
    image.save(stream, format="PNG")
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode("ascii")


def test_registry_reports_missing_weights_without_faking_availability(tmp_path):
    modules = ComputerVisionService(tmp_path).get_model_status()["modules"]
    assert set(modules) == {"skinguard", "ocularvision", "echovision", "motionguard"}
    assert modules["skinguard"]["state"] == "MODEL_NOT_CONFIGURED"
    for name in ("ocularvision", "echovision", "motionguard"):
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


def test_real_checkpoints_load_and_accept_expected_tensor_shapes():
    np = pytest.importorskip("numpy")
    torch = pytest.importorskip("torch")
    pytest.importorskip("torchvision")
    pytest.importorskip("mediapipe")
    from vigile.computer_vision import OCT_WEIGHTS, ECHO_WEIGHTS, HOLISTIC_ASSET
    if not (OCT_WEIGHTS.is_file() and ECHO_WEIGHTS.is_file() and HOLISTIC_ASSET.is_file()):
        pytest.skip("local model assets were not explicitly installed")
    torch.set_num_threads(min(4, torch.get_num_threads()))
    service = ComputerVisionService()
    try:
        oct_model = service._load_oct()
        echo_model = service._load_echo()
        mp, landmarker = service._load_motion()
        with torch.inference_mode():
            oct_output = oct_model(torch.zeros(1, 1, 496, 768))
            echo_output = echo_model(torch.zeros(1, 3, 112, 112))["out"]
        assert tuple(oct_output.shape) == (1, 8, 496, 768)
        assert tuple(echo_output.shape) == (1, 1, 112, 112)
        from vigile.computer_vision import predict_echo_frame
        mask, overlay = predict_echo_frame(echo_model, np.zeros((64, 96, 3), dtype=np.uint8))
        assert mask.shape == (64, 96) and overlay.shape == (64, 96, 3)
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


def test_real_echo_video_pipeline_exports_masks_for_synthetic_nonmedical_clip(tmp_path):
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    pytest.importorskip("torch")
    pytest.importorskip("torchvision")
    from vigile.computer_vision import ECHO_WEIGHTS, VideoRequest
    if not ECHO_WEIGHTS.is_file():
        pytest.skip("local EchoNet checkpoint was not explicitly installed")
    input_path = tmp_path / "synthetic.mp4"
    writer = cv2.VideoWriter(str(input_path), cv2.VideoWriter_fourcc(*"mp4v"), 4, (160, 120))
    if not writer.isOpened():
        pytest.skip("this OpenCV build has no MP4 video encoder")
    for index in range(2):
        frame = np.full((120, 160, 3), 30 + index * 20, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    encoded = base64.b64encode(input_path.read_bytes()).decode("ascii")
    request = VideoRequest(
        video_data="data:video/mp4;base64," + encoded,
        filename="synthetic.mp4",
        frame_stride=1,
        confirm_a4c=True,
    )
    service = ComputerVisionService()
    try:
        result = service.analyze_echo(request)
    finally:
        service.close()
    assert result["analysis_performed"] is True
    assert result["video"]["decoded_frames"] == 2
    assert len(result["sampled_frames"]) == 2
    assert all(frame["mask_shape"] == [120, 160] for frame in result["sampled_frames"])
    assert result["mask_png_base64"] and result["overlay_frame_jpeg_base64"]
    assert result["overlay_video_exported"] is True
    assert result["overlay_video_base64"]
    assert any("No ejection fraction" in item for item in result["limitations"])


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
