"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/how-it-works", label: "Cara kerja" },
  { href: "/features", label: "Fitur" },
  { href: "/about", label: "Tentang" },
];

export function PublicNav() {
  const pathname = usePathname();

  return (
    <header className="public-nav">
      <div className="public-nav-inner">
        <Link href="/" className="public-brand" aria-label="NutriVision beranda">
          <span className="brand-chip">N</span>
          <span>NutriVision</span>
        </Link>
        <nav className="public-links" aria-label="Navigasi informasi">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className={pathname === link.href ? "is-active" : ""}>
              {link.label}
            </Link>
          ))}
        </nav>
        <Link href="/login" className="btn-primary public-login">
          Masuk <span aria-hidden="true">→</span>
        </Link>
      </div>
    </header>
  );
}