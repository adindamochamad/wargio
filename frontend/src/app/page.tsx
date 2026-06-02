"use client";

import { useState } from "react";
import { ChatWargio } from "@/components/chat/chat-wargio";
import { RingkasanDashboard } from "@/components/dashboard/ringkasan-dashboard";
import { Header } from "@/components/layout/header";
import { StatusApi } from "@/components/layout/status-api";

export default function HalamanUtama() {
  const [kunciDashboard, setKunciDashboard] = useState(0);

  return (
    <div className="flex min-h-full flex-col bg-zinc-50 dark:bg-zinc-950">
      <StatusApi />
      <Header />
      <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-4 py-6">
        <section aria-labelledby="judul-dashboard">
          <h2
            id="judul-dashboard"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400"
          >
            Ringkasan warung
          </h2>
          <RingkasanDashboard key={kunciDashboard} />
        </section>

        <section aria-labelledby="judul-chat" className="pb-8">
          <h2
            id="judul-chat"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400"
          >
            Tanya Wargio
          </h2>
          <ChatWargio
            onTransaksiSelesai={() =>
              setKunciDashboard((k) => k + 1)
            }
          />
        </section>
      </main>
    </div>
  );
}
