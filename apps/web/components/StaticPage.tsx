import Link from "next/link";
import { PublicNav } from "./PublicNav";

type Section = { title: string; body: string };

export function StaticPage({
  eyebrow,
  title,
  intro,
  sections,
  cta = true,
}: {
  eyebrow: string;
  title: string;
  intro: string;
  sections: Section[];
  cta?: boolean;
}) {
  return (
    <div className="public-page">
      <PublicNav />
      <main className="static-page">
        <div className="static-hero">
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="static-intro">{intro}</p>
        </div>
        <div className="static-sections">
          {sections.map((section, index) => (
            <section className="static-section" key={section.title}>
              <span className="static-index">{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h2>{section.title}</h2>
                <p>{section.body}</p>
              </div>
            </section>
          ))}
        </div>
        {cta && (
          <div className="static-cta">
            <div>
              <p className="eyebrow">Mulai dengan satu foto</p>
              <h2>Kenali piringmu dengan lebih jernih.</h2>
            </div>
            <Link href="/register" className="btn-primary">
              Buat akun gratis <span aria-hidden="true">→</span>
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}