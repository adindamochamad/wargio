import { describe, expect, it } from "vitest";
import { formatRupiah, pecahTeksBold } from "./format";

describe("formatRupiah", () => {
  it("format IDR tanpa desimal", () => {
    expect(formatRupiah(12500)).toContain("12");
    expect(formatRupiah(12500)).toMatch(/Rp|IDR/);
  });
});

describe("pecahTeksBold", () => {
  it("memecah teks **bold**", () => {
    const hasil = pecahTeksBold("Stok **Indomie** aman");
    expect(hasil).toEqual([
      { tebal: false, isi: "Stok " },
      { tebal: true, isi: "Indomie" },
      { tebal: false, isi: " aman" },
    ]);
  });
});
