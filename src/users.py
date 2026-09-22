"""
users.py — User profiles + BMR/TDEE/daily target calculations.

Formula: Mifflin-St Jeor (1990)
- Recommended by the Academy of Nutrition and Dietetics
- ~5% error rate vs. Harris-Benedict, which overestimates by 5–15%

Activity multiplier (Compendium of Physical Activities):
sedentary   = 1.2   (office job, no exercise)
light       = 1.375 (light exercise 1–3x/week)
moderate    = 1.55  (moderate exercise 3–5x/week)
active      = 1.725 (heavy exercise 6–7x/week)
very_active = 1.9   (athlete/heavy physical labor)

Calorie adjustment for goals (ACSM guidelines):
cutting     = TDEE - 500 kcal/day → ~0.5kg/week loss (safe, avoids muscle loss)
maintenance = TDEE
bulking     = TDEE + 350 kcal/day → lean bulk, minimizes fat gain

Protein target (ISSN Position Stand 2017):
cutting     = 2.2g/kg → preserves muscle during deficit
maintenance = 1.8g/kg → optimal muscle synthesis
bulking     = 2.0g/kg → supports hypertrophy

Fat: 25% of total calories (minimum for hormonal function)
Carbs: remaining calories after protein and fat requirements are met
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import storage

class Gender(str, Enum):
    MALE   = "male"
    FEMALE = "female"

class ActivityLevel(str, Enum):
    SEDENTARY  = "sedentary"   
    LIGHT      = "light"       
    MODERATE   = "moderate"    
    ACTIVE     = "active"      
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

class UserProfile(BaseModel):
    uid:      str
    gender:         Gender
    age:            int         = Field(ge=10, le=100, description="Age in year")
    height_cm:      float       = Field(gt=0,  description="Height in cm")
    weight_kg:      float       = Field(gt=0,  description="Weight in kg")
    activity_level: ActivityLevel
    goal:           Goal

class DailyTarget(BaseModel):
    bmr:              float   
    tdee:             float  
    target_calories:  float 
    target_protein_g: float
    target_fat_g:     float
    target_carbs_g:   float
    goal:             str
    activity_level:   str

def calculate_bmr(profile: UserProfile) -> float:
    """
    Mifflin-St Jeor:
      Male:   10W + 6.25H - 5A + 5
      Female: 10W + 6.25H - 5A - 161
    W=kg, H=cm, A=age
    """
    base = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age
    return base + 5 if profile.gender == Gender.MALE else base - 161

def calculate_daily_target(profile: UserProfile) -> DailyTarget:
    bmr             = calculate_bmr(profile)
    tdee            = bmr * _ACTIVITY_MULTIPLIER[profile.activity_level]
    target_calories = tdee + _GOAL_CALORIE_ADJUSTMENT[profile.goal]

    protein_g = _PROTEIN_G_PER_KG[profile.goal] * profile.weight_kg

    fat_g = (target_calories * FAT_PERCENTAGE) / 9 

    carbs_g = max(target_calories - protein_g * 4 - fat_g * 9, 0) / 4

    return DailyTarget(
        bmr=round(bmr, 1),
        tdee=round(tdee, 1),
        target_calories=round(target_calories, 1),
        target_protein_g=round(protein_g, 1),
        target_fat_g=round(fat_g, 1),
        target_carbs_g=round(carbs_g, 1),
        goal=profile.goal.value,
        activity_level=profile.activity_level.value,
    )

def save_profile(profile: UserProfile) -> None:
    storage.save_user_profile(profile.uid, profile.dict())

def get_profile(uid: str) -> Optional[UserProfile]:
    data = storage.load_user_profile(uid)
    return UserProfile(**data) if data else None
