import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { AuthProvider } from "@/components/AuthProvider";
import "./globals.css";
import "./brand.css";

export const metadata: Metadata = {
  title: "NutriVision — Understand what you eat",
  description: "AI-powered food scanning and daily nutrition guidance for real life.",
};

export const viewport: Viewport = {
  themeColor: "#f7f8f5",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="id">
      <body><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}
