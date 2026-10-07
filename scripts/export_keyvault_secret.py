#!/usr/bin/env python3
"""Read one service-principal secret from Key Vault after Azure login.

The caller must already be authenticated. This script does not log in and
does not print the secret. GitHub Actions receives it through GITHUB_ENV
after a mask command.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from iris_model.identities import (  # noqa: E402
    KEY_VAULT_NAME,
    TENANT_ID,
    client_secret_name,
)


def public_env(target: str) -> dict[str, str]:
    """Host, client id, and tenant. None of these are the client secret."""
    record = json.loads((ROOT / "infra" / "identities.json").read_text(encoding="utf-8"))
    row = next(item for item in record["service_principals"] if item["databricks_target"] == target)
    return {
        "DATABRICKS_HOST": str(record["workspace_host"]),
        "ARM_CLIENT_ID": str(row["client_id"]),
        "DATABRICKS_AZURE_RESOURCE_ID": str(record["workspace_resource_id"]),
        "ARM_TENANT_ID": TENANT_ID,
    }


def show_command(target: str) -> list[str]:
    """Azure CLI command that reads one secret. The value stays in stdout."""
    return [
        "az",
        "keyvault",
        "secret",
        "show",
        "--vault-name",
        KEY_VAULT_NAME,
        "--name",
        client_secret_name(target),
        "--query",
        "value",
        "-o",
        "tsv",
    ]


def fetch_secret(target: str) -> str:
    completed = subprocess.run(show_command(target), capture_output=True, text=True, check=False)
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        detail = (completed.stderr or "key vault read failed").strip()
        raise SystemExit(detail)
    return value


def write_github_env(target: str, *, secret: str, env_path: str) -> None:
    """Append ARM_CLIENT_SECRET. The mask command hides the value in the log."""
    print(f"::add-mask::{secret}", flush=True)
    with open(env_path, "a", encoding="utf-8") as handle:
        for name, value in public_env(target).items():
            handle.write(f"{name}={value}\n")
        handle.write("ARM_CLIENT_SECRET<<IRIS_KV_SECRET\n")
        handle.write(f"{secret}\n")
        handle.write("IRIS_KV_SECRET\n")
    print(f"Fetched {client_secret_name(target)} from {KEY_VAULT_NAME}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=("develop", "ppe", "prod"))
    parser.add_argument(
        "--github-env",
        action="store_true",
        help="Write ARM_CLIENT_SECRET to GITHUB_ENV. Requires an existing az login.",
    )
    args = parser.parse_args(argv)
    if not args.github_env:
        raise SystemExit("Pass --github-env. This script does not print the secret.")
    env_path = os.environ.get("GITHUB_ENV", "").strip()
    if not env_path:
        raise SystemExit("GITHUB_ENV is not set.")
    write_github_env(args.target, secret=fetch_secret(args.target), env_path=env_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
