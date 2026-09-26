from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel

import storage
import users
from schemas import DetectionResult
from nutrition import NUTRIENT_KEYS


class DiaryEntry(BaseModel):
    uid: str
    image_id: str
    logged_at: str 
    food_items: List[str]
    totals: Dict[str, float] 
    # Menerima objek DailyTarget utuh (termasuk string goal & activity_level)
    target_snapshot: Optional[users.DailyTarget] = None


class DailySummary(BaseModel):
    date: str
    entries: List[DiaryEntry]
    n_meals: int

    consumed_totals: Dict[str, float]
    target: users.DailyTarget

    remaining: Dict[str, float]
    progress: Dict[str, float]


def log_meal(uid: str, result: DetectionResult) -> DiaryEntry:
    """Save a meal session to the diary using the totals dictionary from DetectionResult."""
    profile = users.get_profile(uid)
    if profile is None:
        raise ValueError(f"User Profile '{uid}' not exists. call POST /users first.")
    
    # Ambil objek DailyTarget langsung (tanpa .model_dump())
    target_snapshot = users.calculate_daily_target(profile)

    entry = DiaryEntry(
        uid=uid,
        image_id=result.image_id,
        logged_at=datetime.now(timezone.utc).isoformat(),
        food_items=list({item.class_name for item in result.detected_classes}),
        totals=result.totals,
        target_snapshot=target_snapshot,
    )
    storage.append_diary_entry(uid, entry.model_dump())
    return entry


def get_daily_summary(
    uid: str,
    target_date: Optional[str] = None,
) -> DailySummary:
    target_date = target_date or date.today().isoformat()

    raw_entries = storage.load_diary_entries(uid, target_date)
    entries = [DiaryEntry(**e) for e in raw_entries]
    # Storage tidak menjamin urutan kronologis (sort key DynamoDB pakai
    # image_id, bukan waktu) — urutkan eksplisit di sini karena kode di bawah
    # bergantung pada entries[0] = entry PERTAMA hari itu.
    entries.sort(key=lambda e: e.logged_at)

    consumed_totals: Dict[str, float] = {}
    for entry in entries:
        for key, val in entry.totals.items():
            clean_key = key.replace("total_", "")
            consumed_totals[clean_key] = round(consumed_totals.get(clean_key, 0.0) + val, 1)

    # Pakai target yang dibekukan dari entry pertama hari itu kalau ada —
    # ini yang bikin riwayat tanggal lampau tidak ikut berubah kalau profile
    # diedit belakangan. Kalau belum ada entry (hari ini, belum makan apa-apa)
    # atau entry lama sebelum field ini ada, baru hitung live dari profile.
    if entries and entries[0].target_snapshot:
        # target = users.DailyTarget(**entries[0].target_snapshot)
        target = entries[0].target_snapshot
    else:
        profile = users.get_profile(uid)
        if profile is None:
            raise ValueError(f"User Profile '{uid}' not exists. call POST /users first.")
        target = users.calculate_daily_target(profile)

    target_dict = target.model_dump()

    remaining: Dict[str, float] = {}
    progress: Dict[str, float] = {}

    for key in NUTRIENT_KEYS:
        consumed = consumed_totals.get(key, 0.0)
        target_val = target_dict.get(key, 0.0)
        
        remaining[key] = round(target_val - consumed, 1)
        progress[key] = round(consumed / target_val, 3) if target_val > 0 else 0.0

    return DailySummary(
        date=target_date,
        entries=entries,
        n_meals=len(entries),
        consumed_totals=consumed_totals,
        target=target,
        remaining=remaining,
        progress=progress,
    )