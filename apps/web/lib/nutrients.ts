import { NUTRIENT_KEYS, type NutrientKey } from "./types";

export const NUTRIENT_META: Record<NutrientKey, { label: string; unit: string }> = {
  calories: { label: "Kalori", unit: "kkal" },
  protein_g: { label: "Protein", unit: "g" },
  carbs_g: { label: "Karbohidrat", unit: "g" },
  fat_g: { label: "Lemak", unit: "g" },
  fiber_g: { label: "Serat", unit: "g" },
  omega_3_g: { label: "Omega-3", unit: "g" },
  magnesium_mg: { label: "Magnesium", unit: "mg" },
  zinc_mg: { label: "Zinc", unit: "mg" },
  iron_mg: { label: "Zat besi", unit: "mg" },
  calcium_mg: { label: "Kalsium", unit: "mg" },
  vitamin_c_mg: { label: "Vitamin C", unit: "mg" },
  vitamin_b_complex_mg: { label: "Vitamin B kompleks", unit: "mg" },
  vitamin_d_mcg: { label: "Vitamin D", unit: "mcg" },
  vitamin_b12_mcg: { label: "Vitamin B12", unit: "mcg" },
  vitamin_a_mcg: { label: "Vitamin A", unit: "mcg" },
  folic_acid_mcg: { label: "Asam folat", unit: "mcg" },
};

// 4 makro utama yang selalu tampil di ringkasan; sisanya (12 mikronutrien)
// masuk ke bagian "detail lengkap" yang bisa di-expand — supaya kartu tidak
// penuh angka tapi datanya tetap semua bisa diakses.
export const MACRO_KEYS: NutrientKey[] = ["calories", "protein_g", "carbs_g", "fat_g"];
export const MICRO_KEYS: NutrientKey[] = NUTRIENT_KEYS.filter((k) => !MACRO_KEYS.includes(k));

export function formatNutrientValue(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
