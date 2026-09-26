"use client";

import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";
import { PublicNav } from "@/components/PublicNav";

export default function RootPage() {
  const { user, loading } = useAuth();

  return (
    <div className="public-page home-page">
      <PublicNav />
      <main>
        <section className="hero-section page-container">
          <div className="hero-copy">
            <p className="eyebrow">Nutrition intelligence, with care</p>
            <h1>
              Lihat makananmu dengan <em>lebih jernih.</em>
            </h1>
            <p className="lede">
              NutriVision membaca isi piring dari satu foto, lalu mengubahnya menjadi informasi yang tenang dan bisa kamu gunakan.
            </p>
            <div className="hero-actions">
              {!loading && (
                <Link href={user ? "/scan" : "/register"} className="btn-primary">
                  {user ? "Scan makanan" : "Mulai dengan gratis"} <span aria-hidden="true">→</span>
                </Link>
              )}
              <Link href="/how-it-works" className="btn-secondary">Cara kerja</Link>
            </div>
          </div>
          <div className="hero-art" aria-label="Ilustrasi piring dan nutrisi">
            <div className="plate-art"><span className="plate-center" /></div>
            <div className="hero-badge"><strong>74 g</strong><span>protein teridentifikasi</span></div>
          </div>
        </section>

        <section className="feature-band page-container">
          <p className="eyebrow">A calmer way to track</p>
          <h2>Informasi yang mengikuti kehidupan nyata.</h2>
          <div className="feature-list">
            <div className="feature-item">
              <span className="feature-mark" aria-hidden="true">01</span>
              <h3>Foto, bukan input panjang</h3>
              <p>Mulai dari apa yang sudah ada di piringmu. Sesuaikan detail hanya jika perlu.</p>
            </div>
            <div className="feature-item">
              <span className="feature-mark" aria-hidden="true">02</span>
              <h3>Angka yang punya konteks</h3>
              <p>Kalori, makro, dan nutrisi harian dibandingkan dengan target personalmu.</p>
            </div>
            <div className="feature-item">
              <span className="feature-mark" aria-hidden="true">03</span>
              <h3>Kebiasaan tanpa hukuman</h3>
              <p>Simpan meal ke diary dan lihat pola dengan rasa ingin tahu, bukan rasa bersalah.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
