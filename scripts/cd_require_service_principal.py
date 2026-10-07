#!/usr/bin/env python3
"""Fail unless this step has the Entra service principal for Azure Databricks.

Azure Databricks accepts that principal as ARM_CLIENT_ID, ARM_CLIENT_SECRET,
and ARM_TENANT_ID. DATABRICKS_CLIENT_ID is a different OAuth client and
rejects this Entra secret. A personal access token is not the pipeline
identity. This script does not print secret values. The caller unsets
DATABRICKS_TOKEN before the Databricks CLI runs.
"""

from __future__ import annotations

import os
import sys

REQUIRED = (
    "DATABRICKS_HOST",
    "ARM_CLIENT_ID",
    "ARM_CLIENT_SECRET",
    "ARM_TENANT_ID",
)


def missing(env: dict[str, str] | None = None) -> list[str]:
    source = os.environ if env is None else env
    return [name for name in REQUIRED if not source.get(name, "").strip()]


def main() -> int:
    gaps = missing()
    if gaps:
        print(
            "Pipeline identity is incomplete. Set " + ", ".join(gaps) + " for this environment.",
            file=sys.stderr,
        )
        return 1
    if os.environ.get("DATABRICKS_TOKEN", "").strip():
        print(
            "DATABRICKS_TOKEN is set. Unset it and use the service principal.",
            file=sys.stderr,
        )
        return 1
    if (
        os.environ.get("DATABRICKS_CLIENT_ID", "").strip()
        or os.environ.get("DATABRICKS_CLIENT_SECRET", "").strip()
    ):
        print(
            "Unset DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET. "
            "This Entra app signs in with ARM_CLIENT_ID and ARM_CLIENT_SECRET.",
            file=sys.stderr,
        )
        return 1
    print("Pipeline identity: Entra service principal (ARM client id is set, token is unset).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
