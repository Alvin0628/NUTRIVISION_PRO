from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class LogRequest(BaseModel):
    image_id: str

class ServingStyle(str, Enum):
    FRIED   = "fried"    
    BOILED  = "boiled"   
    STEAMED = "steamed"  
    RAW     = "raw"     

# schemas.py
class SegmentedFood(BaseModel):
    detection_id: str
    class_name: str
    original_class: Optional[str] = None
    confidence: float
    bbox: List[float]
    mask_area_ratio: float = 0.0
    mask_polygon: List[List[float]] = []   # BARU -- restore
    estimated_grams: float = 100.0
    serving_style: ServingStyle = ServingStyle.FRIED


class NutrientInfo(BaseModel):
    class_name: str
    grams: float
    
    # Makronutrien
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    omega_3_g: float = 0.0

    # Mineral
    magnesium_mg: float = 0.0
    zinc_mg: float = 0.0
    iron_mg: float = 0.0
    calcium_mg: float = 0.0

    # Vitamin
    vitamin_c_mg: float = 0.0
    vitamin_b_complex_mg: float = 0.0
    vitamin_d_mcg: float = 0.0
    vitamin_b12_mcg: float = 0.0
    vitamin_a_mcg: float = 0.0
    folic_acid_mcg: float = 0.0

    source: str = "gemini"


class DetectionResult(BaseModel):
    image_id: str
    detected_classes: List[SegmentedFood]
    nutrients: List[NutrientInfo]
    
    totals: Dict[str, float] 
    inference_time_ms: float

class GramsOverride(BaseModel):
    image_id:          str
    grams_map:         Dict[str, float]        
    serving_style_map: Dict[str, ServingStyle] = {}

class RemoveRequest(BaseModel):
    image_id:       str
    detection_id:   str
    original_class: str
    mask_polygon:   List[List[float]]       

class MissingFoodRequest(BaseModel):
    image_id:  str
    food_name: str = Field(min_length=2, max_length=50, description="food name from user")
    tap_x:     float = Field(ge=0.0, le=1.0)
    tap_y:     float = Field(ge=0.0, le=1.0)

class HealthResponse(BaseModel):
    status:  str
    model:   str
    classes: List[str]
    version: str
