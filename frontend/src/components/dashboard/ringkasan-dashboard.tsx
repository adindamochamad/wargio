"use client";

import { useEffect, useState } from "react";
import { ambilDashboard, KesalahanApi } from "@/lib/api";
import { formatRupiah } from "@/lib/format";
import type { ResponsDashboard } from "@/types/dashboard";
import { Skeleton } from "@/components/ui/skeleton";

export function RingkasanDashboard() {
  const [data, setData] = useState<ResponsDashboard | null>(null);
  const [sedangMemuat, setSedangMemuat] = useState(true);
  const [pesanError, setPesanError] = useState<string | null>(null);

  useEffect(() => {
    let dibatalkan = false;

    void ambilDashboard()
      .then((ringkasan) => {
        if (!dibatalkan) {
          setData(ringkasan);
          setPesanError(null);
        }
      })
      .catch((e) => {
        if (!dibatalkan) {
          let pesan =
            e instanceof KesalahanApi
              ? e.message
              : "Tidak bisa memuat dashboard.";
          if (e instanceof KesalahanApi && e.statusKode === 404) {
            pesan +=
              " Restart backend: uvicorn app.main:aplikasi --reload --port 8000";
          }
          setPesanError(pesan);
          setData(null);
        }
      })
      .finally(() => {
        if (!dibatalkan) {
          setSedangMemuat(false);
        }
      });

    return () => {
      dibatalkan = true;
    };
  }, []);

  if (sedangMemuat) {
    return (
      <section className="grid gap-3 sm:grid-cols-3" aria-busy="true">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </section>
    );
  }

  if (pesanError) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100"
      >
        <p>{pesanError}</p>
        <button
          type="button"
          onClick={() => {
            setSedangMemuat(true);
            setPesanError(null);
            void ambilDashboard()
              .then(setData)
              .catch((err) => {
                setPesanError(
                  err instanceof KesalahanApi
                    ? err.message
                    : "Gagal memuat ulang.",
                );
              })
              .finally(() => setSedangMemuat(false));
          }}
          className="mt-2 text-xs font-medium underline"
        >
          Muat ulang
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <section className="grid gap-3 sm:grid-cols-3">
      <Kartu
        judul="Stok kritis"
        nilai={String(data.jumlah_produk_kritis)}
        sub={
          data.stok_kritis.length > 0
            ? data.stok_kritis
                .slice(0, 2)
                .map((p) => `${p.nama} (${p.stok_saat_ini})`)
                .join(", ")
            : "Semua aman"
        }
        warna="merah"
      />
      <Kartu
        judul="Total hutang"
        nilai={formatRupiah(data.total_hutang_aktif)}
        sub={`${data.jumlah_customer_berhutang} pelanggan`}
        warna="kuning"
      />
      <Kartu
        judul="Penjualan hari ini"
        nilai={formatRupiah(data.omzet_hari_ini)}
        sub={`${data.jumlah_transaksi_hari_ini} transaksi`}
        warna="hijau"
      />
    </section>
  );
}

function Kartu({
  judul,
  nilai,
  sub,
  warna,
}: {
  judul: string;
  nilai: string;
  sub: string;
  warna: "hijau" | "kuning" | "merah";
}) {
  const border =
    warna === "hijau"
      ? "border-[#16a34a]/30"
      : warna === "kuning"
        ? "border-amber-300/50"
        : "border-red-300/50";

  return (
    <article
      className={`rounded-xl border bg-white p-4 shadow-sm dark:bg-zinc-900 ${border}`}
    >
      <h2 className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {judul}
      </h2>
      <p className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        {nilai}
      </p>
      <p className="mt-1 line-clamp-2 text-xs text-zinc-600 dark:text-zinc-400">
        {sub}
      </p>
    </article>
  );
}
