"""
storage.py — Storage abstraction: S3 if available, falling back to local storage.
All other modules import from here, rather than directly using boto3.

Local Directory:
  /tmp/nutrivision/
  ├── feedback/
  │   ├── images/       → image from /predict
  │   └── annotations/  → JSON annotation form /feedback/*
  ├── users/            → profile per device_id (device_id.json)
  └── diary/
      └── {device_id}/
          └── {YYYY-MM-DD}.json  → list DiaryEntry
"""

import json
import os
from pathlib import Path
from typing import Optional

_BASE           = Path(os.getenv("STORAGE_LOCAL_DIR", "/tmp/nutrivision"))
_IMAGES_DIR     = _BASE / "feedback" / "images"
_ANNOTATIONS_DIR = _BASE / "feedback" / "annotations"
_USERS_DIR      = _BASE / "users"
_DIARY_DIR      = _BASE / "diary"

for _d in (_IMAGES_DIR, _ANNOTATIONS_DIR, _USERS_DIR, _DIARY_DIR):
    _d.mkdir(parents=True, exist_ok=True)


_S3_BUCKET = os.getenv("S3_FEEDBACK_BUCKET", "")
_s3_client = None

def _s3():
    global _s3_client
    if _s3_client is None and _S3_BUCKET:
        try:
            import boto3
            _s3_client = boto3.client("s3")
        except Exception as e:
            print(f"[storage] boto3 not ready: {e}")
    return _s3_client

def _s3_upload(key: str, body: bytes, content_type: str):
    """Upload to S3"""
    client = _s3()
    if not client:
        return
    try:
        client.put_object(
            Bucket=_S3_BUCKET, Key=key,
            Body=body, ContentType=content_type,
        )
    except Exception as e:
        print(f"[storage] S3 upload failed ({key}): {e}")


# ── Feedback: Image & Annotation ──────────────────────────────────────────────

def save_image(image_id: str, image_bytes: bytes) -> str:
    path = _IMAGES_DIR / f"{image_id}.jpg"
    path.write_bytes(image_bytes)
    _s3_upload(f"feedback/images/{image_id}.jpg", image_bytes, "image/jpeg")
    return str(path)

def save_annotation(ann_id: str, annotation: dict) -> str:
    path    = _ANNOTATIONS_DIR / f"{ann_id}.json"
    payload = json.dumps(annotation, ensure_ascii=False, indent=2).encode()
    path.write_bytes(payload)
    _s3_upload(f"feedback/annotations/{ann_id}.json", payload, "application/json")
    return str(path)

def count_feedback_items() -> int:
    """Number of feedback annotations — for Airflow threshold check."""
    return len(list(_ANNOTATIONS_DIR.glob("*.json")))

def save_user_profile(uid: str, profile: dict) -> None:
    path = _USERS_DIR / f"{uid}.json"
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def load_user_profile(uid: str) -> Optional[dict]:
    path = _USERS_DIR / f"{uid}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def append_diary_entry(uid: str, entry: dict) -> None:
    """Add one DiaryEntry to the device_id daily file."""
    day  = entry["logged_at"][:10]  
    path = _DIARY_DIR / uid / f"{day}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    entries.append(entry)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

def load_diary_entries(uid: str, day: str) -> list:
    """Load all DiaryEntry records for the given device_id on the specified date (YYYY-MM-DD)."""
    path = _DIARY_DIR / uid / f"{day}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def get_logged_dates(uid: str) -> list:
    """Retrieve all dates (YYYY-MM-DD) that have diary entries."""
    user_diary_dir = _DIARY_DIR / uid
    if not user_diary_dir.exists():
        return []
    return [f.stem for f in user_diary_dir.glob("*.json")]