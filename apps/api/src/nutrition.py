import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import redis
from google import genai
from google.genai import types

from schemas import NutrientInfo

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

# Cache nutrisi disimpan di Redis (db terpisah dari session di main.py yang
# pakai db=0) supaya persist lintas restart & di-share antar container —
# sebelumnya ini file JSON lokal yang hilang tiap kali container di-redeploy.
_REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
_REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
_CACHE_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 hari — nilai gizi per 100g jarang berubah

_cache_redis = redis.Redis(
    host=_REDIS_HOST, port=_REDIS_PORT, db=1, decode_responses=True,
)

def _cache_key(class_name: str, serving_style: str) -> str:
    return f"nutrition:{class_name}__{serving_style}"

# Inisialisasi Google GenAI SDK
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# Flag Cooldown Rate-Limit Global (Timestamp Epoch)
API_COOLDOWN_UNTIL: float = 0.0

_PROMPT = """\
You are a nutritionist. Provide estimated nutritional values per 100 grams for: "{food_name}"
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
    "beef": {
        "calories": 207.0, "protein_g": 18.8, "carbs_g": 0.0, "fat_g": 14.0,
        "fiber_g": 0.0, "omega_3_g": 0.05, "magnesium_mg": 21.0, "zinc_mg": 4.8,
        "iron_mg": 2.6, "calcium_mg": 11.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.3,
        "vitamin_d_mcg": 0.1, "vitamin_b12_mcg": 2.1, "vitamin_a_mcg": 0.0, "folic_acid_mcg": 6.0,
    },
    "chicken": {
        "calories": 179.0, "protein_g": 18.2, "carbs_g": 0.0, "fat_g": 11.5,
        "fiber_g": 0.0, "omega_3_g": 0.03, "magnesium_mg": 20.0, "zinc_mg": 1.3,
        "iron_mg": 1.3, "calcium_mg": 14.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.2,
        "vitamin_d_mcg": 0.1, "vitamin_b12_mcg": 0.3, "vitamin_a_mcg": 10.0, "folic_acid_mcg": 4.0,
    },
    "egg": {
        "calories": 154.0, "protein_g": 12.4, "carbs_g": 0.7, "fat_g": 10.8,
        "fiber_g": 0.0, "omega_3_g": 0.1, "magnesium_mg": 12.0, "zinc_mg": 1.1,
        "iron_mg": 2.7, "calcium_mg": 86.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 2.0, "vitamin_b12_mcg": 0.9, "vitamin_a_mcg": 180.0, "folic_acid_mcg": 44.0,
    },
    "fish": {
        "calories": 113.0, "protein_g": 17.0, "carbs_g": 0.0, "fat_g": 4.5,
        "fiber_g": 0.0, "omega_3_g": 0.4, "magnesium_mg": 29.0, "zinc_mg": 0.8,
        "iron_mg": 1.0, "calcium_mg": 20.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.2,
        "vitamin_d_mcg": 2.5, "vitamin_b12_mcg": 2.8, "vitamin_a_mcg": 15.0, "folic_acid_mcg": 5.0,
    },
    "fruit": {
        "calories": 60.0, "protein_g": 0.8, "carbs_g": 14.0, "fat_g": 0.3,
        "fiber_g": 2.4, "omega_3_g": 0.01, "magnesium_mg": 12.0, "zinc_mg": 0.1,
        "iron_mg": 0.3, "calcium_mg": 12.0, "vitamin_c_mg": 30.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "vitamin_a_mcg": 40.0, "folic_acid_mcg": 14.0,
    },
    "noodles": {
        "calories": 138.0, "protein_g": 4.5, "carbs_g": 27.0, "fat_g": 1.2,
        "fiber_g": 1.2, "omega_3_g": 0.01, "magnesium_mg": 18.0, "zinc_mg": 0.5,
        "iron_mg": 1.2, "calcium_mg": 16.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "vitamin_a_mcg": 0.0, "folic_acid_mcg": 18.0,
    },
    "pork": {
        "calories": 242.0, "protein_g": 16.0, "carbs_g": 0.0, "fat_g": 20.0,
        "fiber_g": 0.0, "omega_3_g": 0.06, "magnesium_mg": 18.0, "zinc_mg": 2.4,
        "iron_mg": 1.1, "calcium_mg": 12.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.4,
        "vitamin_d_mcg": 0.2, "vitamin_b12_mcg": 0.7, "vitamin_a_mcg": 2.0, "folic_acid_mcg": 3.0,
    },
    "rice": {
        "calories": 180.0, "protein_g": 3.0, "carbs_g": 40.6, "fat_g": 0.3,
        "fiber_g": 0.4, "omega_3_g": 0.01, "magnesium_mg": 12.0, "zinc_mg": 0.6,
        "iron_mg": 0.4, "calcium_mg": 10.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "vitamin_a_mcg": 0.0, "folic_acid_mcg": 8.0,
    },
    "sambal": {
        "calories": 35.0, "protein_g": 1.0, "carbs_g": 6.0, "fat_g": 1.2,
        "fiber_g": 1.5, "omega_3_g": 0.01, "magnesium_mg": 10.0, "zinc_mg": 0.2,
        "iron_mg": 0.5, "calcium_mg": 15.0, "vitamin_c_mg": 25.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "vitamin_a_mcg": 50.0, "folic_acid_mcg": 10.0,
    },
    "shrimp": {
        "calories": 84.0, "protein_g": 17.6, "carbs_g": 0.9, "fat_g": 1.1,
        "fiber_g": 0.0, "omega_3_g": 0.3, "magnesium_mg": 33.0, "zinc_mg": 1.1,
        "iron_mg": 2.1, "calcium_mg": 52.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 1.2, "vitamin_a_mcg": 18.0, "folic_acid_mcg": 3.0,
    },
    "squid": {
        "calories": 79.0, "protein_g": 16.4, "carbs_g": 0.8, "fat_g": 1.0,
        "fiber_g": 0.0, "omega_3_g": 0.2, "magnesium_mg": 33.0, "zinc_mg": 1.5,
        "iron_mg": 0.7, "calcium_mg": 32.0, "vitamin_c_mg": 4.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 1.3, "vitamin_a_mcg": 10.0, "folic_acid_mcg": 5.0,
    },
    "tempeh": {
        "calories": 149.0, "protein_g": 18.3, "carbs_g": 9.4, "fat_g": 4.0,
        "fiber_g": 1.4, "omega_3_g": 0.1, "magnesium_mg": 70.0, "zinc_mg": 1.1,
        "iron_mg": 2.3, "calcium_mg": 80.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.2,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.1, "vitamin_a_mcg": 0.0, "folic_acid_mcg": 24.0,
    },
    "tofu": {
        "calories": 68.0, "protein_g": 7.8, "carbs_g": 1.6, "fat_g": 3.8,
        "fiber_g": 0.3, "omega_3_g": 0.08, "magnesium_mg": 30.0, "zinc_mg": 0.8,
        "iron_mg": 1.8, "calcium_mg": 124.0, "vitamin_c_mg": 0.0, "vitamin_b_complex_mg": 0.05,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "vitamin_a_mcg": 0.0, "folic_acid_mcg": 15.0,
    },
    "vegetable": {
        "calories": 30.0, "protein_g": 2.0, "carbs_g": 5.5, "fat_g": 0.3,
        "fiber_g": 2.5, "omega_3_g": 0.02, "magnesium_mg": 25.0, "zinc_mg": 0.3,
        "iron_mg": 1.0, "calcium_mg": 40.0, "vitamin_c_mg": 20.0, "vitamin_b_complex_mg": 0.1,
        "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "vitamin_a_mcg": 120.0, "folic_acid_mcg": 30.0,
    },
}

_GENERIC_FALLBACK: Dict = {
    "calories": 150.0, "protein_g": 8.0, "carbs_g": 15.0, "fat_g": 6.0,
    "fiber_g": 2.0, "omega_3_g": 0.1, "magnesium_mg": 20.0, "zinc_mg": 1.0,
    "iron_mg": 1.0, "calcium_mg": 30.0, "vitamin_c_mg": 2.0,
    "vitamin_b_complex_mg": 0.2, "vitamin_d_mcg": 0.2, "vitamin_b12_mcg": 0.3,
    "vitamin_a_mcg": 30.0, "folic_acid_mcg": 15.0,
}

NUTRIENT_KEYS = [
    "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "omega_3_g",
    "magnesium_mg", "zinc_mg", "iron_mg", "calcium_mg", "vitamin_c_mg",
    "vitamin_b_complex_mg", "vitamin_d_mcg", "vitamin_b12_mcg", "vitamin_a_mcg", "folic_acid_mcg"
]

def _is_complete_entry(entry: dict) -> bool:
    return isinstance(entry, dict) and all(k in entry for k in NUTRIENT_KEYS)

async def _query_gemini_with_retry(food_name: str, serving_style: str = "fried", max_retries: int = 3) -> Optional[dict]:
    """
    Memanggil Gemini API dengan penanganan Exponential Backoff dan Cooldown 60s jika terkena Rate-Limit (429).
    """
    global API_COOLDOWN_UNTIL

    if not gemini_client:
        print("[nutrition DEBUG ERROR] GEMINI_API_KEY tidak ditemukan!")
        return None

    # Cek Cooldown Rate Limit
    if time.time() < API_COOLDOWN_UNTIL:
        print(f"[nutrition COOLDOWN] Skipping Gemini API call for '{food_name}' (Cooldown aktif)")
        return None

    prompt = _PROMPT.format(food_name=food_name, serving_style=serving_style)
    delay = 1.0
    loop = asyncio.get_running_loop()

    for attempt in range(max_retries):
        try:
            # Eksekusi SDK synchronous di thread executor agar non-blocking
            response = await loop.run_in_executor(
                None,
                lambda: gemini_client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
            )

            data = json.loads(response.text)
            parsed_nutrients = {k: float(data.get(k, 0.0)) for k in NUTRIENT_KEYS}
            parsed_nutrients["source"] = "gemini"
            print(f"[nutrition DEBUG SUCCESS] Gemini berhasil memproses '{food_name}' ({serving_style})!")
            return parsed_nutrients

        except Exception as e:
            err_msg = str(e)
            print(f"[nutrition ERROR] Percobaan {attempt + 1} gagal untuk '{food_name}': {err_msg}")

            # Tangani Error 429 / ResourceExhausted
            if "429" in err_msg or "ResourceExhausted" in err_msg:
                print("[nutrition WARNING] Rate limit 429 terdeteksi! Cooldown diaktifkan 60 detik.")
                API_COOLDOWN_UNTIL = time.time() + 60.0
                break

            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2.0

    return None

async def get_nutrients_async(
    class_name: str, 
    grams: float = 100.0, 
    serving_style: str = "fried", 
    original_class: Optional[str] = None
) -> NutrientInfo:
    """
    Mengambil data nutrisi secara asinkron dengan urutan pencarian:
    Cache -> Gemini (Retry/Backoff) -> Static Fallback -> Generic Fallback.
    """
    cache_key = _cache_key(class_name, serving_style)
    entry, source = None, "unknown"

    # 1. Cek Cache Redis
    cached_raw = _cache_redis.get(cache_key)
    cached = json.loads(cached_raw) if cached_raw else None
    if cached and _is_complete_entry(cached):
        entry, source = cached, cached.get("source", "gemini_cached")
    else:
        # 2. Query Gemini API
        entry = await _query_gemini_with_retry(class_name, serving_style)
        if entry:
            _cache_redis.setex(cache_key, _CACHE_TTL_SECONDS, json.dumps(entry))
            source = "gemini"

    # 3. Fallback jika Gemini Offline / Error
    if entry is None:
        fallback_key = None
        if class_name in _STATIC_FALLBACK:
            fallback_key = class_name
        elif original_class and original_class in _STATIC_FALLBACK:
            fallback_key = original_class
        else:
            for base_key in _STATIC_FALLBACK:
                if base_key in class_name.lower():
                    fallback_key = base_key
                    break

        if fallback_key and fallback_key in _STATIC_FALLBACK:
            entry, source = _STATIC_FALLBACK[fallback_key], "static_fallback"

    # 4. Final Generic Fallback
    if entry is None:
        entry, source = _GENERIC_FALLBACK, "generic_estimate"

    factor = grams / 100.0
    nutr_data = {k: round(entry.get(k, 0.0) * factor, 2) for k in NUTRIENT_KEYS}
    return NutrientInfo(class_name=class_name, grams=grams, source=source, **nutr_data)

def get_nutrients(
    class_name: str, 
    grams: float = 100.0, 
    serving_style: str = "fried", 
    original_class: Optional[str] = None
) -> NutrientInfo:
    """Wrapper synchronous untuk kebutuhan panggilan non-async."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.run_until_complete(get_nutrients_async(class_name, grams, serving_style, original_class))
    else:
        return asyncio.run(get_nutrients_async(class_name, grams, serving_style, original_class))

