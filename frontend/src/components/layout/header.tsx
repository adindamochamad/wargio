"use client";

import { useTema } from "@/components/providers/tema-provider";

export function Header() {
  const { tema, toggleTema } = useTema();

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
              Asisten warung Anda
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={toggleTema}
          className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
          aria-label={tema === "dark" ? "Mode terang" : "Mode gelap"}
        >
          {tema === "dark" ? "☀️ Terang" : "🌙 Gelap"}
        </button>
      </div>
    </header>
  );
}
