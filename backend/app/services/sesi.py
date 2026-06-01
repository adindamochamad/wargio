"""Manajemen sesi chat di collection agent_sessions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase


async def muat_atau_buat_sesi(
    db: AsyncDatabase,
    session_id: str,
) -> dict[str, Any]:
    """Load sesi existing atau buat dokumen baru."""
    sekarang = datetime.now(timezone.utc)
    dokumen = await db.agent_sessions.find_one({"session_id": session_id})
    if dokumen:
        return dokumen

    baru = {
        "session_id": session_id,
        "messages": [],
        "context": {},
        "created_at": sekarang,
        "updated_at": sekarang,
    }
    await db.agent_sessions.insert_one(baru)
    return baru


async def simpan_pesan(
    db: AsyncDatabase,
    session_id: str,
    peran: str,
    isi: str,
    intent: Optional[str] = None,
    aksi: Optional[list[str]] = None,
) -> None:
    """Append pesan ke histori sesi."""
    sekarang = datetime.now(timezone.utc)
    entri = {
        "role": peran,
        "content": isi,
        "timestamp": sekarang,
        "intent": intent,
        "actions_taken": aksi or [],
    }
    await db.agent_sessions.update_one(
        {"session_id": session_id},
        {
            "$push": {"messages": entri},
            "$set": {"updated_at": sekarang},
        },
    )