async def get_nutrients_bulk_async(
    items: List[Tuple[str, float, str, Optional[str]]]
) -> Tuple[List[NutrientInfo], Dict[str, float]]:
    """Menjalankan eksekusi pemanggilan nutrisi secara paralel/asinkron."""
    tasks = [
        get_nutrients_async(cls, g, style, orig_cls)
        for cls, g, style, orig_cls in items
    ]
    
    results: List[NutrientInfo] = await asyncio.gather(*tasks)

    totals = {}
    for key in NUTRIENT_KEYS:
        totals[f"total_{key}"] = round(sum(getattr(r, key, 0.0) for r in results), 2)

    return results, totals

def get_nutrients_bulk(
    items: List[Tuple[str, float, str, Optional[str]]]
) -> Tuple[List[NutrientInfo], Dict[str, float]]:
    """Backward compatibility synchronous bulk call."""
    return asyncio.run(get_nutrients_bulk_async(items))

async def warm_up_cache_async():
    """Fungsi warm-up cache asinkron."""
    CLASS_STYLE_MATRIX = {
        "beef":      ["fried"],
        "chicken":   ["fried"],
        "egg":       ["fried", "boiled"],
        "fish":      ["fried", "boiled", "steamed"],
        "fruit":     ["raw"],
        "noodles":   ["boiled"],
        "pork":      ["fried"],
        "rice":      ["boiled"],
        "sambal":    ["raw"],
        "shrimp":    ["fried", "boiled"],
        "squid":     ["fried"],
        "tempeh":    ["fried"],
        "tofu":      ["fried", "boiled"],
        "vegetable": ["steamed", "raw"],
    }

    pairs_needed = [
        (cls, style)
        for cls, styles in CLASS_STYLE_MATRIX.items()
        for style in styles
    ]

    def _cached_complete(cls: str, style: str) -> bool:
        raw = _cache_redis.get(_cache_key(cls, style))
        return bool(raw) and _is_complete_entry(json.loads(raw))

    missing = [(cls, style) for cls, style in pairs_needed if not _cached_complete(cls, style)]

    if not missing:
        print("[nutrition] Cache sudah lengkap")
        return

    print(f"[nutrition] Warming up {len(missing)} kombinasi via Gemini...")

    for cls, style in missing:
        cache_key = _cache_key(cls, style)
        result = await _query_gemini_with_retry(cls, style)

        if result:
            _cache_redis.setex(cache_key, _CACHE_TTL_SECONDS, json.dumps(result))
            print(f"  ✓ {cls} ({style}): {result['calories']} kcal/100g [gemini]")
        elif cls in _STATIC_FALLBACK:
            fallback = {**_STATIC_FALLBACK[cls], "source": "static_fallback"}
            _cache_redis.setex(cache_key, _CACHE_TTL_SECONDS, json.dumps(fallback))
            print(f"  ✗ {cls} ({style}): static_fallback cached [Gemini gagal]")
        else:
            generic = {**_GENERIC_FALLBACK, "source": "generic_estimate"}
            _cache_redis.setex(cache_key, _CACHE_TTL_SECONDS, json.dumps(generic))
            print(f"  ✗ {cls} ({style}): generic cached [kelas baru]")

    print("[nutrition] Cache warm-up selesai")

def warm_up_cache():
    asyncio.run(warm_up_cache_async())