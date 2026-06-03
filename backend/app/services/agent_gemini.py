"""
Integrasi Gemini untuk klasifikasi intent (Agent Builder / Vertex AI).

Fallback ke regex jika kredensial belum dikonfigurasi.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.config import ambil_pengaturan
from app.services.klasifikasi import INTENT_LIST, klasifikasi_intent  # noqa: F401

_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "wargio_system.txt"

INTENT_VALID = {i for i in INTENT_LIST if i != "unknown"}

# Lacak status Gemini runtime — diupdate setiap panggilan
_gemini_status: dict = {"ok": None, "error": None}


def gemini_runtime_ok() -> bool | None:
    """None = belum pernah dipanggil, True = sukses, False = gagal."""
    return _gemini_status["ok"]


@lru_cache
def _muat_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _buat_klien_gemini():
    """Buat klien google-genai jika kredensial tersedia."""
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


async def klasifikasi_dengan_gemini(pesan: str) -> Optional[str]:
    """
    Klasifikasi intent via Gemini. Return None jika gagal → fallback regex.
    """
    klien = _buat_klien_gemini()
    if klien is None:
        return None

    pengaturan = ambil_pengaturan()
    prompt = (
        f"{_muat_system_prompt()}\n\n"
        f"Classify this user message into one intent: {', '.join(sorted(INTENT_VALID))}, or unknown.\n"
        f"User message: {pesan}\n"
        "Reply with ONLY the intent name, nothing else."
    )

    try:
        respons = klien.models.generate_content(
            model=pengaturan.gemini_model,
            contents=prompt,
        )
        teks = (respons.text or "").strip().lower().replace("-", "_")
        # Ambil token intent pertama yang valid
        for intent in INTENT_VALID | {"unknown"}:
            if intent in teks.split():
                result = intent if intent != "unknown" else None
                _gemini_status["ok"] = True
                _gemini_status["error"] = None
                return result
        if teks in INTENT_VALID:
            _gemini_status["ok"] = True
            _gemini_status["error"] = None
            return teks
        return None
    except Exception as e:
        _gemini_status["ok"] = False
        _gemini_status["error"] = type(e).__name__
        return None


async def tentukan_intent(pesan: str) -> tuple[str, str]:
    """
    Tentukan intent + mode klasifikasi (gemini atau regex).
    Write/tier2: regex diutamakan jika berbeda dari Gemini (lebih deterministik).
    """
    intent_regex = klasifikasi_intent(pesan)
    intent_prioritas = {
        "record_sale",
        "record_payment",
        "debt_collection",
        "sales_forecast",
    }

    intent_gemini = await klasifikasi_dengan_gemini(pesan)
    if intent_regex in intent_prioritas:
        return intent_regex, "regex"
    if intent_gemini:
        return intent_gemini, "gemini"

    return intent_regex, "regex"
