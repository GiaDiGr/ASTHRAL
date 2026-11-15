import math

import numpy as np
import pytest

from vigile.computer_vision_metrics import (
    box_iou_xyxy,
    classification_metrics,
    detection_metrics,
    segmentation_metrics,
)


def test_segmentation_perfect_masks_include_background_by_default():
    truth = np.array([[0, 1, 1], [0, 2, 2]], dtype=np.uint8)
    result = segmentation_metrics(truth, truth)
    assert result["pixel_accuracy_percent"] == 100
    assert result["macro_dice_percent"] == 100
    assert result["macro_iou_percent"] == 100
    assert set(result["labels"]) == {"0", "1", "2"}
    assert result["ground_truth_is_required"] is True


def test_segmentation_foreground_only_and_explicit_absent_class():
    truth = np.array([[0, 1], [0, 1]], dtype=np.uint8)
    prediction = np.array([[0, 1], [1, 0]], dtype=np.uint8)
    result = segmentation_metrics(truth, prediction, labels=[1, 3], ignore_label=0)
    assert result["pixels_evaluated"] == 2
    assert result["pixel_accuracy_percent"] == 50
    assert result["labels"]["1"]["dice"] == pytest.approx(2 / 3)
    assert result["labels"]["3"]["dice"] is None


@pytest.mark.parametrize(
    ("truth", "prediction", "message"),
    [
        (np.zeros((2, 2)), np.zeros((3, 2)), "MASK_SHAPES_MUST_MATCH"),
        (np.array([]), np.array([]), "MASK_SHAPES_MUST_MATCH"),
        (np.array([[0.1]]), np.array([[0.1]]), "MASK_LABELS_MUST_BE_FINITE_INTEGERS"),
        (np.array([[np.nan]]), np.array([[0]]), "MASK_LABELS_MUST_BE_FINITE_INTEGERS"),
        (np.array([[-1]]), np.array([[0]]), "MASK_LABELS_MUST_BE_NONNEGATIVE"),
    ],
)
def test_segmentation_rejects_malformed_masks(truth, prediction, message):
    with pytest.raises(ValueError, match=message):
        segmentation_metrics(truth, prediction)


def test_segmentation_rejects_empty_evaluation_region_and_bad_labels():
    with pytest.raises(ValueError, match="NO_PIXELS_REMAIN"):
        segmentation_metrics(np.zeros((2, 2), dtype=int), np.zeros((2, 2), dtype=int), ignore_label=0)
    for labels in ([], [1, 1], [-1], [1.0]):
        with pytest.raises(ValueError, match="EVALUATION_LABELS_INVALID"):
            segmentation_metrics(np.ones((2, 2), dtype=int), np.ones((2, 2), dtype=int), labels=labels)


def test_segmentation_randomized_identity_invariant_for_many_shapes():
    rng = np.random.default_rng(20261114)
    for height in range(1, 8):
        for width in range(1, 8):
            mask = rng.integers(0, 5, size=(height, width), dtype=np.uint8)
            result = segmentation_metrics(mask, mask)
            assert result["pixel_accuracy"] == 1
            assert result["macro_dice"] == 1
            assert result["macro_iou"] == 1


def test_classification_perfect_threshold_metrics_and_auc():
    result = classification_metrics([0, 0, 1, 1], [0.05, 0.2, 0.8, 0.99])
    assert result["accuracy_percent"] == 100
    assert result["precision_percent"] == 100
    assert result["sensitivity_percent"] == 100
    assert result["specificity_percent"] == 100
    assert result["f1_percent"] == 100
    assert result["auroc_percent"] == 100


def test_classification_handles_tied_scores_and_undefined_auc():
    tied = classification_metrics([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5])
    assert tied["auroc"] == 0.5
    single_class = classification_metrics([1, 1], [0.2, 0.9])
    assert single_class["specificity"] is None
    assert single_class["auroc"] is None
    assert single_class["specificity_percent"] is None


@pytest.mark.parametrize(
    ("labels", "scores", "threshold", "message"),
    [
        ([], [], 0.5, "LABELS_AND_SCORES"),
        ([0], [], 0.5, "LABELS_AND_SCORES"),
        ([2], [0.1], 0.5, "LABELS_MUST_BE_BINARY"),
        ([0, 1], [0.1], 0.5, "LABELS_AND_SCORES"),
        ([0, 1], [math.nan, 0.8], 0.5, "SCORES_AND_THRESHOLD"),
        ([0, 1], [-0.1, 0.8], 0.5, "SCORES_AND_THRESHOLD"),
        ([0, 1], [0.1, 0.8], 1.1, "SCORES_AND_THRESHOLD"),
    ],
)
def test_classification_rejects_bad_inputs(labels, scores, threshold, message):
    with pytest.raises(ValueError, match=message):
        classification_metrics(labels, scores, threshold=threshold)


