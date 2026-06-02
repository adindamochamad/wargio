"""Skema respons dashboard mini Hari 4."""

from pydantic import BaseModel


class ProdukStokKritis(BaseModel):
    nama: str
    stok_saat_ini: int
    stok_minimum: int
    satuan: str


class CustomerHutangRingkas(BaseModel):
    nama: str
    total_hutang: int


class ResponsDashboard(BaseModel):
    """Ringkasan untuk kartu dashboard — data dari Atlas live."""

    stok_kritis: list[ProdukStokKritis]
    jumlah_produk_kritis: int
    total_hutang_aktif: int
    jumlah_customer_berhutang: int
    customer_hutang_teratas: list[CustomerHutangRingkas]
    omzet_hari_ini: int
    jumlah_transaksi_hari_ini: int
