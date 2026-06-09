"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { ambilKodeBahasa, simpanKodeBahasa } from "@/lib/bahasa";
import {
  ambilKamus,
  type Kamus,
  type KodeBahasa,
} from "@/lib/i18n/kamus";

interface KonteksBahasa {
  bahasa: KodeBahasa;
  kamus: Kamus;
  setBahasa: (kode: KodeBahasa) => void;
}

const BahasaContext = createContext<KonteksBahasa | null>(null);

export function BahasaProvider({ children }: { children: React.ReactNode }) {
  const [bahasa, setBahasaState] = useState<KodeBahasa>("id");

  useEffect(() => {
    const kode = ambilKodeBahasa();
    setBahasaState(kode);
    document.documentElement.lang = kode === "en" ? "en" : "id";
  }, []);

  const setBahasa = useCallback((kode: KodeBahasa) => {
    simpanKodeBahasa(kode);
    setBahasaState(kode);
  }, []);

  const kamus = useMemo(() => ambilKamus(bahasa), [bahasa]);

  return (
    <BahasaContext.Provider value={{ bahasa, kamus, setBahasa }}>
      {children}
    </BahasaContext.Provider>
  );
}

export function useBahasa(): KonteksBahasa {
  const ctx = useContext(BahasaContext);
  if (!ctx) {
    throw new Error("useBahasa harus di dalam BahasaProvider");
  }
  return ctx;
}
