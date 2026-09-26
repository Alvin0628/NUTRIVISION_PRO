import asyncio
import io
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import redis
import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image

import diary
import feedback as fb
import inference
import nutrition as nutr
import storage
import users
from schemas import (
    DetectionResult, GramsOverride, HealthResponse, LogRequest,
    MissingFoodRequest, RemoveRequest, SegmentedFood, ServingStyle,
)
from users import UserProfile, DailyTarget 
from vision_refine import BROAD_CLASSES, refine_broad_classes_batch
from nutrition import warm_up_cache_async

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cek flag dari .env, default False di dev
    if os.getenv("ENABLE_WARMUP", "false").lower() == "true":
        print("[startup] Memulai warm up cache Gemini...")
        await warm_up_cache_async()
    else:
        print("[startup] Cache warmup dilewati (Development Mode)")
    
    yield
    
    
app = FastAPI(
    title="NutriVision Pro API",
    description="Indonesian food segmentation + nutritional estimates",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")
APP_ENV = os.getenv("APP_ENV", "development")  # set APP_ENV=production di ECS/env prod

if APP_ENV == "production" and not FIREBASE_WEB_API_KEY:
    # Fail fast saat startup — jangan biarkan API jalan tanpa auth di production
    # secara diam-diam (sebelumnya verify_token() akan fallback ke "test_uid_local"
    # untuk SEMUA request kalau key ini kosong).
    raise RuntimeError(
        "FIREBASE_WEB_API_KEY wajib di-set saat APP_ENV=production. "
        "API tidak akan dijalankan tanpa auth yang valid."
    )

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
)

def _save_session(image_id: str, data: dict, ttl_seconds: int = 3600):
    redis_client.setex(f"session:{image_id}", ttl_seconds, json.dumps(data))

def _get_session(image_id: str) -> Optional[dict]:
    raw_data = redis_client.get(f"session:{image_id}")
    return json.loads(raw_data) if raw_data else None

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if not FIREBASE_WEB_API_KEY:
        # Hanya boleh lolos di development lokal — di production baris di atas
        # (startup check) sudah mencegah proses ini jalan tanpa key sama sekali.
        if APP_ENV != "production":
            return "test_uid_local"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth is not configured.",
        )

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_WEB_API_KEY}"
    try:
        resp = requests.post(url, json={"idToken": token}, timeout=5)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The Firebase token is invalid or has expired.",
            )
        data = resp.json()
        users_list = data.get("users")
        if not users_list:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user found for this token.",
            )
        return users_list[0]["localId"]
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to contact the Firebase authentication service.",
        )

@app.get("/health")
def health_check():
    return {"status": "ok"}

async def _build_result(
    image_id: str,
    detected: List[SegmentedFood],
    grams_map: Dict[str, float],
    serving_style_map: Dict[str, str],
    inference_ms: float,
) -> DetectionResult:
    grams_by_class: Dict[str, float] = {}
    style_by_class: Dict[str, str] = {}
    orig_class_by_class: Dict[str, str] = {}

    for item in detected:
        if item.class_name in serving_style_map:
            item.serving_style = ServingStyle(serving_style_map[item.class_name])
        style_by_class[item.class_name] = item.serving_style.value

        orig_class_by_class[item.class_name] = getattr(item, "original_class", item.class_name) or item.class_name

        if item.class_name in grams_map:
            item.estimated_grams = grams_map[item.class_name]

        # Selalu overwrite (last-wins), JANGAN dijumlahkan lintas instance dari class yang sama.
        # 1 class_name = 1 gramasi total di UI, terlepas berapa banyak instance yang terdeteksi.
        grams_by_class[item.class_name] = item.estimated_grams

    items_for_nutr = [
        (
            cls,
            grams_by_class[cls],
            style_by_class[cls],
            orig_class_by_class.get(cls, cls),
        )
        for cls in grams_by_class
    ]

    nutrient_list, totals = await nutr.get_nutrients_bulk_async(items_for_nutr)

    return DetectionResult(
        image_id=image_id,
        detected_classes=detected,
        nutrients=nutrient_list,
        totals=totals,
        inference_time_ms=inference_ms,
    )

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

@app.post("/predict", response_model=DetectionResult)
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 10MB limit.",
        )

    loop = asyncio.get_running_loop()

    # --- TIMING: Mulai YOLO Inference ---
    t0 = time.perf_counter()
    detected_items, inference_ms = await loop.run_in_executor(
        None, inference.run_pipeline, image_bytes
    )
    t1 = time.perf_counter()
    print(f"[timing] YOLO inference: {t1 - t0:.2f}s")

    broad_items = []
    for item in detected_items:
        if item.class_name.lower() in BROAD_CLASSES:
            item.original_class = item.class_name
            broad_items.append({"bbox": item.bbox, "broad_class": item.class_name})

    # --- TIMING: Gemini Batch Refine ---
    if broad_items:
        refined_names = await refine_broad_classes_batch(image_bytes, broad_items)
        
        broad_idx = 0
        for item in detected_items:
            if item.class_name.lower() in BROAD_CLASSES:
                item.class_name = refined_names[broad_idx]
                broad_idx += 1
    t2 = time.perf_counter()
    print(f"[timing] Gemini refine: {t2 - t1:.2f}s")

    image_id = str(uuid.uuid4())
    session_data = {
        "detections": {d.detection_id: d.model_dump() for d in detected_items}
    }
    _save_session(image_id, session_data)

    grams_map = {d.class_name: d.estimated_grams for d in detected_items}
    style_map = {d.class_name: d.serving_style.value for d in detected_items}

    # --- TIMING: Nutrition Bulk & Build Result ---
    result = await _build_result(
        image_id, detected_items, grams_map, style_map, inference_ms
    )
    t3 = time.perf_counter()
    print(f"[timing] Nutrition (Gemini bulk): {t3 - t2:.2f}s")
    print(f"[timing] TOTAL /predict execution: {t3 - t0:.2f}s")

    return result

