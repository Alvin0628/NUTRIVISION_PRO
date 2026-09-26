import { StaticPage } from "@/components/StaticPage";

export default function TermsPage() {
  return (
    <StaticPage
      eyebrow="Ketentuan"
      title="Gunakan NutriVision sebagai panduan, bukan diagnosis."
      intro="Ketentuan berikut adalah konten informasi awal untuk aplikasi dan perlu ditinjau secara hukum sebelum digunakan sebagai ketentuan final."
      sections={[
        { title: "Estimasi nutrisi", body: "Hasil deteksi dan nilai nutrisi bersifat estimasi untuk membantu pemahaman sehari-hari, bukan nasihat medis atau diagnosis." },
        { title: "Tanggung jawab pengguna", body: "Tinjau hasil sebelum menyimpan meal dan gunakan pertimbangan sendiri, terutama untuk kebutuhan alergi, kondisi medis, atau diet khusus." },
        { title: "Penggunaan yang wajar", body: "Gunakan aplikasi sesuai tujuan, jangan mencoba mengganggu layanan, dan jangan mengandalkan hasil estimasi sebagai satu-satunya dasar keputusan kesehatan." },
      ]}
      cta={false}
    />
  );
}