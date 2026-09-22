import asyncio
import io
import json
import os
import uuid
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
from vision_refine import BROAD_CLASSES, refine_broad_class
from contextlib import asynccontextmanager

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    nutr.warm_up_cache()
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
        return "test_uid_local"

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


@app.on_event("startup")
async def startup_event():
    nutr.warm_up_cache()

def _build_result(
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
        orig_class_by_class[item.class_name] = item.original_class

        # --- LOGIKA GRAMASI (OVERRIDE VS AKUMULASI) ---
        if item.class_name in grams_map:
            item.estimated_grams = grams_map[item.class_name]
            grams_by_class[item.class_name] = grams_map[item.class_name]
        else:
            grams_by_class[item.class_name] = (
                grams_by_class.get(item.class_name, 0.0) + item.estimated_grams
            )

    # Kirim 4-tuple: (class_name, grams, serving_style, original_class)
    items_for_nutr = [
        (
            cls,
            grams_by_class[cls],
            style_by_class[cls],
            orig_class_by_class.get(cls, cls),
        )
        for cls in grams_by_class
    ]

    nutrient_list, totals = nutr.get_nutrients_bulk(items_for_nutr)

    return DetectionResult(
        image_id=image_id,
        detected_classes=detected,
        nutrients=nutrient_list,
        totals=totals,
        inference_time_ms=inference_ms,
    )

@app.post("/predict", response_model=DetectionResult)
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()

    loop = asyncio.get_running_loop()
    detected_items, inference_ms = await loop.run_in_executor(
        None, inference.run_pipeline, image_bytes
    )

    refinement_tasks = []
    task_indices = []

    for idx, item in enumerate(detected_items):
        if item.class_name.lower() in BROAD_CLASSES:
            item.original_class = item.class_name
            task = refine_broad_class(image_bytes, item.bbox, item.class_name)
            refinement_tasks.append(task)
            task_indices.append(idx)

    if refinement_tasks:
        specific_names = await asyncio.gather(*refinement_tasks)
        for idx, new_name in zip(task_indices, specific_names):
            detected_items[idx].class_name = new_name

    image_id = str(uuid.uuid4())
    session_data = {
        "detections": {d.detection_id: d.dict() for d in detected_items}
    }
    _save_session(image_id, session_data)

    grams_map = {d.class_name: d.estimated_grams for d in detected_items}
    style_map = {d.class_name: d.serving_style.value for d in detected_items}

    return await loop.run_in_executor(
        None, _build_result, image_id, detected_items, grams_map, style_map, inference_ms
    )


@app.post("/recalculate", response_model=DetectionResult)
def recalculate(req: GramsOverride):
    session = _get_session(req.image_id)
    if not session:
        raise HTTPException(404, "Session tidak ditemukan atau telah kedaluwarsa.")

    detections = [SegmentedFood(**v) for v in session["detections"].values()]
    style_map = {
        k: v.value if hasattr(v, "value") else v
        for k, v in req.serving_style_map.items()
    }

    for d in detections:
        if d.class_name in req.grams_map:
            d.estimated_grams = req.grams_map[d.class_name]
        if d.class_name in req.serving_style_map:
            d.serving_style = req.serving_style_map[d.class_name]

    updated_session = {
        "detections": {d.detection_id: d.dict() for d in detections}
    }
    _save_session(req.image_id, updated_session)

    return _build_result(req.image_id, detections, req.grams_map, style_map, 0.0)


@app.post("/feedback/remove")
def feedback_remove(req: RemoveRequest):
    return fb.handle_remove(req)


@app.post("/feedback/missing")
def feedback_missing(req: MissingFoodRequest):
    session = _get_session(req.image_id)
    if not session:
        raise HTTPException(404, "Session not found or expired..")
    return fb.handle_missing(req)


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
def log_meal(req: LogRequest, uid: str = Depends(verify_token)):
    session = _get_session(req.image_id)
    if not session:
        raise HTTPException(404, "The session was not found or has expired.")

    profile = users.get_profile(uid)
    if not profile:
        raise HTTPException(
            404, "User profile does not exist yet. Call POST /users first to set up the profile."
        )

    detections = [SegmentedFood(**v) for v in session["detections"].values()]
    result = _build_result(req.image_id, detections, {}, {}, 0.0)
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