import { StaticPage } from "@/components/StaticPage";

export default function HowItWorksPage() {
  return (
    <StaticPage
      eyebrow="Cara kerja"
      title="Tiga langkah menuju piring yang lebih terbaca."
      intro="Alur yang sederhana supaya kamu bisa kembali ke hal yang lebih penting: menikmati makan."
      sections={[
        { title: "Ambil foto", body: "Unggah foto makanan dari sudut yang nyaman. Tidak perlu plating sempurna—foto sehari-hari justru paling berguna." },
        { title: "Tinjau dan sesuaikan", body: "NutriVision menampilkan deteksi makanan dan estimasi gramasi. Kamu tetap memegang kendali untuk mengubah atau menghapusnya." },
        { title: "Simpan polanya", body: "Simpan meal ke diary untuk melihat kalori, makro, dan nutrisi dibanding target personalmu." },
      ]}
    />
  );
}