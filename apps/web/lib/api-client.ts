import { getIdToken } from "./firebase";
import type {
  DailySummary,
  DailyTarget,
  DetectionResult,
  MissingFoodRequest,
  RemoveRequest,
  UserProfileInput,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

/**
 * Satu jalur untuk semua request ke backend. `requiresAuth: true` akan
 * melampirkan Bearer token Firebase secara otomatis — pemanggil (halaman)
 * tidak pernah perlu tahu soal token sama sekali.
 */
async function request<T>(
  path: string,
  options: RequestInit = {},
  requiresAuth = false
): Promise<T> {
  const headers = new Headers(options.headers);

  if (requiresAuth) {
    const token = await getIdToken();
    if (!token) {
      throw new ApiError(401, "Kamu belum login.");
    }
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}) as { detail?: string });
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }

  return res.json() as Promise<T>;
}

function json(body: unknown): RequestInit {
  return { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export const api = {
  // --- Detection (tidak butuh login — sengaja disamakan dengan backend) ---

  predict(file: File): Promise<DetectionResult> {
    const form = new FormData();
    form.append("file", file);
    return request<DetectionResult>("/predict", { method: "POST", body: form });
  },

  recalculate(
    imageId: string,
    gramsMap: Record<string, number>,
    servingStyleMap: Record<string, string> = {}
  ): Promise<DetectionResult> {
    return request<DetectionResult>("/recalculate", {
      method: "POST",
      ...json({ image_id: imageId, grams_map: gramsMap, serving_style_map: servingStyleMap }),
    });
  },

  // --- Feedback ---

  removeDetection(req: RemoveRequest): Promise<DetectionResult> {
    return request<DetectionResult>("/feedback/remove", { method: "POST", ...json(req) });
  },

  reportMissing(req: MissingFoodRequest): Promise<DetectionResult> {
    return request<DetectionResult>("/feedback/missing", { method: "POST", ...json(req) });
  },

  // --- Users (butuh login) ---

  saveProfile(profile: UserProfileInput): Promise<DailyTarget> {
    return request<DailyTarget>("/users", { method: "POST", ...json(profile) }, true);
  },

  getTarget(): Promise<DailyTarget> {
    return request<DailyTarget>("/users/target", {}, true);
  },

  // --- Diary (butuh login) ---

  logMeal(imageId: string) {
    return request<{ uid: string; image_id: string; logged_at: string }>(
      "/log",
      { method: "POST", ...json({ image_id: imageId }) },
      true
    );
  },

  getDiary(date?: string): Promise<DailySummary> {
    const qs = date ? `?date=${encodeURIComponent(date)}` : "";
    return request<DailySummary>(`/diary${qs}`, {}, true);
  },

  getHistoryDates(): Promise<{ dates: string[] }> {
    return request<{ dates: string[] }>("/diary/history-dates", {}, true);
  },
};
