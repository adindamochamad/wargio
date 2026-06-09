import type { PesanUi } from "@/types/chat";
import { TeksBalasan } from "./teks-balasan";

export function PesanChat({ pesan }: { pesan: PesanUi }) {
  const dariUser = pesan.peran === "user";

  return (
    <div
      className={`flex ${dariUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 sm:max-w-[75%] ${
          dariUser
            ? "bg-gradient-to-br from-[#22c55e] to-[#15803d] text-white shadow-md shadow-[#16a34a]/25"
            : "border border-white/50 bg-white/75 text-zinc-900 backdrop-blur-sm dark:border-white/10 dark:bg-zinc-900/65 dark:text-zinc-100"
        }`}
      >
        {pesan.sedangStreaming ? (
          <div className="flex gap-1 py-1" aria-label="Mengetik">
            <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 [animation-delay:0ms]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 [animation-delay:150ms]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 [animation-delay:300ms]" />
          </div>
        ) : dariUser ? (
          <p className="text-sm">{pesan.isi}</p>
        ) : (
          <TeksBalasan teks={pesan.isi} />
        )}
        {!dariUser && pesan.intent && process.env.NODE_ENV === "development" && (
          <p
            className="mt-2 text-[10px] uppercase tracking-wide text-zinc-400"
            aria-hidden
          >
            {pesan.intent}
          </p>
        )}
      </div>
    </div>
  );
}
