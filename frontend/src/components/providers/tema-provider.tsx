"use client";

import { createContext, useCallback, useContext, useState } from "react";

type ModeTema = "light" | "dark";

interface KonteksTema {
  tema: ModeTema;
  toggleTema: () => void;
}

const TemaContext = createContext<KonteksTema | null>(null);

const KUNCI_TEMA = "wargio-tema";

function bacaTemaDariDom(): ModeTema {
  if (typeof document === "undefined") {
    return "light";
  }
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function TemaProvider({ children }: { children: React.ReactNode }) {
  const [tema, setTema] = useState<ModeTema>(() =>
    typeof window !== "undefined" ? bacaTemaDariDom() : "light",
  );

  const toggleTema = useCallback(() => {
    setTema((sebelum) => {
      const berikut = sebelum === "light" ? "dark" : "light";
      localStorage.setItem(KUNCI_TEMA, berikut);
      document.documentElement.classList.toggle("dark", berikut === "dark");
      return berikut;
    });
  }, []);

  return (
    <TemaContext.Provider value={{ tema, toggleTema }}>
      {children}
    </TemaContext.Provider>
  );
}

export function useTema(): KonteksTema {
  const ctx = useContext(TemaContext);
  if (!ctx) {
    throw new Error("useTema harus di dalam TemaProvider");
  }
  return ctx;
}
