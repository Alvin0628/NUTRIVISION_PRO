"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";
import { mapFirebaseAuthError } from "@/lib/firebase-errors";

export default function RegisterPage() {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(false); const router = useRouter();
  async function handleSubmit(e: FormEvent) { e.preventDefault(); setError(null); setLoading(true); try { await createUserWithEmailAndPassword(getFirebaseAuth(), email, password); router.replace("/profile"); } catch (err) { setError(mapFirebaseAuthError(err)); } finally { setLoading(false); } }
  return <main className="auth-layout"><aside className="auth-aside"><div><div className="brand-mark" style={{ color: "white" }}><span className="brand-symbol">N</span><span>NutriVision</span></div><p className="eyebrow" style={{ marginTop: 56 }}>Start small</p></div><p className="auth-quote">Better habits begin with better information.</p><p className="small-note" style={{ color: "#d8e7db" }}>Scan. Understand. Make it yours.</p></aside><section className="auth-main"><div className="auth-form-wrap"><p className="eyebrow">New here?</p><h1 className="page-title">Mulai lebih mindful.</h1><p className="lede">Buat profil sederhana, lalu kami bantu kamu melihat pola di balik setiap piring.</p><form onSubmit={handleSubmit} className="auth-form"><label className="field-label">Email<input className="field" type="email" autoComplete="email" required placeholder="nama@email.com" value={email} onChange={(e) => setEmail(e.target.value)} /></label><label className="field-label">Password<input className="field" type="password" autoComplete="new-password" required minLength={6} placeholder="Minimal 6 karakter" value={password} onChange={(e) => setPassword(e.target.value)} /></label>{error && <div className="alert-error">{error}</div>}<button type="submit" disabled={loading} className="btn-primary">{loading ? "Membuat akun..." : "Buat akun"}</button></form><p className="auth-footer">Sudah punya akun? <Link href="/login">Masuk di sini</Link></p></div></section></main>;
}
