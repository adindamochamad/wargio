"""Pytest — tambahkan backend ke path dan muat .env."""

import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
load_dotenv(ROOT / ".env")

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
async def reset_klien_mongodb():
    """Reset klien Atlas antar test — hindari error event loop berbeda."""
    from app.db.koneksi import tutup_koneksi

    await tutup_koneksi()
    yield
    await tutup_koneksi()
