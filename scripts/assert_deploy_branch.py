#!/usr/bin/env python3
"""Refuse a Databricks deploy when the git branch is not the one for that target.

Allowed pairs live in src/iris_model/promotion.py and must match
variables.git_branch in databricks/targets/<target>.yml.
develop deploys develop, ppe deploys ppe, and main deploys prod.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from iris_model.promotion import normalize_branch, stage_for_target  # noqa: E402


class BranchMismatch(Exception):
    """The running git branch may not deploy this Databricks target."""


def check(target: str, branch: str) -> str:
    """Return a pass message, or raise BranchMismatch / KeyError."""
    stage = stage_for_target(target)
    actual = normalize_branch(branch)
    if actual != stage.git_branch:
        seen = actual or "(empty)"
        raise BranchMismatch(
            f"Refusing deploy. Databricks target {target} deploys only from "
            f"git branch {stage.git_branch}. This run is on {seen}."
        )
    return (
        f"Branch check passed: git {stage.git_branch} may deploy "
        f"Databricks target {stage.databricks_target} ({stage.endpoint_name})."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--branch",
        default=(os.environ.get("BUILD_SOURCEBRANCH") or os.environ.get("GITHUB_REF_NAME") or ""),
    )
    args = parser.parse_args(argv)
    try:
        print(check(args.target, args.branch))
    except (BranchMismatch, KeyError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
