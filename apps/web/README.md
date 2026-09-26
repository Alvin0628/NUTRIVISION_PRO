# NutriVision Pro — Web (Next.js)

## Setup

```bash
npm install
cp .env.local.example .env.local   # lalu isi 4 variabelnya (lihat komentar di file itu)
npm run dev
```

Buka http://localhost:3000 — otomatis redirect ke `/login` kalau belum masuk, atau `/scan` kalau sudah.

## Struktur

```
app/
├── (auth)/login/       — signInWithEmailAndPassword
├── (auth)/register/    — createUserWithEmailAndPassword → redirect ke /profile
├── scan/                — upload foto → /predict → FoodCard per class_name → /log
├── diary/                — progress 16 nutrisi vs target, dropdown history
└── profile/              — form data diri → POST /users → tampilkan DailyTarget

components/
├── AuthProvider.tsx      — context status login, dipakai lewat useAuth()
├── ProtectedRoute.tsx    — redirect ke /login kalau belum auth, render Navbar
├── Navbar.tsx
└── FoodCard.tsx          — 1 card per class_name, slider gram (commit on release)

lib/
├── firebase.ts           — init Firebase, getFirebaseAuth() LAZY (baca komentar di file)
├── firebase-errors.ts    — mapping error code Firebase → pesan Indonesia
├── api-client.ts         — satu-satunya tempat fetch() ke backend, semua endpoint
└── types.ts               — tipe TS 1:1 dengan schemas.py backend
```

## Sudah diverifikasi jalan (bukan cuma ditulis)

`npm install`, `npx tsc --noEmit`, `npx eslint .`, dan `npm run build` semuanya
sudah dijalankan dan lolos bersih sebelum kode ini diserahkan.

## Yang SENGAJA belum dibuat (bukan lupa)

- **Tap-to-mark di foto untuk "makanan yang terlewat"** — sekarang `tap_x`/`tap_y`
  di-hardcode ke tengah gambar (0.5, 0.5). Backend sudah siap terima koordinat asli;
  perlu komponen overlay gambar dengan handler klik untuk versi penuhnya.
- **Proteksi route di level server (middleware.ts + session cookie)** — proteksi
  sekarang murni client-side (cukup untuk MVP karena backend tetap verifikasi
  token sendiri di tiap endpoint). Tambahkan kalau nanti butuh data yang tidak
  boleh sempat ter-render sebelum tahu status login.
- **Kalender visual untuk history** — sekarang masih dropdown `<select>` tanggal,
  bukan komponen kalender.

## Env vars (`.env.local`)

| Variabel | Dari mana |
|---|---|
| `NEXT_PUBLIC_API_URL` | URL backend FastAPI kamu |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | sama dengan `FIREBASE_WEB_API_KEY` di `apps/api/.env` |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Console → Project settings → General → Your apps |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | sama seperti di atas |
