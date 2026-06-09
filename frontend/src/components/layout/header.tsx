"use client";

import { useBahasa } from "@/components/providers/bahasa-provider";
import { useTema } from "@/components/providers/tema-provider";
import type { KodeBahasa } from "@/lib/i18n/kamus";

export function Header() {
  const { tema, toggleTema } = useTema();
  const { bahasa, kamus, setBahasa } = useBahasa();

  const pilihBahasa = (kode: KodeBahasa) => {
    if (kode !== bahasa) {
      setBahasa(kode);
    }
  };

  return (
    <header className="sticky top-0 z-10 border-b border-zinc-200 bg-white/90 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          <span
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#16a34a] text-lg font-bold text-white"
            aria-hidden
          >
            W
          </span>
          <div>
            <h1 className="text-lg font-semibold leading-tight text-zinc-900 dark:text-zinc-50">
              Wargio
            </h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              {kamus.tagline}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="flex rounded-lg border border-zinc-200 p-0.5 dark:border-zinc-700"
            role="group"
            aria-label={kamus.labelBahasa}
          >
            <button
              type="button"
              onClick={() => pilihBahasa("id")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                bahasa === "id"
                  ? "bg-[#16a34a] text-white"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
              }`}
              aria-pressed={bahasa === "id"}
            >
              ID
            </button>
            <button
              type="button"
              onClick={() => pilihBahasa("en")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                bahasa === "en"
                  ? "bg-[#16a34a] text-white"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
              }`}
              aria-pressed={bahasa === "en"}
            >
              EN
            </button>
          </div>
          <button
            type="button"
            onClick={toggleTema}
            className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
            aria-label={tema === "dark" ? kamus.temaTerang : kamus.temaGelap}
          >
            {tema === "dark" ? kamus.temaTerang : kamus.temaGelap}
          </button>
        </div>
      </div>
    </header>
  );
}
