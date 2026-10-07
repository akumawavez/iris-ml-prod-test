#!/usr/bin/env python3
"""Fail unless the queued git commit is the code version the operator named.

HEAD means the commit selected in the Azure DevOps Run pipeline dialog,
or the GitHub workflow ref. A SHA must be a prefix of that commit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from iris_model.release import assert_code_version  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--actual", required=True)
    args = parser.parse_args(argv)
    try:
        commit = assert_code_version(args.expected, args.actual)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Code version {commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
