#!/usr/bin/env python3
"""Refuse committed token and private-key literals. Does not print the match."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = (
    ("Databricks PAT", re.compile(r"dapi[0-9a-fA-F]{32}")),
    ("GitHub classic PAT", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("GitHub fine-grained PAT", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
)
MAX_BYTES = 1_000_000


def findings(path: str, text: str) -> list[str]:
    return [label for label, pattern in PATTERNS if pattern.search(text)]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    failed = False
    for raw in args[1:]:
        path = Path(raw)
        if not path.is_file():
            continue
        if path.stat().st_size > MAX_BYTES:
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        labels = findings(raw, data.decode("utf-8", errors="ignore"))
        if not labels:
            continue
        failed = True
        print(f"{raw}: refused {', '.join(labels)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
