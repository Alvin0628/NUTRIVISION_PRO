import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from schemas import NutrientInfo

_DIR        = Path(__file__).parent / "nutrition_data"
_CACHE_PATH = _DIR / "foods_cache.json"   
_STATIC_PATH = _DIR / "foods_static.json"

_DIR.mkdir(parents=True, exist_ok=True)

_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)

_PROMPT = """\
You are a nutritionist. Provide estimated nutritional values ​​per 100 grams for: "{food_name}"
Cooking/serving method: {serving_style} (fried, boiled, steamed, raw/fresh).

Return ONLY valid JSON without markdown, containing the following 16 nutritional components (per 100g):
{{
  "calories": <float>,
  "protein_g": <float>,
  "carbs_g": <float>,
  "fat_g": <float>,
  "fiber_g": <float>,
  "omega_3_g": <float>,
  "magnesium_mg": <float>,
  "zinc_mg": <float>,
  "iron_mg": <float>,
  "calcium_mg": <float>,
  "vitamin_c_mg": <float>,
  "vitamin_b_complex_mg": <float>,
  "vitamin_d_mcg": <float>,
  "vitamin_b12_mcg": <float>,
  "vitamin_a_mcg": <float>,
  "folic_acid_mcg": <float>
}}
"""

_STATIC_FALLBACK: Dict = {
    "beef":       {"calories": 207, "protein_g": 18.8, "carbs_g": 0.0,  "fat_g": 14.0},
    "chicken":    {"calories": 179, "protein_g": 18.2, "carbs_g": 0.0,  "fat_g": 11.5},
    "egg":        {"calories": 154, "protein_g": 12.4, "carbs_g": 0.7,  "fat_g": 10.8},
    "fish":       {"calories": 113, "protein_g": 17.0, "carbs_g": 0.0,  "fat_g": 4.5},
    "fruit":      {"calories": 60,  "protein_g": 0.8,  "carbs_g": 14.0, "fat_g": 0.3},
    "noodles":    {"calories": 138, "protein_g": 4.5,  "carbs_g": 27.0, "fat_g": 1.2},
    "pork":       {"calories": 242, "protein_g": 16.0, "carbs_g": 0.0,  "fat_g": 20.0},
    "rice":       {"calories": 180, "protein_g": 3.0,  "carbs_g": 40.6, "fat_g": 0.3},
    "sambal":     {"calories": 35,  "protein_g": 1.0,  "carbs_g": 6.0,  "fat_g": 1.2},
    "shrimp":     {"calories": 84,  "protein_g": 17.6, "carbs_g": 0.9,  "fat_g": 1.1},
    "squid":      {"calories": 79,  "protein_g": 16.4, "carbs_g": 0.8,  "fat_g": 1.0},
    "tempeh":     {"calories": 149, "protein_g": 18.3, "carbs_g": 9.4,  "fat_g": 4.0},
    "tofu":       {"calories": 68,  "protein_g": 7.8,  "carbs_g": 1.6,  "fat_g": 3.8},
    "vegetable":  {"calories": 30,  "protein_g": 2.0,  "carbs_g": 5.5,  "fat_g": 0.3},
}


def _load_cache() -> Dict:
    if _CACHE_PATH.exists():
        with _CACHE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: Dict):
    with _CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# Load cache sekali saat startup
_CACHE: Dict = _load_cache()


def _query_gemini(food_name: str, serving_style: str = "fried") -> Optional[dict]:
    """Query Gemini Flash for a single food name. Return a dictionary of nutritional information or None."""
    if not _GEMINI_KEY:
        print("[nutrition] GEMINI_API_KEY not yet set")
        return None

    payload = json.dumps({
        "contents": [{"parts": [{"text": _PROMPT.format(food_name=food_name, serving_style=serving_style)}]}],
        "generationConfig": {
            "temperature":     0.1,
            "maxOutputTokens": 300,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        _GEMINI_URL.format(key=_GEMINI_KEY),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        result = json.loads(text)

        if "error" in result:
            return None

        required = {"calories", "protein_g", "carbs_g", "fat_g"}
        if not required.issubset(result.keys()):
            return None

        return {
            "calories":     float(result["calories"]),
            "protein_g":    float(result["protein_g"]),
            "carbs_g":      float(result["carbs_g"]),
            "fat_g":        float(result["fat_g"]),
            "food_name_id": result.get("food_name_id", food_name),
            "notes":        result.get("notes", ""),
            "source":       "gemini",
        }

    except Exception as e:
        print(f"[nutrition] Gemini error untuk '{food_name}': {e}")
        return None


NUTRIENT_KEYS = [
    "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "omega_3_g",
    "magnesium_mg", "zinc_mg", "iron_mg", "calcium_mg", "vitamin_c_mg",
    "vitamin_b_complex_mg", "vitamin_d_mcg", "vitamin_b12_mcg", "vitamin_a_mcg", "folic_acid_mcg"
]

def get_nutrients(class_name, grams=100.0, serving_style="fried", original_class: Optional[str] = None):
    cache_key = f"{class_name}__{serving_style}"
    entry, source = None, "unknown"

    if cache_key in _CACHE:
        entry, source = _CACHE[cache_key], _CACHE[cache_key].get("source", "gemini_cached")
    else:
        entry = _query_gemini(class_name, serving_style)
        if entry:
            _CACHE[cache_key] = entry
            _save_cache(_CACHE)
            source = "gemini"

    if entry is None:   # BARU -- fallback bertingkat
        fallback_key = class_name if class_name in _STATIC_FALLBACK else original_class
        if fallback_key in _STATIC_FALLBACK:
            entry, source = _STATIC_FALLBACK[fallback_key], "static_fallback"

    if entry is None:
        return NutrientInfo(class_name=class_name, grams=grams, source="unknown")

    factor = grams / 100.0
    nutr_data = {k: round(entry.get(k, 0.0) * factor, 2) for k in NUTRIENT_KEYS}
    return NutrientInfo(class_name=class_name, grams=grams, source=source, **nutr_data)

# Ubah type hint dan unpack-nya jadi 4-tuple
def get_nutrients_bulk(
    items: List[Tuple[str, float, str, Optional[str]]]
) -> Tuple[List[NutrientInfo], Dict[str, float]]:
    # Passing orig_cls ke fungsi get_nutrients
    results = [
        get_nutrients(cls, g, style, orig_cls)
        for cls, g, style, orig_cls in items
    ]
    
    totals = {}
    for key in NUTRIENT_KEYS:
        totals[f"total_{key}"] = round(sum(getattr(r, key, 0.0) for r in results), 2)

    return results, totals

def warm_up_cache():
    base_classes = list(_STATIC_FALLBACK.keys())
    # Samakan format key dengan get_nutrients (default style 'fried')
    missing = [c for c in base_classes if f"{c}__fried" not in _CACHE]
    if not missing:
        print(f"[nutrition] Cache is complete ({len(_CACHE)} items)")
        return
    print(f"[nutrition] Warming up cache for {len(missing)} classes via Gemini...")
    for cls in missing:
        result = _query_gemini(cls, "fried")
        if result:
            cache_key = f"{cls}__fried"
            _CACHE[cache_key] = result
            print(f"  ✓ {cls}: {result['calories']} kcal/100g")
        else:
            print(f"  ✗ {cls}: fallback to static")
    _save_cache(_CACHE)
    print(f"[nutrition] Cache warm-up complete — {len(_CACHE)} items cached")
