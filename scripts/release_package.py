#!/usr/bin/env python3
"""Build the iris-model wheel from pyproject.toml.

The wheel is the release package. It does not deploy and it does not call
Databricks. ``uv build --wheel`` writes ``dist/``. The version string is the
``version`` field in ``pyproject.toml``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def project_version(pyproject: Path) -> str:
    """Return the ``[project]`` version. Stops at the next table."""
    in_project = False
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            continue
        if in_project and stripped.startswith("version"):
            _, _, raw = stripped.partition("=")
            return raw.strip().strip('"').strip("'")
    raise SystemExit(f"{pyproject} has no [project] version")


def build_wheel(root: Path, *, runner=None) -> Path:
    """Build one wheel and return its path."""
    version = project_version(root / "pyproject.toml")
    if runner is None:
        result = subprocess.run(
            ["uv", "build", "--wheel"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stderr or result.stdout)
            raise SystemExit(result.returncode or 1)
    else:
        runner(root, version)
    matches = sorted((root / "dist").glob(f"*{version}*.whl"))
    if not matches:
        raise SystemExit(f"uv build did not write a wheel for version {version}")
    wheel = matches[-1]
    print(f"release package {wheel.name} version {version}")
    return wheel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    build_wheel(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
