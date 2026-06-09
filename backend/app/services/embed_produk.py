"""Embedding teks produk via Gemini — untuk vector search fuzzy match."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from app.config import ambil_pengaturan

DIMENSI_EMBED = 768
MODEL_EMBED_DEFAULT = "gemini-embedding-001"


@lru_cache
def _model_embedding() -> str:
    import os

    return os.getenv("GEMINI_EMBEDDING_MODEL", MODEL_EMBED_DEFAULT).strip() or MODEL_EMBED_DEFAULT


def _buat_klien_gemini():
    """Klien google-genai — sama pola dengan agent_gemini."""
    pengaturan = ambil_pengaturan()
    if not pengaturan.gemini_terkonfigurasi:
        return None

    from google import genai

    if pengaturan.gemini_api_key:
        return genai.Client(api_key=pengaturan.gemini_api_key)

    return genai.Client(
        vertexai=True,
        project=pengaturan.google_cloud_project,
        location=pengaturan.google_cloud_location,
    )


def teks_untuk_embedding_produk(nama: str, alias: list[str] | None = None) -> str:
    """Gabungkan nama + alias jadi satu string untuk embedding."""
    bagian = [nama.strip()]
    if alias:
        bagian.extend(a.strip() for a in alias if a and str(a).strip())
    return " | ".join(dict.fromkeys(bagian))


async def buat_embedding_teks(teks: str) -> Optional[list[float]]:
    """
    Buat vektor 768d dari teks query/nama produk.
    Return None jika Gemini belum dikonfigurasi atau gagal.
    """
    if not teks.strip():
        return None

    klien = _buat_klien_gemini()
    if klien is None:
        return None

    try:
        from google.genai import types

        respons = klien.models.embed_content(
            model=_model_embedding(),
            contents=teks.strip(),
            config=types.EmbedContentConfig(
                output_dimensionality=DIMENSI_EMBED,
            ),
        )
        if not respons.embeddings:
            return None
        nilai = respons.embeddings[0].values
        if not nilai or len(nilai) != DIMENSI_EMBED:
            return None
        return list(nilai)
    except Exception:
        return None
