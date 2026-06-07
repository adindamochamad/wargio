"""Muat manifest tugas verifikasi agentic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "agent" / "verifikasi" / "manifest_tugas.yaml"


def muat_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest tidak ada: {MANIFEST_PATH}")
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_tugas(tugas_id: str) -> dict[str, Any]:
    """Resolve ID tugas atau sub_tugas — merge dengan parent."""
    data = muat_manifest()
    if tugas_id in data.get("tugas", {}):
        entri = dict(data["tugas"][tugas_id])
        entri["_id"] = tugas_id
        entri["_tipe"] = "tugas"
        return entri

    if tugas_id in data.get("sub_tugas", {}):
        sub = dict(data["sub_tugas"][tugas_id])
        parent_id = sub.get("parent", "")
        parent = data.get("tugas", {}).get(parent_id, {})
        gabung = {**parent, **sub}
        gabung["_id"] = tugas_id
        gabung["_tipe"] = "sub_tugas"
        gabung["_parent"] = parent_id
        return gabung

    tersedia = list(data.get("tugas", {}).keys()) + list(data.get("sub_tugas", {}).keys())
    raise KeyError(f"Tugas '{tugas_id}' tidak ada. Pilihan: {', '.join(sorted(tersedia))}")


def daftar_tugas() -> list[tuple[str, str, int | None]]:
    """Return (id, label, hari) untuk CLI --list."""
    data = muat_manifest()
    hasil: list[tuple[str, str, int | None]] = []
    for tid, entri in sorted(data.get("tugas", {}).items()):
        hasil.append((tid, entri.get("label", tid), entri.get("hari")))
    for sid, entri in sorted(data.get("sub_tugas", {}).items()):
        hasil.append((sid, entri.get("label", sid), None))
    return hasil
