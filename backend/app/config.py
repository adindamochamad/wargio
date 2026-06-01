"""Konfigurasi aplikasi dari environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Pengaturan(BaseSettings):
    """Pengaturan runtime — baca dari .env di root repo."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = ""
    mongodb_database: str = "wargio_demo"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    rate_limit_per_minute: int = 30

    # Google Cloud / Gemini (Hari 2+)
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    agent_engine_id: str = ""

    # MCP — live stdio ke mongodb-mcp-server (lambat; default off)
    mcp_live_enabled: bool = False

    @property
    def atlas_terkonfigurasi(self) -> bool:
        """True jika URI Atlas sudah diisi (bukan placeholder)."""
        uri = self.mongodb_uri.strip()
        if not uri:
            return False
        placeholder = ("USER", "PASSWORD", "your_", "changeme")
        return not any(p in uri for p in placeholder)

    @property
    def gemini_terkonfigurasi(self) -> bool:
        """True jika Gemini API key atau Vertex project tersedia."""
        if self.gemini_api_key.strip():
            return True
        return bool(self.google_cloud_project.strip())


@lru_cache
def ambil_pengaturan() -> Pengaturan:
    """Singleton pengaturan agar tidak baca .env berulang."""
    return Pengaturan()
