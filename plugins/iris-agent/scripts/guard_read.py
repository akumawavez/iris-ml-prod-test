#!/usr/bin/env python3
"""Keep .env, key, and certificate files out of the agent context."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_io import allow, deny, emit, load_payload  # noqa: E402


def _is_secret_name(name: str) -> bool:
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return True
    return name.endswith(".pem") or name.endswith(".key")


def decide_read(file_path: str) -> dict[str, object]:
    if _is_secret_name(Path(file_path).name):
        return deny(
            f"Reading {Path(file_path).name} is blocked.",
            "Secret files stay out of the agent context. "
            "Read .env.example or docs/secrets.md for variable names.",
        )
    return allow()


def main() -> None:
    payload = load_payload()
    file_path = payload.get("file_path")
    if not isinstance(file_path, str):
        emit(allow())
        return
    emit(decide_read(file_path))


if __name__ == "__main__":
    main()
