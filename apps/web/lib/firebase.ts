import { initializeApp, getApps, getApp, type FirebaseApp } from "firebase/app";
import { getAuth, type Auth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

let cachedApp: FirebaseApp | null = null;
let cachedAuth: Auth | null = null;

function getFirebaseApp(): FirebaseApp {
  if (!cachedApp) {
    // getApps() check ini penting di Next.js — App Router bisa re-jalankan
    // modul ini di beberapa konteks (Fast Refresh dsb), initializeApp()
    // akan throw kalau dipanggil dua kali dengan config yang sama.
    cachedApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
  }
  return cachedApp;
}

/**
 * SENGAJA berupa fungsi lazy, bukan `export const auth = getAuth(...)`.
 * `next build` melakukan satu render pass di server untuk tiap route
 * WALAUPUN komponennya "use client" — kalau getAuth() dipanggil di level
 * modul, ia langsung throw ("auth/invalid-api-key") saat build karena env
 * var Firebase belum ada nilainya di lingkungan build/CI. Dengan getter
 * ini, getAuth() baru benar-benar dieksekusi saat dipanggil dari dalam
 * useEffect/event handler di browser — yang tidak pernah jalan selama
 * render pass di server.
 */
export function getFirebaseAuth(): Auth {
  if (!cachedAuth) {
    cachedAuth = getAuth(getFirebaseApp());
  }
  return cachedAuth;
}

/**
 * Selalu pakai ini (bukan user.getIdToken() langsung) supaya token yang
 * dikirim ke backend tidak pernah expired di tengah sesi panjang — Firebase
 * SDK otomatis refresh token di background, fungsi ini hanya membaca token
 * yang lagi valid saat ini.
 */
export async function getIdToken(): Promise<string | null> {
  const user = getFirebaseAuth().currentUser;
  if (!user) return null;
  return user.getIdToken();
}
