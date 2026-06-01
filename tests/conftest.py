"""Pytest — tambahkan backend ke path dan muat .env."""

import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
load_dotenv(ROOT / ".env")

# Test cepat — jangan spawn MCP stdio tiap pytest
import os

os.environ["MCP_LIVE_ENABLED"] = "false"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
async def reset_klien_mongodb():
    """Reset klien Atlas antar test — hindari error event loop berbeda."""
    from app.config import ambil_pengaturan
    from app.db.koneksi import tutup_koneksi

    ambil_pengaturan.cache_clear()
    await tutup_koneksi()
    yield
    await tutup_koneksi()
