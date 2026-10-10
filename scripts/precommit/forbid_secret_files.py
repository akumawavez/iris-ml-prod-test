#!/usr/bin/env python3
"""Refuse staged secret files. Names only; file contents are not printed."""

from __future__ import annotations

import sys
from pathlib import Path

BLOCKED_NAMES = {
    ".env",
    "credentials.json",
    "mcp_config.json",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
ALLOWED_NAMES = {".env.example"}


def is_blocked(path: str) -> bool:
    parts = Path(path).parts
    if "backup" in parts:
        return True
    name = Path(path).name
    if name in ALLOWED_NAMES:
        return False
    if name in BLOCKED_NAMES or name in {"keyvault-secrets.json", "pipeline-secrets.json"}:
        return True
    if name == "secrets.json" or name.endswith("-secrets.json"):
        return True
    if name.startswith(".env."):
        return True
    return Path(name).suffix.lower() in BLOCKED_SUFFIXES


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    blocked = [path for path in args[1:] if is_blocked(path)]
    if not blocked:
        return 0
    print("Refusing secret files:", file=sys.stderr)
    for path in blocked:
        print(f"  {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
