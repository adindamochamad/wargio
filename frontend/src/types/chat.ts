/** Tipe respons API chat Wargio */

export interface PermintaanChat {
  pesan: string;
}

export interface ResponsChat {
  balasan: string;
  session_id?: string | null;
  intent?: string | null;
  classification_mode?: string | null;
}

export interface PesanUi {
  id: string;
  peran: "user" | "assistant";
  isi: string;
  intent?: string | null;
  sedangStreaming?: boolean;
}
