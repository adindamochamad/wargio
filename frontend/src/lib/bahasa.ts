/** Kode bahasa persisten — sinkron dengan header API */

import type { KodeBahasa } from "@/lib/i18n/kamus";

const KUNCI_BAHASA = "wargio-bahasa";

export function ambilKodeBahasa(): KodeBahasa {
  if (typeof window === "undefined") {
    return "id";
  }
  const tersimpan = localStorage.getItem(KUNCI_BAHASA);
  return tersimpan === "en" ? "en" : "id";
}

export function simpanKodeBahasa(kode: KodeBahasa): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(KUNCI_BAHASA, kode);
    document.documentElement.lang = kode === "en" ? "en" : "id";
  }
}
