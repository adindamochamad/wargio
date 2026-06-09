import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ambilIdSesi, resetIdSesi, simpanIdSesi } from "./sesi";

describe("sesi", () => {
  const penyimpanan: Record<string, string> = {};

  beforeEach(() => {
    vi.stubGlobal("window", {} as Window);
    vi.stubGlobal("localStorage", {
      getItem: (kunci: string) => penyimpanan[kunci] ?? null,
      setItem: (kunci: string, nilai: string) => {
        penyimpanan[kunci] = nilai;
      },
      removeItem: (kunci: string) => {
        delete penyimpanan[kunci];
      },
    });
    vi.stubGlobal("crypto", {
      randomUUID: () => "uuid-baru-1234",
    });
    delete penyimpanan["wargio-session-id"];
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("membuat id baru jika belum ada di localStorage", () => {
    const id = ambilIdSesi();
    expect(id).toBe("uuid-baru-1234");
    expect(penyimpanan["wargio-session-id"]).toBe("uuid-baru-1234");
  });

  it("mengembalikan id yang sudah tersimpan", () => {
    penyimpanan["wargio-session-id"] = "sesi-lama";
    expect(ambilIdSesi()).toBe("sesi-lama");
  });

  it("simpanIdSesi menulis ke localStorage", () => {
    simpanIdSesi("id-custom");
    expect(penyimpanan["wargio-session-id"]).toBe("id-custom");
  });

  it("resetIdSesi menghasilkan uuid baru", () => {
    penyimpanan["wargio-session-id"] = "lama";
    const id = resetIdSesi();
    expect(id).toBe("uuid-baru-1234");
    expect(penyimpanan["wargio-session-id"]).toBe("uuid-baru-1234");
  });
});
