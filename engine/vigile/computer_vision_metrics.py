"""Metrics for evaluating predictions against labelled held-out references.

These functions do not create labels or validate a model. Callers must provide
predictions and ground truth from a valid, provenance-documented evaluation
split. Percent fields are convenience representations of the same fractions.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence


def _numpy():
    try:
        import numpy as np
    except ImportError as exc:  # Keep the base ASTHRAL portal usable without vision extras.
        raise RuntimeError("NUMPY_REQUIRED_FOR_MASK_METRICS") from exc
    return np


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _percent(value: float | None) -> float | None:
    return round(value * 100, 3) if value is not None else None


def segmentation_metrics(
    ground_truth,
    prediction,
    *,
    labels: Sequence[int] | None = None,
    ignore_label: int | None = None,
) -> dict:
    """Return pixel accuracy and per-label Dice/IoU for same-shaped label masks.

    A class absent from both masks is omitted by default, so absent classes
    cannot inflate the macro score. If ``labels`` is explicit, absent classes
    have ``None`` metrics and still remain visible in the returned class map.
    """
    np = _numpy()
    truth, predicted = np.asarray(ground_truth), np.asarray(prediction)
    if truth.ndim < 1 or predicted.shape != truth.shape or truth.size == 0:
        raise ValueError("MASK_SHAPES_MUST_MATCH_AND_BE_NONEMPTY")
    for array in (truth, predicted):
        if not np.issubdtype(array.dtype, np.integer):
            if not np.issubdtype(array.dtype, np.number) or not np.isfinite(array).all() or not np.equal(array, np.floor(array)).all():
                raise ValueError("MASK_LABELS_MUST_BE_FINITE_INTEGERS")
        if np.any(array < 0):
            raise ValueError("MASK_LABELS_MUST_BE_NONNEGATIVE")
    if labels is None:
        class_ids = sorted((set(np.unique(truth).tolist()) | set(np.unique(predicted).tolist())) - ({ignore_label} if ignore_label is not None else set()))
    else:
        if not labels or len(set(labels)) != len(labels) or any(not isinstance(label, int) or label < 0 for label in labels):
            raise ValueError("EVALUATION_LABELS_INVALID")
        class_ids = list(labels)
    evaluated = (truth != ignore_label) if ignore_label is not None else np.ones(truth.shape, dtype=bool)
    total = int(np.count_nonzero(evaluated))
    if total == 0:
        raise ValueError("NO_PIXELS_REMAIN_AFTER_IGNORE_LABEL")
    correct = int(np.count_nonzero((truth == predicted) & evaluated))
    per_class = {}
    dices, ious = [], []
    for label in class_ids:
        actual = (truth == label) & evaluated
        guessed = (predicted == label) & evaluated
        tp = int(np.count_nonzero(actual & guessed))
        fp = int(np.count_nonzero(~actual & guessed & evaluated))
        fn = int(np.count_nonzero(actual & ~guessed))
        denominator = 2 * tp + fp + fn
        union = tp + fp + fn
        dice = round((2 * tp / denominator), 6) if denominator else None
        iou = round((tp / union), 6) if union else None
        if dice is not None:
            dices.append(dice)
        if iou is not None:
            ious.append(iou)
        per_class[str(label)] = {
            "true_positive_pixels": tp,
            "false_positive_pixels": fp,
            "false_negative_pixels": fn,
            "dice": dice,
            "dice_percent": _percent(dice),
            "iou": iou,
            "iou_percent": _percent(iou),
            "precision": _ratio(tp, tp + fp),
            "sensitivity": _ratio(tp, tp + fn),
        }
    accuracy = round(correct / total, 6)
    return {
        "task": "SEMANTIC_SEGMENTATION",
        "pixels_evaluated": total,
        "ignore_label": ignore_label,
        "labels": per_class,
        "macro_dice": round(sum(dices) / len(dices), 6) if dices else None,
        "macro_dice_percent": _percent(sum(dices) / len(dices)) if dices else None,
        "macro_iou": round(sum(ious) / len(ious), 6) if ious else None,
        "macro_iou_percent": _percent(sum(ious) / len(ious)) if ious else None,
        "pixel_accuracy": accuracy,
        "pixel_accuracy_percent": _percent(accuracy),
        "ground_truth_is_required": True,
    }


def _binary_auc(labels: list[int], scores: list[float]) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    order = sorted(range(len(scores)), key=scores.__getitem__)
    positive_rank_sum = 0.0
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and scores[order[end]] == scores[order[index]]:
            end += 1
        average_rank = ((index + 1) + end) / 2
        positive_rank_sum += sum(labels[order[pos]] for pos in range(index, end)) * average_rank
        index = end
    auc = (positive_rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
    return round(auc, 6)


def classification_metrics(labels: Iterable[int], scores: Iterable[float], *, threshold: float = 0.5) -> dict:
    """Return binary classification metrics from reference labels and scores."""
    truth, confidence = list(labels), [float(score) for score in scores]
    if not truth or len(truth) != len(confidence):
        raise ValueError("LABELS_AND_SCORES_MUST_HAVE_EQUAL_NONZERO_LENGTH")
    if any(value not in (0, 1, False, True) for value in truth):
        raise ValueError("CLASSIFICATION_LABELS_MUST_BE_BINARY")
    if not math.isfinite(threshold) or not 0 <= threshold <= 1 or any(not math.isfinite(score) or not 0 <= score <= 1 for score in confidence):
        raise ValueError("CLASSIFICATION_SCORES_AND_THRESHOLD_MUST_BE_IN_0_1")
    truth = [int(value) for value in truth]
    predicted = [int(score >= threshold) for score in confidence]
    tp = sum(actual == 1 and guess == 1 for actual, guess in zip(truth, predicted))
    fp = sum(actual == 0 and guess == 1 for actual, guess in zip(truth, predicted))
    fn = sum(actual == 1 and guess == 0 for actual, guess in zip(truth, predicted))
    tn = sum(actual == 0 and guess == 0 for actual, guess in zip(truth, predicted))
    accuracy = (tp + tn) / len(truth)
    precision = _ratio(tp, tp + fp)
    sensitivity = _ratio(tp, tp + fn)
    specificity = _ratio(tn, tn + fp)
    f1 = _ratio(2 * tp, 2 * tp + fp + fn)
    auc = _binary_auc(truth, confidence)
    return {
        "task": "BINARY_CLASSIFICATION",
        "samples": len(truth),
        "threshold": threshold,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "accuracy": round(accuracy, 6),
        "accuracy_percent": _percent(accuracy),
        "precision": precision,
        "precision_percent": _percent(precision),
        "sensitivity": sensitivity,
        "sensitivity_percent": _percent(sensitivity),
        "specificity": specificity,
        "specificity_percent": _percent(specificity),
        "f1": f1,
        "f1_percent": _percent(f1),
        "auroc": auc,
        "auroc_percent": _percent(auc),
        "ground_truth_is_required": True,
    }


def box_iou_xyxy(first: Sequence[float], second: Sequence[float]) -> float:
    """Intersection over union for two finite ``[x1,y1,x2,y2]`` boxes."""
    a, b = list(first), list(second)
    if len(a) != 4 or len(b) != 4 or any(not math.isfinite(float(v)) for v in a + b):
        raise ValueError("BOX_COORDINATES_INVALID")
    if a[2] <= a[0] or a[3] <= a[1] or b[2] <= b[0] or b[3] <= b[1]:
        raise ValueError("BOX_COORDINATES_INVALID")
    width = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    height = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = width * height
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return intersection / (area_a + area_b - intersection)


def _ap101(recall: list[float], precision: list[float]) -> float | None:
    if not recall:
        return 0.0
    return round(sum(max((p for r, p in zip(recall, precision) if r >= target), default=0.0) for target in (i / 100 for i in range(101))) / 101, 6)


def detection_metrics(
    ground_truth: Sequence[dict],
    predictions: Sequence[dict],
    image_ids: Sequence[str],
    *,
    iou_thresholds: Sequence[float] = tuple(i / 100 for i in range(50, 96, 5)),
) -> dict:
    """Evaluate one-class detections using confidence ranking and 101-point AP.

    Each box row has ``image_id`` and ``box_xyxy``; predictions also have
    ``score``. ``image_ids`` must include negative images so their false
    detections count. Results are meaningful only for a valid held-out split.
    """
    ids = list(image_ids)
    if not ids or len(set(ids)) != len(ids) or any(not isinstance(item, str) or not item for item in ids):
        raise ValueError("IMAGE_IDS_MUST_BE_UNIQUE_AND_NONEMPTY")
    id_set = set(ids)
    truths, predicted = list(ground_truth), list(predictions)
    if any(row.get("image_id") not in id_set for row in truths + predicted):
        raise ValueError("BOX_IMAGE_ID_NOT_IN_EVALUATION_SPLIT")
    if not iou_thresholds or any(not math.isfinite(float(value)) or not 0 < value <= 1 for value in iou_thresholds):
        raise ValueError("IOU_THRESHOLDS_INVALID")
    for row in truths:
        box_iou_xyxy(row.get("box_xyxy", []), row.get("box_xyxy", []))
    for row in predicted:
        box_iou_xyxy(row.get("box_xyxy", []), row.get("box_xyxy", []))
        if not math.isfinite(float(row.get("score", math.nan))) or not 0 <= float(row["score"]) <= 1:
            raise ValueError("DETECTION_SCORE_INVALID")
    total_truth = len(truths)
    ordered = sorted(predicted, key=lambda row: float(row["score"]), reverse=True)
    threshold_rows = []
    for threshold in iou_thresholds:
        used: set[int] = set()
        tp_flags, fp_flags = [], []
        for row in ordered:
            candidates = [(box_iou_xyxy(row["box_xyxy"], truth["box_xyxy"]), index)
                          for index, truth in enumerate(truths)
                          if index not in used and truth["image_id"] == row["image_id"]]
            best_iou, best_index = max(candidates, default=(0.0, -1))
            if best_index >= 0 and best_iou >= threshold:
                used.add(best_index)
                tp_flags.append(1)
                fp_flags.append(0)
            else:
                tp_flags.append(0)
                fp_flags.append(1)
        cumulative_tp = cumulative_fp = 0
        recalls, precisions = [], []
        for tp, fp in zip(tp_flags, fp_flags):
            cumulative_tp += tp
            cumulative_fp += fp
            recalls.append(cumulative_tp / total_truth if total_truth else 0.0)
            precisions.append(cumulative_tp / (cumulative_tp + cumulative_fp))
        ap = _ap101(recalls, precisions) if total_truth else None
        threshold_rows.append({"iou_threshold": float(threshold), "average_precision_101_point": ap})
    first = threshold_rows[0]["average_precision_101_point"] if threshold_rows else None
    aps = [row["average_precision_101_point"] for row in threshold_rows if row["average_precision_101_point"] is not None]
    matched: set[int] = set()
    tp_flags, fp_flags = [], []
    for row in ordered:
        candidates = [(box_iou_xyxy(row["box_xyxy"], truth["box_xyxy"]), index)
                      for index, truth in enumerate(truths)
                      if index not in matched and truth["image_id"] == row["image_id"]]
        best_iou, best_index = max(candidates, default=(0.0, -1))
        if best_index >= 0 and best_iou >= iou_thresholds[0]:
            matched.add(best_index)
            tp_flags.append(1)
            fp_flags.append(0)
        else:
            tp_flags.append(0)
            fp_flags.append(1)
    tp, fp, fn = sum(tp_flags), sum(fp_flags), max(0, total_truth - sum(tp_flags))
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = _ratio(2 * tp, 2 * tp + fp + fn)
    return {
        "task": "SINGLE_CLASS_OBJECT_DETECTION",
        "images": len(ids),
        "ground_truth_boxes": total_truth,
        "prediction_boxes": len(predicted),
        "iou_thresholds": [float(value) for value in iou_thresholds],
        "average_precision_by_iou": threshold_rows,
        "map50": first,
        "map50_percent": _percent(first),
        "map50_95": round(sum(aps) / len(aps), 6) if aps else None,
        "map50_95_percent": _percent(sum(aps) / len(aps)) if aps else None,
        "precision_at_iou50": precision,
        "precision_at_iou50_percent": _percent(precision),
        "recall_at_iou50": recall,
        "recall_at_iou50_percent": _percent(recall),
        "f1_at_iou50": f1,
        "f1_at_iou50_percent": _percent(f1),
        "ground_truth_is_required": True,
        "negative_images_counted": True,
    }
