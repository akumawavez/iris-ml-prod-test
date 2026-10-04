"""POST an inference check to the iris serving endpoint.

SAFE BY DEFAULT: with no flags the script runs in --dry-run mode — it builds
the exact serving payload, validates it offline, and prints the curl command
it WOULD run. No network, no secrets, no spend.

Live mode (--live) POSTs to $DATABRICKS_HOST/serving-endpoints/<endpoint>/invocations
with $DATABRICKS_TOKEN from the environment only (never from argv, files, or
chat). Each live call keeps a scale-to-zero endpoint warm; see
docs/serving-inference-test.md for the cost note.

Payload shape (Databricks custom-model serving):
    {"dataframe_split": {"columns": [4 feature names], "data": [[row], ...]}}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

FEATURES = (
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
)

SETOSA = {
    "sepal_length_cm": 5.1,
    "sepal_width_cm": 3.5,
    "petal_length_cm": 1.4,
    "petal_width_cm": 0.2,
}
VIRGINICA = {
    "sepal_length_cm": 6.3,
    "sepal_width_cm": 2.9,
    "petal_length_cm": 5.6,
    "petal_width_cm": 1.8,
}
EXPECTED = ("setosa", "virginica")


def build_payload(rows: list[dict]) -> dict:
    """Build the dataframe_split payload the endpoint expects."""
    for row in rows:
        if set(row) != set(FEATURES):
            raise ValueError(f"row keys must be exactly {FEATURES}")
    return {
        "dataframe_split": {
            "columns": list(FEATURES),
            "data": [[row[f] for f in FEATURES] for row in rows],
        }
    }


def dry_run(endpoint: str) -> int:
    """Validate offline and show what a live call would do."""
    payload = build_payload([SETOSA, VIRGINICA])
    print(f"endpoint: {endpoint}")
    print("payload (exact bytes that would be POSTed):")
    print(json.dumps(payload))
    print(f"expected species in order: {list(EXPECTED)}")
    print("dry-run OK: payload valid, no network used, no spend.")
    print("live equivalent:")
    print(
        f'curl -X POST "$DATABRICKS_HOST/serving-endpoints/{endpoint}/invocations" '
        '-H "Authorization: Bearer $DATABRICKS_TOKEN" -H "Content-Type: application/json" '
        f"-d '{json.dumps(payload)}'"
    )
    return 0


def live(endpoint: str) -> int:
    """POST to the live endpoint. Requires env auth; spends warm-DBU time."""
    host = os.environ.get("DATABRICKS_HOST", "").rstrip("/")
    token = os.environ.get("DATABRICKS_TOKEN", "")
    if not host or not token:
        print(
            "live needs DATABRICKS_HOST and DATABRICKS_TOKEN env vars.",
            file=sys.stderr,
        )
        return 2
    payload = build_payload([SETOSA, VIRGINICA])
    req = urllib.request.Request(
        f"{host}/serving-endpoints/{endpoint}/invocations",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode())
    print(json.dumps(body, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="develop-iris-species")
    parser.add_argument("--live", action="store_true", help="POST for real (spends warm time)")
    parser.add_argument("--dry-run", action="store_true", help="offline check (the default)")
    args = parser.parse_args()
    if args.live:
        return live(args.endpoint)
    return dry_run(args.endpoint)


if __name__ == "__main__":
    raise SystemExit(main())
