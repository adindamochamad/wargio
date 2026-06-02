import { pecahTeksBold } from "@/lib/format";

export function TeksBalasan({ teks }: { teks: string }) {
  const baris = teks.split("\n");

  return (
    <div className="space-y-1 text-sm leading-relaxed whitespace-pre-wrap">
      {baris.map((barisTeks, i) => (
        <p key={i}>
          {pecahTeksBold(barisTeks).map((bagian, j) =>
            bagian.tebal ? (
              <strong key={j}>{bagian.isi}</strong>
            ) : (
              <span key={j}>{bagian.isi}</span>
            ),
          )}
        </p>
      ))}
    </div>
  );
}
