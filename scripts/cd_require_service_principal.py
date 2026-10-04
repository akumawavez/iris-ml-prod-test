#!/usr/bin/env python3
"""Fail CD unless this step has a Databricks service principal.

Deploy and validate must use DATABRICKS_CLIENT_ID and
DATABRICKS_CLIENT_SECRET for the selected environment. A personal access
token is not the deploy identity. This script does not print secret values.
The caller unsets DATABRICKS_TOKEN before the Databricks CLI runs, because
the CLI prefers a token when both are set.
"""

from __future__ import annotations

import os
import sys

REQUIRED = ("DATABRICKS_HOST", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET")


def missing(env: dict[str, str] | None = None) -> list[str]:
    source = os.environ if env is None else env
    return [name for name in REQUIRED if not source.get(name, "").strip()]


def main() -> int:
    gaps = missing()
    if gaps:
        print(
            "CD identity is incomplete. Set " + ", ".join(gaps) + " for this environment.",
            file=sys.stderr,
        )
        return 1
    if os.environ.get("DATABRICKS_TOKEN", "").strip():
        print(
            "DATABRICKS_TOKEN is set. CD must unset it and use the service principal.",
            file=sys.stderr,
        )
        return 1
    print("CD identity: service principal (client id is set, token is unset).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
