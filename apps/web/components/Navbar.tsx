"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { signOut } from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";
import { useAuth } from "./AuthProvider";

const LINKS = [
  { href: "/scan", label: "Scan makanan" },
  { href: "/diary", label: "Diary" },
  { href: "/profile", label: "Profil" },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();

  async function handleLogout() {
    await signOut(getFirebaseAuth());
    router.replace("/login");
  }

  return (
    <header className="nav-shell">
      <div className="nav-inner">
        <Link href="/scan" className="brand-mark" aria-label="NutriVision beranda">
          <span className="brand-symbol">N</span><span>NutriVision</span>
        </Link>
        <nav className="nav-links desktop-nav" aria-label="Navigasi utama">
          {LINKS.map((link) => <Link key={link.href} href={link.href} className={`nav-link ${pathname === link.href ? "nav-link-active" : ""}`}>{link.label}</Link>)}
        </nav>
        <div className="nav-user">
          <span className="nav-email desktop-nav">{user?.email}</span>
          <button onClick={handleLogout} className="nav-logout">Keluar</button>
        </div>
      </div>
      <nav className="nav-inner mobile-nav" aria-label="Navigasi mobile">
        {LINKS.map((link) => <Link key={link.href} href={link.href} className={`nav-link ${pathname === link.href ? "nav-link-active" : ""}`}>{link.label}</Link>)}
      </nav>
    </header>
  );
}
