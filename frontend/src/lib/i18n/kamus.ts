/** Kamus UI — Bahasa Indonesia & English */

export type KodeBahasa = "id" | "en";

export interface Kamus {
  tagline: string;
  temaTerang: string;
  temaGelap: string;
  labelBahasa: string;
  ringkasanWarung: string;
  tanyaWargio: string;
  chat: string;
  sesiBaru: string;
  placeholderChat: string;
  kirim: string;
  mengirim: string;
  pesanSelamatDatang: string;
  stokKritis: string;
  totalHutang: string;
  penjualanHariIni: string;
  pelanggan: string;
  transaksi: string;
  semuaAman: string;
  memuatRingkasan: string;
  gagalMuatDashboard: string;
  muatUlang: string;
  apiTidakTerjangkau: string;
  gangguanTeknis: string;
  timeoutChat: string;
  aksiCekStok: string;
  aksiLihatHutang: string;
  aksiLaporan: string;
  aksiRestock: string;
  pesanCekStok: string;
  pesanLihatHutang: string;
  pesanLaporan: string;
  pesanRestock: string;
}

export const KAMUS_ID: Kamus = {
  tagline: "Asisten warung Anda",
  temaTerang: "☀️ Terang",
  temaGelap: "🌙 Gelap",
  labelBahasa: "Bahasa",
  ringkasanWarung: "Ringkasan warung",
  tanyaWargio: "Tanya Wargio",
  chat: "Chat",
  sesiBaru: "Sesi baru",
  placeholderChat: "Tanya stok, hutang, atau catat jualan...",
  kirim: "Kirim",
  mengirim: "...",
  pesanSelamatDatang:
    "Halo, Bu/Pak! Saya Wargio — siap bantu cek stok, hutang, dan catat penjualan. " +
    "Tanya apa saja dalam Bahasa Indonesia, atau pakai tombol cepat di bawah.",
  stokKritis: "Stok kritis",
  totalHutang: "Total hutang",
  penjualanHariIni: "Penjualan hari ini",
  pelanggan: "pelanggan",
  transaksi: "transaksi",
  semuaAman: "Semua aman",
  memuatRingkasan: "Memuat ringkasan warung",
  gagalMuatDashboard: "Tidak bisa memuat dashboard.",
  muatUlang: "Muat ulang",
  apiTidakTerjangkau:
    "API tidak terjangkau. Coba muat ulang halaman; jika masih gagal, cek status server.",
  gangguanTeknis: "Ada gangguan teknis. Coba lagi sebentar ya.",
  timeoutChat:
    "Permintaan terlalu lama. Coba lagi sebentar.",
  aksiCekStok: "Cek Stok",
  aksiLihatHutang: "Lihat Hutang",
  aksiLaporan: "Laporan Hari Ini",
  aksiRestock: "Restock",
  pesanCekStok: "stok indomie goreng berapa?",
  pesanLihatHutang: "hutang Bu Sari berapa?",
  pesanLaporan: "berapa pendapatan hari ini?",
  pesanRestock: "produk apa yang mau habis?",
};

export const KAMUS_EN: Kamus = {
  tagline: "Your shop assistant",
  temaTerang: "☀️ Light",
  temaGelap: "🌙 Dark",
  labelBahasa: "Language",
  ringkasanWarung: "Shop summary",
  tanyaWargio: "Ask Wargio",
  chat: "Chat",
  sesiBaru: "New session",
  placeholderChat: "Ask about stock, debt, or record a sale...",
  kirim: "Send",
  mengirim: "...",
  pesanSelamatDatang:
    "Hello! I'm Wargio — I help you check stock, track customer debt, and record sales. " +
    "Ask in natural language or use the quick actions below.",
  stokKritis: "Critical stock",
  totalHutang: "Total debt",
  penjualanHariIni: "Today's sales",
  pelanggan: "customers",
  transaksi: "transactions",
  semuaAman: "All OK",
  memuatRingkasan: "Loading shop summary",
  gagalMuatDashboard: "Could not load dashboard.",
  muatUlang: "Reload",
  apiTidakTerjangkau:
    "API unreachable. Please reload the page or check server status.",
  gangguanTeknis: "Technical issue. Please try again in a moment.",
  timeoutChat: "Request timed out. Please try again.",
  aksiCekStok: "Check Stock",
  aksiLihatHutang: "View Debt",
  aksiLaporan: "Today's Report",
  aksiRestock: "Restock Alert",
  pesanCekStok: "how much indomie goreng stock is left?",
  pesanLihatHutang: "how much debt does Bu Sari have?",
  pesanLaporan: "what is today's revenue?",
  pesanRestock: "which products are running low?",
};

export function ambilKamus(kode: KodeBahasa): Kamus {
  return kode === "en" ? KAMUS_EN : KAMUS_ID;
}
