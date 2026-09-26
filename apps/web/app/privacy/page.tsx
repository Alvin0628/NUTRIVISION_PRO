import { StaticPage } from "@/components/StaticPage";

export default function PrivacyPage() {
  return (
    <StaticPage
      eyebrow="Privasi"
      title="Informasi yang jelas juga berarti privasi yang jelas."
      intro="Halaman ini menjelaskan prinsip dasar penggunaan data di NutriVision. Sesuaikan detail hukumnya dengan kebijakan organisasi sebelum produksi."
      sections={[
        { title: "Data akun", body: "Alamat email dan identitas akun digunakan untuk autentikasi dan mengaitkan profil serta diary dengan pengguna yang tepat." },
        { title: "Data makanan", body: "Foto dan hasil analisis digunakan untuk menjalankan alur scan, menghitung nutrisi, dan menyimpan meal ketika kamu memilih untuk mencatatnya." },
        { title: "Kontrolmu", body: "Kamu dapat mengatur profil, mengoreksi hasil scan, dan memutuskan kapan sebuah meal disimpan ke diary." },
      ]}
      cta={false}
    />
  );
}