import time
import uuid
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image
from ultralytics import YOLO

from schemas import SegmentedFood
import io

MODEL_PATH  = Path(__file__).parent.parent / "models" / "production" / "yolov11l_seg_v2_final.pt"
CONF_THRESH = 0.25
IOU_THRESH  = 0.45
IMG_SIZE    = 640
DEVICE      = "cpu"   # using CUDA in EC2 GPU

# Default gram / portion detected
DEFAULT_GRAMS = {
    "beef": 100.0, "chicken": 100.0, "egg": 60.0,  "fish": 100.0,
    "fruit": 150.0, "noodles": 150.0, "pork": 100.0, "rice": 200.0,
    "sambal": 20.0, "shrimp": 100.0,  "squid": 100.0, "tempeh": 100.0,
    "tofu": 100.0,  "vegetable": 150.0,
}

# Default serving style
DEFAULT_SERVING_STYLE = {
    "beef": "fried", "chicken": "fried", "egg": "fried", "fish": "fried",
    "pork": "fried", "shrimp": "fried", "squid": "fried",
    "rice": "boiled", "noodles": "boiled", "tempeh": "fried", "tofu": "fried",
    "vegetable": "steamed", "fruit": "raw", "sambal": "raw",
}

print(f"[inference] Loading model {MODEL_PATH} ...")
_model      = YOLO(str(MODEL_PATH))
CLASS_NAMES = list(_model.names.values())
print(f"[inference] Ready — {len(CLASS_NAMES)} classes")


def predict(image: Image.Image) -> Tuple[List[SegmentedFood], float]:
    t0      = time.perf_counter()
    results = _model.predict(
        source=image, conf=CONF_THRESH, iou=IOU_THRESH,
        imgsz=IMG_SIZE, device=DEVICE, verbose=False,
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    result     = results[0]

    if result.boxes is None or len(result.boxes) == 0:
        return [], elapsed_ms

    img_w, img_h = image.size
    img_area     = img_w * img_h
    masks = result.masks.xyn if result.masks is not None else [None] * len(result.boxes)
    detected: List[SegmentedFood] = []

    for box, cls_t, conf_t, mask_xy in zip(result.boxes, result.boxes.cls, result.boxes.conf, masks):
        class_id   = int(cls_t.item())
        class_name = CLASS_NAMES[class_id]
        confidence = round(float(conf_t.item()), 4)

        bbox_coords = [round(float(v), 2) for v in box.xyxy[0].tolist()]

        polygon: List[List[float]] = []
        mask_area_ratio = 0.0
        if mask_xy is not None and len(mask_xy) >= 3:
            pts = mask_xy.tolist()
            polygon = [[round(x, 5), round(y, 5)] for x, y in pts]
            
            arr  = np.asarray(pts)
            x, y = arr[:, 0] * img_w, arr[:, 1] * img_h
            area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
            mask_area_ratio = round(float(area / img_area), 6) if img_area > 0 else 0.0

        detected.append(SegmentedFood(
            detection_id=str(uuid.uuid4()),
            class_name=class_name,
            confidence=confidence,
            bbox=bbox_coords,
            mask_area_ratio=mask_area_ratio,
            mask_polygon=polygon,
            estimated_grams=DEFAULT_GRAMS.get(class_name, 100.0),
            serving_style=DEFAULT_SERVING_STYLE.get(class_name, "fried"),
        ))

    return detected, elapsed_ms

def get_model_info() -> dict:
    return {
        "model_path": str(MODEL_PATH),
        "classes":    CLASS_NAMES,
        "conf":       CONF_THRESH,
        "iou":        IOU_THRESH,
        "device":     DEVICE,
    }

def run_pipeline(image_bytes: bytes) -> Tuple[List[SegmentedFood], float]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return predict(image)