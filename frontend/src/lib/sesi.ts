/** ID sesi chat — persist di localStorage (MVP tanpa login) */

const KUNCI_SESI = "wargio-session-id";

export function ambilIdSesi(): string {
  if (typeof window === "undefined") {
    return "";
  }
  let id = localStorage.getItem(KUNCI_SESI);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KUNCI_SESI, id);
  }
  return id;
}

export function simpanIdSesi(id: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(KUNCI_SESI, id);
  }
}

export function resetIdSesi(): string {
  const id = crypto.randomUUID();
  simpanIdSesi(id);
  return id;
}