@app.post("/recalculate", response_model=DetectionResult)
async def recalculate(req: GramsOverride):
    session = _get_session(req.image_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan atau telah kedaluwarsa.")

    # 1. Ambil detections yang ada dari session
    raw_detections = session.get("detections", {})
    detections = [SegmentedFood(**v) for v in raw_detections.values()]

    # 2. Update estimated_grams & serving_style pada objek detection langsung
    for d in detections:
        if d.class_name in req.grams_map:
            d.estimated_grams = req.grams_map[d.class_name]
        if d.class_name in req.serving_style_map:
            d.serving_style = req.serving_style_map[d.class_name]

    # 3. Simpan perubahan d.estimated_grams kembali ke Redis Session
    updated_session_detections = {d.detection_id: d.model_dump() for d in detections}
    session["detections"] = updated_session_detections
    _save_session(req.image_id, session)

    # 4. CRITICAL FIX: Kirim dict KOSONG {} untuk grams_map ke _build_result 
    # agar tidak terjadi double override / penjumlahan yang merusak gramasi per class
    return await _build_result(req.image_id, detections, {}, {}, 0.0)

@app.post("/feedback/remove", response_model=DetectionResult)
async def feedback_remove(req: RemoveRequest):
    fb.handle_remove_and_sync_session(req, redis_client)
    
    session = _get_session(req.image_id)
    if not session:
        raise HTTPException(404, "Session tidak ditemukan atau expired.")

    detections = [SegmentedFood(**v) for v in session["detections"].values()]
    grams_map = {d.class_name: d.estimated_grams for d in detections}
    style_map = {d.class_name: d.serving_style.value for d in detections}

    return await _build_result(req.image_id, detections, grams_map, style_map, 0.0)

@app.post("/feedback/missing", response_model=DetectionResult)
async def feedback_missing(req: MissingFoodRequest):
    fb.handle_missing(req)

    session = _get_session(req.image_id)
    if not session:
        raise HTTPException(404, "Session not found or expired.")

    new_detection_id = str(uuid.uuid4())
    cleaned_name = fb._normalize_food_name(req.food_name)
    
    new_item = SegmentedFood(
        detection_id=new_detection_id,
        class_name=cleaned_name,
        confidence=1.0,
        bbox=[req.tap_x, req.tap_y, min(req.tap_x + 0.1, 1.0), min(req.tap_y + 0.1, 1.0)],
        estimated_grams=100.0,
        serving_style=ServingStyle.FRIED,
    )

    session["detections"][new_detection_id] = new_item.model_dump()
    _save_session(req.image_id, session)
    
    detections = [SegmentedFood(**v) for v in session["detections"].values()]
    grams_map = {d.class_name: d.estimated_grams for d in detections}
    style_map = {d.class_name: d.serving_style.value for d in detections}

    return await _build_result(req.image_id, detections, grams_map, style_map, 0.0)

@app.get("/feedback/count")
def feedback_count():
    RETRAIN_THRESHOLD = int(os.getenv("RETRAIN_THRESHOLD", "100"))
    count = storage.count_feedback_items()
    return {
        "count": count,
        "threshold": RETRAIN_THRESHOLD,
        "ready_to_retrain": count >= RETRAIN_THRESHOLD,
    }

@app.post("/users", response_model=DailyTarget)
def create_or_update_profile(
    profile: UserProfile, auth_uid: str = Depends(verify_token)
):
    if profile.uid != auth_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to modify this profile.",
        )
    users.save_profile(profile)
    return users.calculate_daily_target(profile)

@app.get("/users/target", response_model=DailyTarget)
def get_target(uid: str = Depends(verify_token)):
    profile = users.get_profile(uid)
    if not profile:
        raise HTTPException(404, "Profile does not exist yet. Call POST /users first.")
    return users.calculate_daily_target(profile)

@app.post("/log")
async def log_meal(req: LogRequest, uid: str = Depends(verify_token)):
    session = _get_session(req.image_id)
    if not session:
        raise HTTPException(404, "The session was not found or has expired.")

    profile = users.get_profile(uid)
    if not profile:
        raise HTTPException(
            404, "User profile does not exist yet. Call POST /users first to set up the profile."
        )

    detections = [SegmentedFood(**v) for v in session["detections"].values()]
    result = await _build_result(req.image_id, detections, {}, {}, 0.0)
    return diary.log_meal(uid, result)

@app.get("/diary")
def get_diary(date: Optional[str] = None, uid: str = Depends(verify_token)):
    try:
        return diary.get_daily_summary(uid, date)
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.get("/diary/history-dates")
def get_history_dates(uid: str = Depends(verify_token)):
    return {"dates": storage.get_logged_dates(uid)}