/** Tipe respons GET /api/dashboard */

export interface ProdukStokKritis {
  nama: string;
  stok_saat_ini: number;
  stok_minimum: number;
  satuan: string;
}

export interface CustomerHutangRingkas {
  nama: string;
  total_hutang: number;
}

export interface ResponsDashboard {
  stok_kritis: ProdukStokKritis[];
  jumlah_produk_kritis: number;
  total_hutang_aktif: number;
  jumlah_customer_berhutang: number;
  customer_hutang_teratas: CustomerHutangRingkas[];
  omzet_hari_ini: number;
  jumlah_transaksi_hari_ini: number;
}
