"use client";

import { useBahasa } from "@/components/providers/bahasa-provider";

export function AksiCepat({
  onPilih,
  nonaktif,
}: {
  onPilih: (pesan: string) => void;
  nonaktif?: boolean;
}) {
  const { kamus } = useBahasa();

  const daftarAksi = [
    { label: kamus.aksiCekStok, pesan: kamus.pesanCekStok },
    { label: kamus.aksiLihatHutang, pesan: kamus.pesanLihatHutang },
    { label: kamus.aksiLaporan, pesan: kamus.pesanLaporan },
    { label: kamus.aksiRestock, pesan: kamus.pesanRestock },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {daftarAksi.map((aksi) => (
        <button
          key={aksi.label}
          type="button"
          disabled={nonaktif}
          onClick={() => onPilih(aksi.pesan)}
          className="rounded-full border border-[#16a34a]/35 bg-[#16a34a]/12 px-3 py-1.5 text-xs font-medium text-[#15803d] backdrop-blur-sm transition hover:border-[#16a34a]/50 hover:bg-[#16a34a]/22 disabled:opacity-50 dark:border-[#4ade80]/30 dark:bg-[#16a34a]/15 dark:text-[#4ade80] dark:hover:bg-[#16a34a]/25"
        >
          {aksi.label}
        </button>
      ))}
    </div>
  );
}
