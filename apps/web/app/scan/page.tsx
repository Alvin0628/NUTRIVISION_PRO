"use client";

import { useState, type ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { FoodCard } from "@/components/FoodCard";
import { api, ApiError } from "@/lib/api-client";
import type { DetectionResult, SegmentedFood } from "@/lib/types";
import { MACRO_KEYS, MICRO_KEYS, NUTRIENT_META, formatNutrientValue } from "@/lib/nutrients";

function ScanContent() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [missingName, setMissingName] = useState("");
  const [showTotalDetail, setShowTotalDetail] = useState(false);
  const router = useRouter();

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  }

  async function handleScan() {
    if (!file) return;
    setScanning(true);
    setError(null);
    try {
      setResult(await api.predict(file));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal scan foto, coba lagi.");
    } finally {
      setScanning(false);
    }
  }

  async function handleGramsCommit(className: string, grams: number) {
    if (!result) return;
    try {
      setResult(await api.recalculate(result.image_id, { [className]: grams }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal update gramasi.");
    }
  }

  async function handleRemove(item: SegmentedFood) {
    if (!result) return;
    try {
      setResult(
        await api.removeDetection({
          image_id: result.image_id,
          detection_id: item.detection_id,
          original_class: item.class_name,
          mask_polygon: item.mask_polygon,
        })
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal menghapus item.");
    }
  }

  async function handleAddMissing() {
    if (!result || !missingName.trim()) return;
    try {
      setResult(
        await api.reportMissing({
          image_id: result.image_id,
          food_name: missingName.trim(),
          tap_x: 0.5,
          tap_y: 0.5,
        })
      );
      setMissingName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal menambah item.");
    }
  }

  async function handleSave() {
    if (!result) return;
    setSaving(true);
    setError(null);
    try {
      await api.logMeal(result.image_id);
      router.push("/diary");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal menyimpan ke diary.");
    } finally {
      setSaving(false);
    }
  }

  // 1 card per class_name walau instance-nya lebih dari 1 di foto yang sama.
  const uniqueItems = result
    ? Array.from(new Map(result.detected_classes.map((it) => [it.class_name, it])).values())
    : [];

  // Data gizi per class_name — dulu di-fetch tapi tidak pernah dipakai di UI.
  const nutrientByClass = new Map((result?.nutrients ?? []).map((n) => [n.class_name, n]));

  return (
    <main className="page-shell">
      <div className="page-container">
        <p className="eyebrow">Nutrition intelligence</p>
        <h1 className="display-title">See what&apos;s on your plate.</h1>
        <p className="lede">
          Upload a photo of your meal. NutriVision breaks it down into something you can actually use.
        </p>

        <div className="scan-grid">
          <section className="card upload-card">
            <label className="upload-zone">
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleFileChange}
              />
              {previewUrl ? (
                <img src={previewUrl} alt="Preview foto makanan" />
              ) : (
                <span className="upload-empty">
                  <span className="upload-icon">+</span>
                  <strong>Drop your meal here</strong>
                  <span className="small-note">JPG, PNG, atau WEBP · klik untuk memilih foto</span>
                </span>
              )}
            </label>
            <div className="scan-actions">
              {file && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setFile(null);
                    setPreviewUrl(null);
                    setResult(null);
                  }}
                >
                  Ganti foto
                </button>
              )}
              {file && !result && (
                <button type="button" onClick={handleScan} disabled={scanning} className="btn-primary">
                  {scanning ? "Menganalisis..." : "Analisis piring"}
                </button>
              )}
            </div>
          </section>

          <section className="results-panel">
            <div className="results-heading">
              <div>
                <h2>{result ? "Your plate, decoded" : "Your results"}</h2>
                <p>{result ? `${uniqueItems.length} item makanan terdeteksi` : "Hasil analisis akan tampil di sini"}</p>
              </div>
            </div>

            {error && <div className="alert-error error-banner">{error}</div>}

            {result ? (
              <>
                <div className="card nutrition-total">
                  <p className="eyebrow">Total estimasi</p>
                  <div className="calorie-number">
                    {Math.round(result.totals.total_calories ?? 0)}{" "}
                    <span style={{ fontSize: 16, letterSpacing: 0 }}>kkal</span>
                  </div>
                  <div className="macro-row">
                    {MACRO_KEYS.filter((k) => k !== "calories").map((key) => (
                      <div key={key} className="macro">
                        <span>{NUTRIENT_META[key].label}</span>
                        <strong>
                          {formatNutrientValue(result.totals[`total_${key}`] ?? 0)}
                          {NUTRIENT_META[key].unit === "g" ? "g" : ` ${NUTRIENT_META[key].unit}`}
                        </strong>
                      </div>
                    ))}
                  </div>

                  <button
                    type="button"
                    className="total-detail-toggle"
                    onClick={() => setShowTotalDetail((v) => !v)}
                    aria-expanded={showTotalDetail}
                  >
                    {showTotalDetail ? "Sembunyikan detail nutrisi" : "Lihat 12 nutrisi lainnya"}
                  </button>

                  {showTotalDetail && (
                    <div className="total-detail-grid">
                      {MICRO_KEYS.map((key) => (
                        <div key={key} className="total-detail-row">
                          <span>{NUTRIENT_META[key].label}</span>
                          <strong>
                            {formatNutrientValue(result.totals[`total_${key}`] ?? 0)} {NUTRIENT_META[key].unit}
                          </strong>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {uniqueItems.map((item) => (
                  <FoodCard
                    key={item.class_name}
                    item={item}
                    nutrient={nutrientByClass.get(item.class_name)}
                    onGramsCommit={handleGramsCommit}
                    onRemove={handleRemove}
                  />
                ))}

                <div className="card" style={{ padding: 14 }}>
                  <label className="field-label">
                    Ada yang terlewat?
                    <div style={{ display: "flex", gap: 8 }}>
                      <input
                        className="field"
                        placeholder="Contoh: sambal"
                        value={missingName}
                        onChange={(e) => setMissingName(e.target.value)}
                      />
                      <button onClick={handleAddMissing} className="btn-secondary">
                        Tambah
                      </button>
                    </div>
                  </label>
                </div>

                <button onClick={handleSave} disabled={saving} className="btn-primary">
                  {saving ? "Menyimpan..." : "Simpan ke diary"}
                </button>
              </>
            ) : (
              <div className="card empty-state">
                <p>Upload foto untuk melihat estimasi kalori dan makro makananmu.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

export default function ScanPage() {
  return (
    <ProtectedRoute>
      <ScanContent />
    </ProtectedRoute>
  );
}
