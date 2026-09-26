"use client";

import { useState } from "react";

type Props = {
  markedDates: string[]; // "YYYY-MM-DD" yang punya riwayat diary
  selectedDate: string; // "YYYY-MM-DD"
  onSelect: (date: string) => void;
};

const WEEKDAY_LABELS = ["M", "S", "S", "R", "K", "J", "S"];

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function isoDate(y: number, m: number, d: number): string {
  return `${y}-${pad(m)}-${pad(d)}`;
}

function todayIso(): string {
  const now = new Date();
  return isoDate(now.getFullYear(), now.getMonth() + 1, now.getDate());
}

export function DiaryCalendar({ markedDates, selectedDate, onSelect }: Props) {
  const markedSet = new Set(markedDates);
  const [selYear, selMonth] = selectedDate.split("-").map(Number);

  // Bulan yang SEDANG DILIHAT sengaja dipisah dari selectedDate — supaya
  // navigasi bulan (‹ ›) tidak diam-diam mengubah tanggal yang dipilih.
  const [viewYear, setViewYear] = useState(selYear);
  const [viewMonth, setViewMonth] = useState(selMonth); // 1-12

  const daysInMonth = new Date(viewYear, viewMonth, 0).getDate();
  const startWeekday = new Date(viewYear, viewMonth - 1, 1).getDay();
  const today = todayIso();

  function changeMonth(delta: number) {
    let m = viewMonth + delta;
    let y = viewYear;
    if (m > 12) {
      m = 1;
      y += 1;
    } else if (m < 1) {
      m = 12;
      y -= 1;
    }
    setViewMonth(m);
    setViewYear(y);
  }

  const monthLabel = new Date(viewYear, viewMonth - 1, 1).toLocaleDateString("id-ID", {
    month: "long",
    year: "numeric",
  });

  const cells: (string | null)[] = Array(startWeekday).fill(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(isoDate(viewYear, viewMonth, d));

  return (
    <div className="calendar card">
      <div className="calendar-header">
        <button type="button" onClick={() => changeMonth(-1)} aria-label="Bulan sebelumnya">
          ‹
        </button>
        <span className="calendar-month-label">{monthLabel}</span>
        <button type="button" onClick={() => changeMonth(1)} aria-label="Bulan berikutnya">
          ›
        </button>
      </div>

      <div className="calendar-weekdays">
        {WEEKDAY_LABELS.map((label, i) => (
          <span key={i}>{label}</span>
        ))}
      </div>

      <div className="calendar-grid">
        {cells.map((date, i) =>
          date ? (
            <button
              type="button"
              key={date}
              onClick={() => onSelect(date)}
              className={[
                "calendar-cell",
                date === selectedDate && "is-selected",
                date === today && "is-today",
                markedSet.has(date) && "has-entry",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {Number(date.slice(-2))}
            </button>
          ) : (
            <span key={`empty-${i}`} />
          )
        )}
      </div>

      <p className="calendar-legend small-note">
        <span className="calendar-dot" /> Ada riwayat makan tercatat
      </p>
    </div>
  );
}

export { todayIso };
