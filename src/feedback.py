from datetime import datetime, timezone
from typing import List

import inference
import storage
from schemas import MissingFoodRequest, RemoveRequest


def _polygon_to_yolo_line(class_id: int, polygon: List[List[float]]) -> str:
    """Convert [[x,y],...] → YOLO segmentation line string."""
    coords = " ".join(f"{x:.5f} {y:.5f}" for x, y in polygon)
    return f"{class_id} {coords}"


def handle_remove(req: RemoveRequest) -> dict:
    class_names_lower = [c.lower() for c in inference.CLASS_NAMES]
    class_id = class_names_lower.index(req.original_class.lower()) if req.original_class.lower() in class_names_lower else -1

    yolo_labels = []
    if req.mask_polygon and class_id != -1:
        yolo_labels.append(_polygon_to_yolo_line(class_id, req.mask_polygon))

    annotation = {
        "image_id": req.image_id,
        "scenario": "B_false_positive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "yolo_labels": yolo_labels,
        "meta": {
            "detection_id": req.detection_id,
            "removed_class": req.original_class,
            "removed_polygon": req.mask_polygon,
            "action": "mark_as_confirmed_negative_region",
        },
    }
    ann_id = f"{req.image_id}_B_{req.detection_id[:8]}"
    storage.save_annotation(ann_id, annotation)
    return {
        "status": "saved",
        "annotation_id": ann_id,
        "removed_class": req.original_class,
        "feedback_total": storage.count_feedback_items(),
        "message": f"Deteksi '{req.original_class}' deleted and stored as a negative sample.",
    }


def _normalize_food_name(raw_name: str) -> str:
    cleaned = raw_name.strip().lower()
    return "_".join(cleaned.split())


def handle_missing(req: MissingFoodRequest) -> dict:
    normalized_name = _normalize_food_name(req.food_name)
    class_names_lower = [c.lower() for c in inference.CLASS_NAMES]
    is_existing = normalized_name in class_names_lower
    class_id = class_names_lower.index(normalized_name) if is_existing else -1

    annotation = {
        "image_id": req.image_id,
        "scenario": "C_false_negative",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "yolo_labels": [],
        "meta": {
            "raw_user_input": req.food_name,
            "class_name": normalized_name,
            "class_id": class_id,
            "is_new_class": not is_existing,
            "tap_point": {"x": req.tap_x, "y": req.tap_y},
            "sam2_pending": True,
        },
    }

    ann_id = f"{req.image_id}_C_{normalized_name}"
    storage.save_annotation(ann_id, annotation)

    return {
        "status": "saved",
        "annotation_id": ann_id,
        "class_name": normalized_name,
        "is_new_class": not is_existing,
        "sam2_pending": True,
        "feedback_total": storage.count_feedback_items(),
        "message": f"'{req.food_name}' Successfully recorded for the model update!",
    }