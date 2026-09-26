import { StaticPage } from "@/components/StaticPage";

export default function FaqPage() {
  return (
    <StaticPage
      eyebrow="Pertanyaan umum"
      title="Yang ingin kamu tahu sebelum mulai."
      intro="Beberapa jawaban singkat tentang cara NutriVision membaca makanan dan bagaimana kamu tetap memegang kendali."
      sections={[
        { title: "Apakah hasilnya selalu tepat?", body: "Hasil scan adalah estimasi. Karena itu kamu bisa meninjau, mengubah gramasi, dan menghapus deteksi sebelum menyimpan meal." },
        { title: "Apakah saya harus menimbang makanan?", body: "Tidak. NutriVision memberi estimasi awal dari foto, lalu kamu bisa menyesuaikannya bila memiliki informasi porsi yang lebih tepat." },
        { title: "Apa yang terjadi pada foto saya?", body: "Foto dikirim melalui alur API aplikasi untuk dianalisis. Gunakan konfigurasi backend dan kebijakan privasi lingkunganmu sebagai sumber informasi penyimpanan data." },
      ]}
    />
  );
}