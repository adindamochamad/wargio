import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  KesalahanApi,
  ambilDashboard,
  cekKesehatanApi,
  ekstrakPesanError,
  kirimChat,
} from "./api";

function mockFetch(respons: Partial<Response> & { json?: () => unknown }) {
  return vi.fn().mockResolvedValue({
    ok: respons.ok ?? true,
    status: respons.status ?? 200,
    json: async () => respons.json?.() ?? {},
    ...respons,
  });
}

describe("ekstrakPesanError", () => {
  it("membaca detail string", () => {
    expect(ekstrakPesanError({ detail: "Not found" }, 404)).toBe("Not found");
  });

  it("membaca detail array validasi FastAPI", () => {
    const body = {
      detail: [
        {
          type: "string_too_short",
          loc: ["body", "pesan"],
          msg: "String should have at least 1 character",
          input: "",
        },
      ],
    };
    expect(ekstrakPesanError(body, 422)).toContain("at least 1 character");
  });

  it("fallback HTTP status", () => {
    expect(ekstrakPesanError(null, 500)).toBe("HTTP 500");
  });
});

describe("permintaan API", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch({ ok: true, json: () => ({ status: "ok" }) }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("kirimChat POST dengan header sesi", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        ok: true,
        json: () => ({ balasan: "Halo", intent: "unknown" }),
      }),
    );
    const hasil = await kirimChat("stok indomie", "sesi-abc");
    expect(hasil.balasan).toBe("Halo");
    const panggilan = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(panggilan[0]).toContain("/api/chat");
    expect(panggilan[1]?.method).toBe("POST");
    expect(panggilan[1]?.headers?.["X-Session-Id"]).toBe("sesi-abc");
  });

  it("ambilDashboard GET", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        ok: true,
        json: () => ({ pendapatan_hari_ini: 1000 }),
      }),
    );
    const dash = await ambilDashboard();
    expect(dash.pendapatan_hari_ini).toBe(1000);
  });

  it("melempar KesalahanApi saat HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        ok: false,
        status: 429,
        json: () => ({ detail: "Terlalu banyak permintaan" }),
      }),
    );
    await expect(kirimChat("halo", "s1")).rejects.toBeInstanceOf(KesalahanApi);
  });

  it("cekKesehatanApi true saat sukses", async () => {
    expect(await cekKesehatanApi()).toBe(true);
  });

  it("cekKesehatanApi false saat gagal", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({ ok: false, status: 503, json: () => ({}) }),
    );
    expect(await cekKesehatanApi()).toBe(false);
  });
});
