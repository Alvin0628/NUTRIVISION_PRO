"use client";

import { useState } from "react";
import type { NutrientInfo, SegmentedFood } from "@/lib/types";
import { MACRO_KEYS, MICRO_KEYS, NUTRIENT_META, formatNutrientValue } from "@/lib/nutrients";

type Props = {
  item: SegmentedFood;
  nutrient?: NutrientInfo; // undefined kalau backend belum sempat kirim nilai gizi untuk class ini
  onGramsCommit: (className: string, grams: number) => void;
  onRemove: (item: SegmentedFood) => void;
};

export function FoodCard({ item, nutrient, onGramsCommit, onRemove }: Props) {
  const [grams, setGrams] = useState(item.estimated_grams);
  const [showDetail, setShowDetail] = useState(false);

  function commit() {
    onGramsCommit(item.class_name, grams);
  }

  return (
    <article className="card food-card">
      <div className="food-card-top">
        <div>
          <div className="food-name">{item.class_name.replace(/_/g, " ")}</div>
          <div className="food-confidence">Terdeteksi dengan akurasi {Math.round(item.confidence * 100)}%</div>
        </div>
        <button type="button" onClick={() => onRemove(item)} className="remove-link">
          Hapus
        </button>
      </div>

      <div className="grams-row">
        <input
          type="range"
          min={10}
          max={500}
          step={10}
          value={grams}
          onChange={(e) => setGrams(Number(e.target.value))}
          onMouseUp={commit}
          onTouchEnd={commit}
          aria-label={`Gramasi ${item.class_name}`}
        />
        <span className="grams-value">{grams} g</span>
      </div>

      {nutrient ? (
        <>
          <div className="food-macro-row">
            {MACRO_KEYS.map((key) => (
              <div key={key} className="food-macro">
                <span>{NUTRIENT_META[key].label}</span>
                <strong>
                  {formatNutrientValue(nutrient[key] ?? 0)} {NUTRIENT_META[key].unit}
                </strong>
              </div>
            ))}
          </div>

          <button
            type="button"
            className="food-detail-toggle"
            onClick={() => setShowDetail((v) => !v)}
            aria-expanded={showDetail}
          >
            {showDetail ? "Sembunyikan detail gizi" : "Lihat detail gizi lengkap"}
          </button>

          {showDetail && (
            <div className="food-detail-grid">
              {MICRO_KEYS.map((key) => (
                <div key={key} className="food-detail-row">
                  <span>{NUTRIENT_META[key].label}</span>
                  <strong>
                    {formatNutrientValue(nutrient[key] ?? 0)} {NUTRIENT_META[key].unit}
                  </strong>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <p className="small-note food-nutrient-pending">Menghitung nilai gizi...</p>
      )}
    </article>
  );
}
