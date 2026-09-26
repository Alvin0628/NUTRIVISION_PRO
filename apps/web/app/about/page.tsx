import { StaticPage } from "@/components/StaticPage";

export default function AboutPage() {
  return (
    <StaticPage
      eyebrow="Tentang NutriVision"
      title="Lebih banyak konteks. Lebih sedikit kebisingan."
      intro="NutriVision dibuat untuk orang yang ingin memahami makanan tanpa menjadikan setiap makan sebagai ujian."
      sections={[
        { title: "Teknologi yang melayani perhatianmu", body: "Kami memulai dari foto karena kehidupan sehari-hari jarang datang dengan timbangan dan spreadsheet. Sistem mengenali makanan, memperkirakan porsinya, lalu memberi kamu ruang untuk mengoreksi." },
        { title: "Bukan hakim di meja makan", body: "Tidak ada makanan baik atau buruk di sini. Hanya informasi yang bisa membantu kamu membuat keputusan berikutnya dengan lebih sadar." },
        { title: "Dibuat untuk ritme nyata", body: "NutriVision membantu kamu melihat pola tanpa menuntut kesempurnaan. Satu foto dan satu catatan kecil sudah cukup untuk memulai." },
      ]}
    />
  );
}