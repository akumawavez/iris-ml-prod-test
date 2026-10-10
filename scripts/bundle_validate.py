#!/usr/bin/env python3
"""Validate Databricks bundle targets without deploying or running jobs.

A schema or YAML error fails the process. With ``--allow-missing``, a
deleted workspace, a missing catalog or model, or an unreachable host is
reported and skipped so local tests and CI still pass while those
resources are gone.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

MISSING_MARKERS = (
    "resource_does_not_exist",
    "does not exist",
    "no such host",
    "name or service not known",
    "connection refused",
    "workspace has been deleted",
    "status code: 404",
    "error: 404",
    "not_found",
)
MISSING_NOUNS = ("resource", "catalog", "schema", "model", "endpoint", "workspace", "job")
AUTH_MARKERS = (
    "cannot configure default credentials",
    "default auth:",
    "unauthenticated",
    "invalid_client",
    "invalid authorization",
    "403 forbidden",
)


def resource_unavailable(output: str, *, allow_auth: bool = False) -> bool:
    """True when the CLI output says a host or Unity Catalog object is gone."""
    lowered = output.lower()
    if any(marker in lowered for marker in MISSING_MARKERS):
        return True
    if "not found" in lowered and any(noun in lowered for noun in MISSING_NOUNS):
        return True
    if allow_auth and any(marker in lowered for marker in AUTH_MARKERS):
        return True
    return False


def run_validate(target: str) -> tuple[int, str]:
    """Run ``databricks bundle validate`` for one target."""
    result = subprocess.run(
        ["databricks", "bundle", "validate", "-t", target],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, f"{result.stdout or ''}{result.stderr or ''}"


def validate_targets(
    targets: list[str],
    *,
    allow_missing: bool = False,
    runner=run_validate,
) -> int:
    """Return 0 when every target validates or is an allowed missing resource."""
    if not targets:
        print("no bundle targets", file=sys.stderr)
        return 1
    failed = False
    for target in targets:
        try:
            code, output = runner(target)
        except FileNotFoundError:
            print("databricks CLI is not installed", file=sys.stderr)
            return 1
        if code == 0:
            print(f"databricks bundle validate -t {target} ok")
            continue
        if allow_missing and resource_unavailable(output, allow_auth=True):
            print(
                f"databricks bundle validate -t {target} skipped: "
                "workspace or resource is missing or deleted",
                file=sys.stderr,
            )
            continue
        sys.stderr.write(output)
        if output and not output.endswith("\n"):
            sys.stderr.write("\n")
        print(f"databricks bundle validate -t {target} failed", file=sys.stderr)
        failed = True
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--target", action="append", dest="targets", required=True)
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Skip a target when its workspace or registered resource is gone.",
    )
    args = parser.parse_args(argv)
    return validate_targets(args.targets, allow_missing=args.allow_missing)


if __name__ == "__main__":
    raise SystemExit(main())
