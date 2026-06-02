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
            ? "bg-[#16a34a] text-white"
            : "border border-zinc-200 bg-white text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
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
        {!dariUser && pesan.intent && (
          <p className="mt-2 text-[10px] uppercase tracking-wide text-zinc-400">
            {pesan.intent}
          </p>
        )}
      </div>
    </div>
  );
}
