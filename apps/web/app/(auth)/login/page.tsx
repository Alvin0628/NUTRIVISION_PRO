"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signInWithEmailAndPassword } from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";
import { mapFirebaseAuthError } from "@/lib/firebase-errors";

export default function LoginPage() {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(false); const router = useRouter();
  async function handleSubmit(e: FormEvent) { e.preventDefault(); setError(null); setLoading(true); try { await signInWithEmailAndPassword(getFirebaseAuth(), email, password); router.replace("/scan"); } catch (err) { setError(mapFirebaseAuthError(err)); } finally { setLoading(false); } }
  return <main className="auth-layout"><aside className="auth-aside"><div><div className="brand-mark" style={{ color: "white" }}><span className="brand-symbol">N</span><span>NutriVision</span></div><p className="eyebrow" style={{ marginTop: 56 }}>Eat with clarity</p></div><p className="auth-quote">Your plate has a story. We help you read it.</p><p className="small-note" style={{ color: "#d8e7db" }}>AI food intelligence for everyday decisions.</p></aside><section className="auth-main"><div className="auth-form-wrap"><p className="eyebrow">Welcome back</p><h1 className="page-title">Masuk ke akunmu.</h1><p className="lede">Lanjutkan perjalanan makan yang lebih sadar dan seimbang.</p><form onSubmit={handleSubmit} className="auth-form"><label className="field-label">Email<input className="field" type="email" autoComplete="username" required placeholder="nama@email.com" value={email} onChange={(e) => setEmail(e.target.value)} /></label><label className="field-label">Password<input className="field" type="password" autoComplete="current-password" required placeholder="Masukkan password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>{error && <div className="alert-error">{error}</div>}<button type="submit" disabled={loading} className="btn-primary">{loading ? "Memproses..." : "Masuk ke NutriVision"}</button></form><p className="auth-footer">Belum punya akun? <Link href="/register">Buat akun baru</Link></p></div></section></main>;
}
