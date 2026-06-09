/** Fetch dashboard di server (SSR) — hindari skeleton kosong saat first paint */

import type { ResponsDashboard } from "@/types/dashboard";

function urlDasarApiServer(): string {
  const internal = process.env.API_INTERNAL_URL?.replace(/\/$/, "");
  if (internal) {
    return internal;
  }
  const publik = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (publik) {
    return publik;
  }
  return "http://127.0.0.1:8000";
}

export async function ambilDashboardServer(): Promise<ResponsDashboard | null> {
  try {
    const res = await fetch(`${urlDasarApiServer()}/api/dashboard`, {
      next: { revalidate: 30 },
    });
    if (!res.ok) {
      return null;
    }
    return (await res.json()) as ResponsDashboard;
  } catch {
    return null;
  }
}
