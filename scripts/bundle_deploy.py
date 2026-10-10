#!/usr/bin/env python3
"""Deploy one Databricks bundle target from the release wheel.

``databricks bundle deploy`` uploads the wheel built by ``uv build --wheel``.
With ``--allow-missing``, a deleted workspace, a missing catalog, or a
rejected login is reported and skipped. A schema error still fails. This
script does not run jobs.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


def _validate_module():
    path = Path(__file__).resolve().with_name("bundle_validate.py")
    spec = importlib.util.spec_from_file_location("bundle_validate", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_deploy(target: str) -> tuple[int, str]:
    """Run ``databricks bundle deploy`` for one target."""
    result = subprocess.run(
        [
            "databricks",
            "bundle",
            "deploy",
            "-t",
            target,
            "--auto-approve",
            "--force-lock",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, f"{result.stdout or ''}{result.stderr or ''}"


def deploy_target(
    target: str,
    *,
    allow_missing: bool = False,
    runner=run_deploy,
    unavailable=None,
) -> int:
    """Return 0 when deploy succeeds or an allowed missing resource is skipped."""
    if unavailable is None:
        unavailable = _validate_module().resource_unavailable
    try:
        code, output = runner(target)
    except FileNotFoundError:
        print("databricks CLI is not installed", file=sys.stderr)
        return 1
    if code == 0:
        print(f"databricks bundle deploy -t {target} ok")
        return 0
    if allow_missing and unavailable(output, allow_auth=True):
        print(
            f"databricks bundle deploy -t {target} skipped: "
            "workspace or resource is missing or deleted",
            file=sys.stderr,
        )
        return 0
    sys.stderr.write(output)
    if output and not output.endswith("\n"):
        sys.stderr.write("\n")
    print(f"databricks bundle deploy -t {target} failed", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--target", required=True)
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Skip deploy when the workspace or registered resource is gone.",
    )
    args = parser.parse_args(argv)
    return deploy_target(args.target, allow_missing=args.allow_missing)


if __name__ == "__main__":
    raise SystemExit(main())
