import { ambilDashboardServer } from "@/lib/ambil-dashboard-server";
import { HalamanUtamaKlien } from "./halaman-utama-klien";

export const revalidate = 30;

export default async function HalamanUtama() {
  const dashboardAwal = await ambilDashboardServer();
  return <HalamanUtamaKlien dashboardAwal={dashboardAwal} />;
}
