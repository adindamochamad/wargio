/** Format angka ke Rupiah Indonesia */

export function formatRupiah(jumlah: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(jumlah);
}

/** Render teks dengan **bold** markdown sederhana */
export function pecahTeksBold(teks: string): Array<{ tebal: boolean; isi: string }> {
  const bagian: Array<{ tebal: boolean; isi: string }> = [];
  const pola = /\*\*(.+?)\*\*/g;
  let indeksTerakhir = 0;
  let cocok: RegExpExecArray | null;

  while ((cocok = pola.exec(teks)) !== null) {
    if (cocok.index > indeksTerakhir) {
      bagian.push({ tebal: false, isi: teks.slice(indeksTerakhir, cocok.index) });
    }
    bagian.push({ tebal: true, isi: cocok[1] });
    indeksTerakhir = cocok.index + cocok[0].length;
  }

  if (indeksTerakhir < teks.length) {
    bagian.push({ tebal: false, isi: teks.slice(indeksTerakhir) });
  }

  if (bagian.length === 0) {
    bagian.push({ tebal: false, isi: teks });
  }

  return bagian;
}
