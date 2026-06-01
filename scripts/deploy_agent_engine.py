#!/usr/bin/env python3
"""Deploy Wargio ADK agent ke Google Agent Engine."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent" / "wargio"
ENV_FILE = ROOT / ".env"
VENV_ADK = ROOT / "backend" / ".venv" / "bin" / "adk"


def main() -> None:
    if not ENV_FILE.exists():
        print("GAGAL: .env tidak ditemukan di root repo")
        sys.exit(1)
    if not VENV_ADK.exists():
        print("GAGAL: jalankan pip install google-adk di backend/.venv")
        sys.exit(1)

    # Muat project dari .env
    for baris in ENV_FILE.read_text().splitlines():
        if baris.startswith("GOOGLE_CLOUD_PROJECT="):
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", baris.split("=", 1)[1].strip())
        if baris.startswith("GOOGLE_CLOUD_LOCATION="):
            os.environ.setdefault("GOOGLE_CLOUD_LOCATION", baris.split("=", 1)[1].strip())

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "tessera-496904")
    region = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    print(f"Deploy Wargio → Agent Engine ({project} / {region})")
    cmd = [
        str(VENV_ADK),
        "deploy",
        "agent_engine",
        str(AGENT),
        f"--project={project}",
        f"--region={region}",
        "--display_name=wargio",
        "--description=AI agent for Indonesian micro-retailers",
        f"--env_file={ENV_FILE}",
        f"--requirements_file={AGENT / 'requirements.txt'}",
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    print("\nOK: Deploy selesai. Cek Agent Engine di Cloud Console.")


if __name__ == "__main__":
    main()
