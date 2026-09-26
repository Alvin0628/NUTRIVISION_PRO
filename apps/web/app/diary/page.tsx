"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { DiaryCalendar, todayIso } from "@/components/Calendar";
import { api, ApiError } from "@/lib/api-client";
import { NUTRIENT_KEYS, type DailySummary } from "@/lib/types";
import { NUTRIENT_META, formatNutrientValue } from "@/lib/nutrients";

function prettifyFoodName(name: string): string {
  return name.replace(/_/g, " ");
}

function formatEntryTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
}

function DiaryContent() {
  const [dates, setDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | undefined>(undefined);
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getHistoryDates()
      .then((res) => setDates(res.dates))
      .catch(() => {
        /* daftar tanggal cuma pemanis penanda kalender — kalau gagal, halaman tetap jalan untuk "hari ini" */
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getDiary(selectedDate)
      .then(setSummary)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Belum ada profile tersimpan, atau gagal memuat diary.")
      )
      .finally(() => setLoading(false));
  }, [selectedDate]);

  const hasEntries = !!summary && summary.n_meals > 0;

  return (
    <main className="page-shell">
      <div className="page-container">
        <div className="diary-header">
          <div>
            <p className="eyebrow">Your daily overview</p>
            <h1 className="page-title">Progress harian.</h1>
            <p className="lede">
              Small choices add up. See how today&apos;s meals map to your personal targets.
            </p>
          </div>
        </div>

        <div className="diary-layout">
          <DiaryCalendar
            markedDates={dates}
            selectedDate={selectedDate ?? todayIso()}
            onSelect={setSelectedDate}
          />

          <div className="diary-content">
            {loading && <div className="loading-state">Memuat ringkasan...</div>}
            {error && <div className="alert-error error-banner">{error}</div>}

            {summary && !loading && !hasEntries && (
              <div className="card empty-state">
                <p>Belum ada makanan tercatat di tanggal {summary.date}.</p>
              </div>
            )}

            {summary && !loading && hasEntries && (
              <>
                <p className="small-note">
                  {summary.date} · {summary.n_meals} kali makan tercatat
                </p>

                <div className="diary-summary">
                  {(["calories", "protein_g", "carbs_g", "fat_g"] as const).map((key) => (
                    <div key={key} className="card stat-card">
                      <div className="stat-label">{NUTRIENT_META[key].label}</div>
                      <div className="stat-value">
                        {formatNutrientValue(summary.consumed_totals[key] ?? 0)}
                        <span style={{ fontSize: 12, fontWeight: 400 }}>
                          {" "}
                          / {formatNutrientValue(summary.target[key])} {NUTRIENT_META[key].unit}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <section className="card meal-history">
                  <h2>Riwayat makan</h2>
                  <div className="meal-list">
                    {summary.entries.map((entry) => (
                      <div key={entry.image_id} className="meal-entry">
                        <span className="meal-time">{formatEntryTime(entry.logged_at)}</span>
                        <span className="meal-items">
                          {entry.food_items.map(prettifyFoodName).join(", ")}
                        </span>
                        <span className="meal-cal">{Math.round(entry.totals.total_calories ?? 0)} kkal</span>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="card nutrient-list">
                  <div style={{ gridColumn: "1/-1", marginBottom: 4 }}>
                    <h2 style={{ margin: 0, fontSize: 18 }}>Nutrient detail</h2>
                    <p className="small-note">Konsumsi dibanding target harianmu.</p>
                  </div>
                  {NUTRIENT_KEYS.map((key) => {
                    const consumed = summary.consumed_totals[key] ?? 0;
                    const target = summary.target[key] ?? 0;
                    const pct = Math.min(100, Math.round((summary.progress[key] ?? 0) * 100));
                    const { label, unit } = NUTRIENT_META[key];
                    return (
                      <div key={key} className="nutrient-item">
                        <div className="nutrient-meta">
                          <span>{label}</span>
                          <strong>
                            {formatNutrientValue(consumed)} / {formatNutrientValue(target)} {unit}
                          </strong>
                        </div>
                        <div className="progress-track">
                          <div className="progress-fill" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </section>
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default function DiaryPage() {
  return (
    <ProtectedRoute>
      <DiaryContent />
    </ProtectedRoute>
  );
}
