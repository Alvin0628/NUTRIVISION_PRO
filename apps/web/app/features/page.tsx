import { StaticPage } from "@/components/StaticPage";

export default function FeaturesPage() {
  return (
    <StaticPage
      eyebrow="Fitur"
      title="Dibuat untuk membantu, bukan menambah pekerjaan."
      intro="Setiap bagian NutriVision dirancang untuk membuat informasi makanan terasa lebih mudah dibaca dan lebih mudah dipakai."
      sections={[
        { title: "Food scan", body: "Mulai dengan foto makanan. Hasil deteksi dikelompokkan dengan rapi agar kamu melihat makanan, bukan daftar objek yang berulang." },
        { title: "Kontrol tetap di tanganmu", body: "Sesuaikan estimasi gramasi, hapus deteksi yang keliru, atau laporkan makanan yang terlewat sebelum menyimpan." },
        { title: "Diary yang personal", body: "Lihat meal yang sudah tercatat, perkembangan makro, dan detail nutrisi dibanding targetmu sendiri." },
      ]}
    />
  );
}