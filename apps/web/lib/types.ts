// Tipe-tipe ini SENGAJA dicocokkan 1:1 dengan schemas.py / users.py / diary.py
// di backend. Kalau backend berubah, ubah di sini juga — supaya jangan ada
// asumsi struktur data yang diam-diam berbeda antara FE dan BE (sumber bug
// paling umum di integrasi FE-BE).

export type Gender = "male" | "female";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "very_active";
export type Goal = "cutting" | "maintenance" | "bulking";
export type ServingStyle = "fried" | "boiled" | "steamed" | "raw";

// 16 nutrisi yang dipatok — urutan sengaja disamakan dengan NUTRIENT_KEYS di nutrition.py
export type NutrientKey =
  | "calories"
  | "protein_g"
  | "carbs_g"
  | "fat_g"
  | "fiber_g"
  | "omega_3_g"
  | "magnesium_mg"
  | "zinc_mg"
  | "iron_mg"
  | "calcium_mg"
  | "vitamin_c_mg"
  | "vitamin_b_complex_mg"
  | "vitamin_d_mcg"
  | "vitamin_b12_mcg"
  | "vitamin_a_mcg"
  | "folic_acid_mcg";

export const NUTRIENT_KEYS: NutrientKey[] = [
  "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "omega_3_g",
  "magnesium_mg", "zinc_mg", "iron_mg", "calcium_mg", "vitamin_c_mg",
  "vitamin_b_complex_mg", "vitamin_d_mcg", "vitamin_b12_mcg", "vitamin_a_mcg", "folic_acid_mcg",
];

// Nilai per nutrisi TANPA prefix — dipakai di DailyTarget, DailySummary.consumed_totals,
// DailySummary.remaining, DailySummary.progress
export type NutrientAmounts = Record<NutrientKey, number>;

// Nilai per nutrisi DENGAN prefix "total_" — HANYA dipakai di DetectionResult.totals
// (lihat nutrition.py: get_nutrients_bulk_async menulis totals[f"total_{key}"], sementara
// diary.py men-strip prefix itu sebelum masuk ke DailySummary). Jangan disamakan.
export type PrefixedNutrientTotals = Record<`total_${NutrientKey}`, number>;

// --- Users ---

export interface UserProfileInput {
  uid: string;
  gender: Gender;
  age: number;
  height_cm: number;
  weight_kg: number;
  activity_level: ActivityLevel;
  goal: Goal;
}

export interface DailyTarget extends NutrientAmounts {
  bmr: number;
  tdee: number;
  goal: string;
  activity_level: string;
}

// --- Detection / Predict ---

export interface SegmentedFood {
  detection_id: string;
  class_name: string;
  original_class: string | null;
  confidence: number;
  bbox: number[];
  mask_area_ratio: number;
  mask_polygon: number[][];
  estimated_grams: number;
  serving_style: ServingStyle;
}

export interface NutrientInfo extends NutrientAmounts {
  class_name: string;
  grams: number;
  source: string;
}

export interface DetectionResult {
  image_id: string;
  detected_classes: SegmentedFood[];
  nutrients: NutrientInfo[];
  totals: PrefixedNutrientTotals;
  inference_time_ms: number;
}

// --- Feedback ---

export interface RemoveRequest {
  image_id: string;
  detection_id: string;
  original_class: string;
  mask_polygon: number[][];
}

export interface MissingFoodRequest {
  image_id: string;
  food_name: string;
  tap_x: number;
  tap_y: number;
}

// --- Diary ---

export interface DiaryEntry {
  uid: string;
  image_id: string;
  logged_at: string;
  food_items: string[];
  totals: PrefixedNutrientTotals;
}

export interface DailySummary {
  date: string;
  entries: DiaryEntry[];
  n_meals: number;
  consumed_totals: Partial<NutrientAmounts>;
  target: DailyTarget;
  remaining: Partial<NutrientAmounts>;
  progress: Partial<NutrientAmounts>; // rasio 0..1 (bisa >1 kalau sudah lewat target)
}
