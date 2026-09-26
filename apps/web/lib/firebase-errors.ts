import { FirebaseError } from "firebase/app";

export function mapFirebaseAuthError(err: unknown): string {
  if (!(err instanceof FirebaseError)) return "Terjadi kesalahan, coba lagi.";

  switch (err.code) {
    case "auth/invalid-credential":
    case "auth/wrong-password":
    case "auth/user-not-found":
      return "Email atau password salah.";
    case "auth/invalid-email":
      return "Format email tidak valid.";
    case "auth/email-already-in-use":
      return "Email ini sudah terdaftar — coba masuk saja.";
    case "auth/weak-password":
      return "Password minimal 6 karakter.";
    case "auth/too-many-requests":
      return "Terlalu banyak percobaan, coba lagi nanti.";
    default:
      return "Gagal memproses, coba lagi.";
  }
}
