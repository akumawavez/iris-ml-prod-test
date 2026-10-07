#!/usr/bin/env python3
"""CI workflows test and validate. They must not deploy or run Databricks jobs."""

from __future__ import annotations

import sys
from pathlib import Path

BANNED = ("databricks bundle deploy", "databricks bundle run")


def violations(text: str) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in BANNED if phrase in lowered]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    failed = False
    for raw in args[1:]:
        path = Path(raw)
        if not path.is_file():
            continue
        found = violations(path.read_text(encoding="utf-8"))
        if not found:
            continue
        failed = True
        print(f"{raw}: CI must not contain {', '.join(found)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
