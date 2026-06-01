"""Modul koneksi dan akses database Atlas."""

from app.db.koneksi import dapatkan_database, tutup_koneksi

__all__ = ["dapatkan_database", "tutup_koneksi"]
