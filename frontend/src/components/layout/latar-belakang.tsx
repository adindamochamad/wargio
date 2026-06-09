/**
 * Latar dekoratif — mesh gradient + grid (inspirasi Linear / Vercel / Nexus.ai).
 * Warna mengikuti class .dark di <html>; animasi dimatikan jika prefers-reduced-motion.
 */
export function LatarBelakang() {
  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      aria-hidden
    >
      <div className="wargio-latar-dasar absolute inset-0" />

      <div className="wargio-orb wargio-orb--satu" />
      <div className="wargio-orb wargio-orb--dua" />
      <div className="wargio-orb wargio-orb--tiga" />
      <div className="wargio-orb wargio-orb--empat" />

      <div className="wargio-grid absolute inset-0" />
      <div className="wargio-vignette absolute inset-0" />
    </div>
  );
}
