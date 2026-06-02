"use client";

export interface AksiCepatItem {
  label: string;
  pesan: string;
}

const DAFTAR_AKSI: AksiCepatItem[] = [
  { label: "Cek Stok", pesan: "stok indomie goreng berapa?" },
  { label: "Lihat Hutang", pesan: "hutang Bu Sari berapa?" },
  { label: "Laporan Hari Ini", pesan: "berapa pendapatan hari ini?" },
  { label: "Restock", pesan: "produk apa yang mau habis?" },
];

export function AksiCepat({
  onPilih,
  nonaktif,
}: {
  onPilih: (pesan: string) => void;
  nonaktif?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {DAFTAR_AKSI.map((aksi) => (
        <button
          key={aksi.label}
          type="button"
          disabled={nonaktif}
          onClick={() => onPilih(aksi.pesan)}
          className="rounded-full border border-[#16a34a]/30 bg-[#16a34a]/10 px-3 py-1.5 text-xs font-medium text-[#15803d] transition hover:bg-[#16a34a]/20 disabled:opacity-50 dark:border-[#16a34a]/40 dark:text-[#4ade80]"
        >
          {aksi.label}
        </button>
      ))}
    </div>
  );
}
