"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useBahasa } from "@/components/providers/bahasa-provider";
import { kirimChat, KesalahanApi } from "@/lib/api";
import { ambilIdSesi, resetIdSesi, simpanIdSesi } from "@/lib/sesi";
import type { PesanUi } from "@/types/chat";
import { AksiCepat } from "./aksi-cepat";
import { PesanChat } from "./pesan-chat";

export function ChatWargio({
  onTransaksiSelesai,
}: {
  onTransaksiSelesai?: () => void;
}) {
  const { kamus } = useBahasa();
  const [pesanDaftar, setPesanDaftar] = useState<PesanUi[]>([]);
  const [inputTeks, setInputTeks] = useState("");
  const [sedangKirim, setSedangKirim] = useState(false);
  const [pesanError, setPesanError] = useState<string | null>(null);
  const [idSesi, setIdSesi] = useState(() =>
    typeof window !== "undefined" ? ambilIdSesi() : "",
  );
  const bawahRef = useRef<HTMLDivElement>(null);

  // Perbarui sambutan saat bahasa berganti (hanya jika belum ada percakapan user)
  useEffect(() => {
    setPesanDaftar((sebelum) => {
      const hanyaSambutan =
        sebelum.length === 0 ||
        (sebelum.length === 1 && sebelum[0].id === "selamat-datang");
      if (!hanyaSambutan) {
        return sebelum;
      }
      return [
        {
          id: "selamat-datang",
          peran: "assistant",
          isi: kamus.pesanSelamatDatang,
        },
      ];
    });
  }, [kamus.pesanSelamatDatang]);

  useEffect(() => {
    bawahRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [pesanDaftar, sedangKirim]);

  const kirimPesan = useCallback(
    async (teks: string) => {
      const pesanBersih = teks.trim();
      if (!pesanBersih || sedangKirim) {
        return;
      }

      setPesanError(null);
      setSedangKirim(true);

      const idUser = `u-${Date.now()}`;
      const idAsisten = `a-${Date.now()}`;

      setPesanDaftar((sebelum) => [
        ...sebelum,
        { id: idUser, peran: "user", isi: pesanBersih },
        { id: idAsisten, peran: "assistant", isi: "", sedangStreaming: true },
      ]);
      setInputTeks("");

      try {
        const sesi = idSesi || ambilIdSesi();
        const res = await kirimChat(pesanBersih, sesi);
        if (res.session_id) {
          simpanIdSesi(res.session_id);
          setIdSesi(res.session_id);
        }

        setPesanDaftar((sebelum) =>
          sebelum.map((p) =>
            p.id === idAsisten
              ? {
                  ...p,
                  isi: res.balasan,
                  intent: res.intent,
                  sedangStreaming: false,
                }
              : p,
          ),
        );

        const intentWrite =
          res.intent === "record_sale" || res.intent === "record_payment";
        const suksesWrite =
          res.balasan.toLowerCase().includes("berhasil") ||
          res.balasan.toLowerCase().includes("successfully") ||
          res.balasan.toLowerCase().includes("recorded");
        if (intentWrite && suksesWrite) {
          onTransaksiSelesai?.();
        }
      } catch (e) {
        let pesan = kamus.gangguanTeknis;
        if (e instanceof KesalahanApi) {
          pesan = e.message;
        } else if (
          e instanceof DOMException &&
          (e.name === "TimeoutError" || e.name === "AbortError")
        ) {
          pesan = kamus.timeoutChat;
        }
        setPesanError(pesan);
        setPesanDaftar((sebelum) =>
          sebelum.filter((p) => p.id !== idAsisten).concat({
            id: idAsisten,
            peran: "assistant",
            isi: pesan,
          }),
        );
      } finally {
        setSedangKirim(false);
      }
    },
    [idSesi, kamus, onTransaksiSelesai, sedangKirim],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void kirimPesan(inputTeks);
  };

  const handleResetSesi = () => {
    const baru = resetIdSesi();
    setIdSesi(baru);
    setPesanDaftar([
      {
        id: "selamat-datang",
        peran: "assistant",
        isi: kamus.pesanSelamatDatang,
      },
    ]);
    setPesanError(null);
  };

  return (
    <div className="wargio-panel-kaca flex min-h-[420px] flex-col rounded-xl shadow-lg shadow-[#16a34a]/5 dark:shadow-black/25">
      <div className="flex items-center justify-between border-b border-white/30 px-4 py-2 dark:border-white/8">
        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          {kamus.chat}
        </span>
        <button
          type="button"
          onClick={handleResetSesi}
          className="text-xs text-zinc-500 underline hover:text-zinc-800 dark:hover:text-zinc-200"
        >
          {kamus.sesiBaru}
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {pesanDaftar.map((p) => (
          <PesanChat key={p.id} pesan={p} />
        ))}
        <div ref={bawahRef} />
      </div>

      {pesanError && (
        <p
          role="alert"
          className="mx-4 mb-2 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-950 dark:text-red-200"
        >
          {pesanError}
        </p>
      )}

      <div className="border-t border-white/30 p-3 dark:border-white/8">
        <div className="mb-3">
          <AksiCepat
            onPilih={(pesan) => void kirimPesan(pesan)}
            nonaktif={sedangKirim}
          />
        </div>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputTeks}
            onChange={(e) => setInputTeks(e.target.value)}
            placeholder={kamus.placeholderChat}
            disabled={sedangKirim}
            maxLength={2000}
            className="flex-1 rounded-lg border border-white/50 bg-white/60 px-3 py-2.5 text-sm outline-none backdrop-blur-sm focus:border-[#16a34a] focus:ring-1 focus:ring-[#16a34a] disabled:opacity-60 dark:border-white/10 dark:bg-zinc-950/50 dark:text-zinc-100"
            aria-label={kamus.placeholderChat}
          />
          <button
            type="submit"
            disabled={sedangKirim || !inputTeks.trim()}
            className="rounded-lg bg-[#16a34a] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#15803d] disabled:cursor-not-allowed disabled:bg-zinc-400 disabled:text-zinc-100 dark:disabled:bg-zinc-600"
          >
            {sedangKirim ? kamus.mengirim : kamus.kirim}
          </button>
        </form>
      </div>
    </div>
  );
}
