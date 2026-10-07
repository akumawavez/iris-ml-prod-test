#!/usr/bin/env python3
"""Turn the manual model selector into an alias, a version, and a model URI.

Champion and env read the alias. A number pins that version. Azure DevOps
output is ##vso variable commands. Nothing secret is printed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from iris_model.release import model_uri, resolve_model_selector  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selector", required=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--format", choices=("text", "ado"), default="text")
    args = parser.parse_args(argv)
    try:
        alias, version = resolve_model_selector(args.selector, args.env)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    uri = model_uri(args.env, alias, version)
    if args.format == "ado":
        print(f"##vso[task.setvariable variable=modelAlias]{alias}")
        print(f"##vso[task.setvariable variable=modelVersion]{version}")
        print(f"##vso[task.setvariable variable=modelUri]{uri}")
    else:
        print(f"alias={alias}")
        print(f"version={version}")
        print(f"uri={uri}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
