/** Klien HTTP ke FastAPI Wargio */

import type { PermintaanChat, ResponsChat } from "@/types/chat";
import type { ResponsDashboard } from "@/types/dashboard";

const BATAS_WAKTU_MS = 90_000;

function urlDasarApi(): string {
  const dasar = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  return dasar ?? "";
}

export class KesalahanApi extends Error {
  constructor(
    pesan: string,
    public statusKode?: number,
  ) {
    super(pesan);
    this.name = "KesalahanApi";
  }
}

/** Ubah body error FastAPI (detail string atau array) jadi teks UI */
export function ekstrakPesanError(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: string }).msg);
          }
          return String(item);
        })
        .join("; ");
    }
  }
  return `HTTP ${status}`;
}

async function permintaan<T>(
  path: string,
  opsi?: RequestInit,
): Promise<T> {
  const url = `${urlDasarApi()}${path}`;
  const sinyal = AbortSignal.timeout(BATAS_WAKTU_MS);

  const res = await fetch(url, {
    ...opsi,
    signal: sinyal,
    headers: {
      "Content-Type": "application/json",
      ...opsi?.headers,
    },
  });

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      /* abaikan */
    }
    throw new KesalahanApi(ekstrakPesanError(body, res.status), res.status);
  }

  return res.json() as Promise<T>;
}

export async function kirimChat(
  pesan: string,
  idSesi: string,
): Promise<ResponsChat> {
  const body: PermintaanChat = { pesan };
  return permintaan<ResponsChat>("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "X-Session-Id": idSesi },
  });
}

export async function ambilDashboard(): Promise<ResponsDashboard> {
  return permintaan<ResponsDashboard>("/api/dashboard");
}

export async function cekKesehatanApi(): Promise<boolean> {
  try {
    await permintaan<{ status: string }>("/api/health");
    return true;
  } catch {
    return false;
  }
}
