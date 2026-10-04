#!/usr/bin/env python3
"""Format an agent-edited Python file with ruff. Failures are ignored."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _inside_workspace(path: str, roots: object) -> bool:
    if not isinstance(roots, list) or not roots:
        return True
    absolute = os.path.abspath(path)
    for root in roots:
        if not isinstance(root, str):
            continue
        root_abs = os.path.abspath(root)
        try:
            if os.path.commonpath([absolute, root_abs]) == root_abs:
                return True
        except ValueError:
            continue
    return False


def should_format(path: str, roots: object) -> bool:
    file_path = Path(path)
    if file_path.suffix != ".py" or not file_path.is_file():
        return False
    if not _inside_workspace(path, roots):
        return False
    blocked = {".venv", "venv", "site-packages"}
    return not blocked.intersection(file_path.parts)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return
    file_path = payload.get("file_path")
    roots = payload.get("workspace_roots")
    if not isinstance(file_path, str) or not should_format(file_path, roots):
        return
    for args in (
        ["uv", "run", "ruff", "format", file_path],
        ["uv", "run", "ruff", "check", "--fix", file_path],
    ):
        try:
            subprocess.run(args, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            return


if __name__ == "__main__":
    main()
