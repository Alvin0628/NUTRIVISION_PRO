"""
storage.py — Storage abstraction:
  - feedback images/annotations → S3 (falls back to local disk if S3 not configured)
  - user profiles & diary entries → DynamoDB (falls back to local disk ONLY if
    table names are not set — meant for local dev without AWS, never rely on
    this fallback in production: container disks are ephemeral)

All other modules import from here, never call boto3 directly.

Local Directory (dev fallback only):
  /tmp/nutrivision/
  ├── feedback/
  │   ├── images/       → image from /predict
  │   └── annotations/  → JSON annotation form /feedback/*
  ├── users/            → profile per uid (uid.json)   [dev fallback only]
  └── diary/
      └── {uid}/
          └── {YYYY-MM-DD}.json  → list DiaryEntry     [dev fallback only]
"""

import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Optional

_BASE            = Path(os.getenv("STORAGE_LOCAL_DIR", "/tmp/nutrivision"))
_IMAGES_DIR      = _BASE / "feedback" / "images"
_ANNOTATIONS_DIR = _BASE / "feedback" / "annotations"
_USERS_DIR       = _BASE / "users"
_DIARY_DIR       = _BASE / "diary"

for _d in (_IMAGES_DIR, _ANNOTATIONS_DIR, _USERS_DIR, _DIARY_DIR):
    _d.mkdir(parents=True, exist_ok=True)


_AWS_REGION       = os.getenv("AWS_REGION", "ap-southeast-1")
_S3_BUCKET        = os.getenv("S3_FEEDBACK_BUCKET", "")
_USERS_TABLE_NAME = os.getenv("DYNAMODB_USERS_TABLE", "")
_DIARY_TABLE_NAME = os.getenv("DYNAMODB_DIARY_TABLE", "")

_s3_client = None
_dynamodb  = None


def _s3():
    global _s3_client
    if _s3_client is None and _S3_BUCKET:
        try:
            import boto3
            _s3_client = boto3.client("s3", region_name=_AWS_REGION)
        except Exception as e:
            print(f"[storage] boto3 S3 not ready: {e}")
    return _s3_client


def _dynamo():
    global _dynamodb
    if _dynamodb is None and (_USERS_TABLE_NAME or _DIARY_TABLE_NAME):
        try:
            import boto3
            _dynamodb = boto3.resource("dynamodb", region_name=_AWS_REGION)
        except Exception as e:
            print(f"[storage] boto3 DynamoDB not ready: {e}")
    return _dynamodb


def _users_table():
    db = _dynamo()
    return db.Table(_USERS_TABLE_NAME) if db and _USERS_TABLE_NAME else None


def _diary_table():
    db = _dynamo()
    return db.Table(_DIARY_TABLE_NAME) if db and _DIARY_TABLE_NAME else None


def _s3_upload(key: str, body: bytes, content_type: str):
    client = _s3()
    if not client:
        return
    try:
        client.put_object(Bucket=_S3_BUCKET, Key=key, Body=body, ContentType=content_type)
    except Exception as e:
        print(f"[storage] S3 upload failed ({key}): {e}")


# ── DynamoDB numeric helpers ────────────────────────────────────────────────
# boto3's DynamoDB resource rejects native float — everything numeric must be
# Decimal going in, and comes back as Decimal, so we round-trip through these.

def _floats_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _floats_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_floats_to_decimal(v) for v in obj]
    return obj


def _decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(v) for v in obj]
    return obj


# ── Feedback: Image & Annotation (unchanged) ───────────────────────────────

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


# ── User profile: DynamoDB (dev fallback: local JSON) ──────────────────────

def save_user_profile(uid: str, profile: dict) -> None:
    table = _users_table()
    if table:
        item = _floats_to_decimal({"uid": uid, **profile})
        table.put_item(Item=item)
        return
    print("[storage] WARNING: DYNAMODB_USERS_TABLE not set — writing profile to local disk "
          "(will NOT survive container restart/redeploy). Set it before deploying.")
    path = _USERS_DIR / f"{uid}.json"
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def load_user_profile(uid: str) -> Optional[dict]:
    table = _users_table()
    if table:
        resp = table.get_item(Key={"uid": uid})
        item = resp.get("Item")
        return _decimal_to_float(item) if item else None
    path = _USERS_DIR / f"{uid}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ── Diary: DynamoDB, PK=uid SK="{date}#{entry_id}" (dev fallback: local JSON) ─

def append_diary_entry(uid: str, entry: dict) -> None:
    day = entry["logged_at"][:10]
    table = _diary_table()
    if table:
        entry_id = entry.get("image_id") or entry["logged_at"]
        item = _floats_to_decimal({"uid": uid, "sk": f"{day}#{entry_id}", "date": day, **entry})
        table.put_item(Item=item)
        return
    print("[storage] WARNING: DYNAMODB_DIARY_TABLE not set — writing diary entry to local disk "
          "(will NOT survive container restart/redeploy). Set it before deploying.")
    path = _DIARY_DIR / uid / f"{day}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    entries.append(entry)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def load_diary_entries(uid: str, day: str) -> list:
    """Load all DiaryEntry records for the given uid on the specified date (YYYY-MM-DD)."""
    table = _diary_table()
    if table:
        from boto3.dynamodb.conditions import Key
        resp = table.query(
            KeyConditionExpression=Key("uid").eq(uid) & Key("sk").begins_with(f"{day}#")
        )
        return [_decimal_to_float(item) for item in resp.get("Items", [])]
    path = _DIARY_DIR / uid / f"{day}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def get_logged_dates(uid: str) -> list:
    """Retrieve all dates (YYYY-MM-DD) that have diary entries."""
    table = _diary_table()
    if table:
        from boto3.dynamodb.conditions import Key
        resp = table.query(KeyConditionExpression=Key("uid").eq(uid))
        dates = {item["date"] for item in resp.get("Items", []) if "date" in item}
        return sorted(dates)
    user_diary_dir = _DIARY_DIR / uid
    if not user_diary_dir.exists():
        return []
    return [f.stem for f in user_diary_dir.glob("*.json")]