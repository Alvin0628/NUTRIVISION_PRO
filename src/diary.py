from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel

import storage
import users
from schemas import DetectionResult


class DiaryEntry(BaseModel):
    uid: str
    image_id: str
    logged_at: str 
    food_items: List[str]
    totals: Dict[str, float] 


class DailySummary(BaseModel):
    date: str
    entries: List[DiaryEntry]
    n_meals: int

    consumed_totals: Dict[str, float]

    target: users.DailyTarget

    # Remaining amounts & progress
    remaining_calories: float
    remaining_protein_g: float
    remaining_carbs_g: float
    remaining_fat_g: float

    progress_calories: float
    progress_protein: float
    progress_carbs: float
    progress_fat: float


def log_meal(uid: str, result: DetectionResult) -> DiaryEntry:
    """Save a meal session to the diary using the totals dictionary from DetectionResult."""
    entry = DiaryEntry(
        uid=uid,
        image_id=result.image_id,
        logged_at=datetime.now(timezone.utc).isoformat(),
        food_items=list({item.class_name for item in result.detected_classes}),
        totals=result.totals,
    )
    storage.append_diary_entry(uid, entry.dict())
    return entry


def get_daily_summary(
    uid: str,
    target_date: Optional[str] = None,
) -> DailySummary:
    """Get a daily summary with an aggregation of all 16 nutrients."""
    target_date = target_date or date.today().isoformat()

    raw_entries = storage.load_diary_entries(uid, target_date)
    entries = [DiaryEntry(**e) for e in raw_entries]

    consumed_totals: Dict[str, float] = {}
    for entry in entries:
        for key, val in entry.totals.items():
            consumed_totals[key] = round(consumed_totals.get(key, 0.0) + val, 1)

    consumed_calories = consumed_totals.get("total_calories", 0.0)
    consumed_protein = consumed_totals.get("total_protein_g", 0.0)
    consumed_carbs = consumed_totals.get("total_carbs_g", 0.0)
    consumed_fat = consumed_totals.get("total_fat_g", 0.0)

    profile = users.get_profile(uid)
    if profile is None:
        raise ValueError(f"User Profile '{uid}' not exists. call POST /users first.")

    target = users.calculate_daily_target(profile)

    def _progress(consumed: float, target_val: float) -> float:
        return round(consumed / target_val, 3) if target_val > 0 else 0.0

    return DailySummary(
        date=target_date,
        entries=entries,
        n_meals=len(entries),
        consumed_totals=consumed_totals,
        target=target,
        remaining_calories=round(target.target_calories - consumed_calories, 1),
        remaining_protein_g=round(target.target_protein_g - consumed_protein, 1),
        remaining_carbs_g=round(target.target_carbs_g - consumed_carbs, 1),
        remaining_fat_g=round(target.target_fat_g - consumed_fat, 1),
        progress_calories=_progress(consumed_calories, target.target_calories),
        progress_protein=_progress(consumed_protein, target.target_protein_g),
        progress_carbs=_progress(consumed_carbs, target.target_carbs_g),
        progress_fat=_progress(consumed_fat, target.target_fat_g),
    )