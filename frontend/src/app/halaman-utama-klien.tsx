"use client";

import { useState } from "react";
import { useBahasa } from "@/components/providers/bahasa-provider";
import { ChatWargio } from "@/components/chat/chat-wargio";
import { RingkasanDashboard } from "@/components/dashboard/ringkasan-dashboard";
import { Header } from "@/components/layout/header";
import { LatarBelakang } from "@/components/layout/latar-belakang";
import { StatusApi } from "@/components/layout/status-api";
import type { ResponsDashboard } from "@/types/dashboard";

export function HalamanUtamaKlien({
  dashboardAwal,
}: {
  dashboardAwal: ResponsDashboard | null;
}) {
  const { kamus } = useBahasa();
  const [kunciDashboard, setKunciDashboard] = useState(0);

  return (
    <div className="relative flex min-h-full flex-col">
      <LatarBelakang />
      <StatusApi />
      <Header />
      <main className="relative z-[1] mx-auto w-full max-w-6xl flex-1 space-y-6 px-4 py-6">
        <section aria-labelledby="judul-dashboard">
          <h2
            id="judul-dashboard"
            className="mb-3 text-sm font-semibold uppercase tracking-widest text-zinc-600 dark:text-zinc-400"
          >
            {kamus.ringkasanWarung}
          </h2>
          <RingkasanDashboard
            key={kunciDashboard}
            dataAwal={kunciDashboard === 0 ? dashboardAwal : null}
          />
        </section>

        <section aria-labelledby="judul-chat" className="pb-8">
          <h2
            id="judul-chat"
            className="mb-3 text-sm font-semibold uppercase tracking-widest text-zinc-600 dark:text-zinc-400"
          >
            {kamus.tanyaWargio}
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
