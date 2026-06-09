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
          className="rounded-full border border-[#16a34a]/30 bg-[#16a34a]/10 px-3 py-1.5 text-xs font-medium text-[#15803d] transition hover:bg-[#16a34a]/20 disabled:opacity-50 dark:border-[#16a34a]/40 dark:text-[#4ade80]"
        >
          {aksi.label}
        </button>
      ))}
    </div>
  );
}
