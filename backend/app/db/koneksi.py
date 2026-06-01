"""Koneksi MongoDB Atlas via PyMongo Async API."""

from typing import Optional

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import ambil_pengaturan

_klien: Optional[AsyncMongoClient] = None


async def dapatkan_database() -> AsyncDatabase:
    """
    Mengembalikan database async. Membuat klien sekali per proses.

    Raises:
        RuntimeError: Jika MONGODB_URI belum dikonfigurasi.
    """
    global _klien
    pengaturan = ambil_pengaturan()
    if not pengaturan.atlas_terkonfigurasi:
        raise RuntimeError(
            "MONGODB_URI belum valid. Salin .env.example ke .env dan isi connection string Atlas."
        )
    if _klien is None:
        _klien = AsyncMongoClient(pengaturan.mongodb_uri)
    return _klien[pengaturan.mongodb_database]


async def tutup_koneksi() -> None:
    """Menutup klien MongoDB saat shutdown aplikasi."""
    global _klien
    if _klien is not None:
        await _klien.close()
        _klien = None


async def cek_koneksi_atlas() -> bool:
    """Ping Atlas; False jika gagal atau belum dikonfigurasi."""
    try:
        db = await dapatkan_database()
        await db.command("ping")
        return True
    except Exception:
        return False
