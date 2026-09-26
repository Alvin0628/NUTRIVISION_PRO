from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import storage

class Gender(str, Enum):
    MALE   = "male"
    FEMALE = "female"

class ActivityLevel(str, Enum):
    SEDENTARY   = "sedentary"   
    LIGHT       = "light"       
    MODERATE    = "moderate"    
    ACTIVE      = "active"      
    VERY_ACTIVE = "very_active"

class Goal(str, Enum):
    CUTTING     = "cutting"     
    MAINTENANCE = "maintenance" 
    BULKING     = "bulking"     

_ACTIVITY_MULTIPLIER = {
    ActivityLevel.SEDENTARY:   1.2,
    ActivityLevel.LIGHT:       1.375,
    ActivityLevel.MODERATE:    1.55,
    ActivityLevel.ACTIVE:      1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}

_GOAL_CALORIE_ADJUSTMENT = {
    Goal.CUTTING:     -500,
    Goal.MAINTENANCE:    0,
    Goal.BULKING:     +350,
}

_PROTEIN_G_PER_KG = {
    Goal.CUTTING:     2.2,
    Goal.MAINTENANCE: 1.8,
    Goal.BULKING:     2.0,
}

FAT_PERCENTAGE = 0.25  

_AKG_MICRONUTRIENTS = {
    Gender.MALE: {
        "fiber_g": 37.0,
        "omega_3_g": 1.6,
        "magnesium_mg": 360.0,
        "zinc_mg": 11.0,
        "iron_mg": 9.0,
        "calcium_mg": 1000.0,
        "vitamin_c_mg": 90.0,
        "vitamin_b_complex_mg": 1.3,
        "vitamin_d_mcg": 15.0,
        "vitamin_b12_mcg": 4.0,
        "vitamin_a_mcg": 650.0,
        "folic_acid_mcg": 400.0,
    },
    Gender.FEMALE: {
        "fiber_g": 32.0,
        "omega_3_g": 1.1,
        "magnesium_mg": 330.0,
        "zinc_mg": 8.0,
        "iron_mg": 18.0,
        "calcium_mg": 1000.0,
        "vitamin_c_mg": 75.0,
        "vitamin_b_complex_mg": 1.1,
        "vitamin_d_mcg": 15.0,
        "vitamin_b12_mcg": 4.0,
        "vitamin_a_mcg": 600.0,
        "folic_acid_mcg": 400.0,
    },
}

class UserProfile(BaseModel):
    uid:            str
    gender:         Gender
    age:            int         = Field(ge=10, le=100, description="Age in year")
    height_cm:      float       = Field(gt=0,  description="Height in cm")
    weight_kg:      float       = Field(gt=0,  description="Weight in kg")
    activity_level: ActivityLevel
    goal:           Goal

class DailyTarget(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    omega_3_g: float
    magnesium_mg: float
    zinc_mg: float
    iron_mg: float
    calcium_mg: float
    vitamin_c_mg: float
    vitamin_b_complex_mg: float
    vitamin_d_mcg: float
    vitamin_b12_mcg: float
    vitamin_a_mcg: float
    folic_acid_mcg: float
    bmr: float
    tdee: float
    goal: str
    activity_level: str

def calculate_bmr(profile: UserProfile) -> float:
    base = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age
    return base + 5 if profile.gender == Gender.MALE else base - 161

def calculate_daily_target(profile: UserProfile) -> DailyTarget:
    bmr = calculate_bmr(profile)
    tdee = bmr * _ACTIVITY_MULTIPLIER[profile.activity_level]
    target_calories = tdee + _GOAL_CALORIE_ADJUSTMENT[profile.goal]

    protein_g = _PROTEIN_G_PER_KG[profile.goal] * profile.weight_kg
    fat_g = (target_calories * FAT_PERCENTAGE) / 9
    carbs_g = max(target_calories - protein_g * 4 - fat_g * 9, 0) / 4

    micronutrients = _AKG_MICRONUTRIENTS[profile.gender]

    return DailyTarget(
        calories=round(target_calories, 1),
        protein_g=round(protein_g, 1),
        fat_g=round(fat_g, 1),
        carbs_g=round(carbs_g, 1),
        **{k: round(v, 2) for k, v in micronutrients.items()},
        bmr=round(bmr, 1),
        tdee=round(tdee, 1),
        goal=profile.goal.value,
        activity_level=profile.activity_level.value,
    )

def save_profile(profile: UserProfile) -> None:
    storage.save_user_profile(profile.uid, profile.model_dump())

def get_profile(uid: str) -> Optional[UserProfile]:
    data = storage.load_user_profile(uid)
    return UserProfile(**data) if data else None