def test_classification_empty_positive_predictions_leave_precision_undefined():
    result = classification_metrics([0, 0], [0.1, 0.2])
    assert result["precision"] is None
    assert result["sensitivity"] is None
    assert result["specificity"] == 1
    assert result["f1"] is None


def test_box_iou_known_overlap_and_disjoint_boxes():
    assert box_iou_xyxy([0, 0, 2, 2], [1, 1, 3, 3]) == pytest.approx(1 / 7)
    assert box_iou_xyxy([0, 0, 1, 1], [2, 2, 3, 3]) == 0
    assert box_iou_xyxy([0, 0, 3, 3], [0, 0, 3, 3]) == 1


@pytest.mark.parametrize("box", [[0, 0, 0, 1], [0, 2, 1, 1], [0, 0, math.inf, 1], [0, 1, 1]])
def test_box_iou_rejects_invalid_boxes(box):
    with pytest.raises(ValueError, match="BOX_COORDINATES_INVALID"):
        box_iou_xyxy(box, [0, 0, 1, 1])


def test_detection_exact_boxes_and_negative_images_are_counted():
    truth = [{"image_id": "a", "box_xyxy": [0, 0, 10, 10]}]
    predictions = [
        {"image_id": "a", "box_xyxy": [0, 0, 10, 10], "score": 0.99},
        {"image_id": "negative", "box_xyxy": [2, 2, 4, 4], "score": 0.4},
    ]
    result = detection_metrics(truth, predictions, ["a", "negative"])
    assert result["map50_percent"] == 100
    assert result["map50_95_percent"] == 100
    assert result["precision_at_iou50_percent"] == 50
    assert result["recall_at_iou50_percent"] == 100
    assert result["negative_images_counted"] is True


def test_detection_duplicate_and_missed_ground_truth_reduce_scores():
    truth = [
        {"image_id": "a", "box_xyxy": [0, 0, 10, 10]},
        {"image_id": "a", "box_xyxy": [20, 20, 30, 30]},
    ]
    predictions = [
        {"image_id": "a", "box_xyxy": [0, 0, 10, 10], "score": 0.9},
        {"image_id": "a", "box_xyxy": [0, 0, 10, 10], "score": 0.8},
    ]
    result = detection_metrics(truth, predictions, ["a"])
    assert result["map50_percent"] < 100
    assert result["recall_at_iou50_percent"] == 50
    assert result["precision_at_iou50_percent"] == 50


def test_detection_no_ground_truth_returns_undefined_ap_and_counts_false_positives():
    prediction = [{"image_id": "negative", "box_xyxy": [0, 0, 1, 1], "score": 0.7}]
    result = detection_metrics([], prediction, ["negative"])
    assert result["map50"] is None
    assert result["precision_at_iou50"] == 0
    assert result["recall_at_iou50"] is None


def test_detection_without_predictions_has_zero_ap_and_no_defined_precision():
    truth = [{"image_id": "a", "box_xyxy": [0, 0, 1, 1]}]
    result = detection_metrics(truth, [], ["a"])
    assert result["map50"] == 0
    assert result["precision_at_iou50"] is None
    assert result["recall_at_iou50"] == 0


@pytest.mark.parametrize(
    ("truth", "predictions", "image_ids", "message"),
    [
        ([], [], [], "IMAGE_IDS_MUST_BE_UNIQUE"),
        ([], [], ["a", "a"], "IMAGE_IDS_MUST_BE_UNIQUE"),
        ([{"image_id": "missing", "box_xyxy": [0, 0, 1, 1]}], [], ["a"], "BOX_IMAGE_ID"),
        ([], [{"image_id": "a", "box_xyxy": [0, 0, 1, 1], "score": 1.1}], ["a"], "DETECTION_SCORE_INVALID"),
        ([], [], ["a"], "IOU_THRESHOLDS_INVALID"),
    ],
)
def test_detection_rejects_bad_evaluation_records(truth, predictions, image_ids, message):
    thresholds = [] if message == "IOU_THRESHOLDS_INVALID" else (0.5,)
    with pytest.raises(ValueError, match=message):
        detection_metrics(truth, predictions, image_ids, iou_thresholds=thresholds)


def test_detection_thresholds_and_iou_match_known_geometry():
    truth = [{"image_id": "a", "box_xyxy": [0, 0, 10, 10]}]
    prediction = [{"image_id": "a", "box_xyxy": [0, 0, 5, 10], "score": 0.8}]
    result = detection_metrics(truth, prediction, ["a"], iou_thresholds=[0.5, 0.6])
    assert result["average_precision_by_iou"][0]["average_precision_101_point"] == 1
    assert result["average_precision_by_iou"][1]["average_precision_101_point"] == 0
    assert result["map50_95_percent"] == 50
