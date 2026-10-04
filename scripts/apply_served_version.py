#!/usr/bin/env python3
"""Point a serving endpoint at the Unity Catalog alias version.

Gated CD calls this after the train job. A missing endpoint is created.
An existing endpoint is updated when the alias moved. The call does not
wait for the container, and it does not print tokens.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def alias_version(model: dict, alias: str) -> str:
    """Return the version number the alias points at."""
    for item in model.get("aliases") or []:
        if item.get("alias_name") != alias:
            continue
        version = str(item.get("version_num") or "")
        if version:
            return version
    raise SystemExit(f"alias {alias} has no version on {model.get('name', 'model')}")


def served_entity_version(endpoint: dict) -> str:
    """Return the entity_version of the first served entity, or empty."""
    entities = (endpoint.get("config") or {}).get("served_entities") or []
    if not entities:
        return ""
    return str(entities[0].get("entity_version") or "")


def endpoint_config(model: str, version: str) -> dict:
    """CPU Small, scale-to-zero, one entity. No inference-table capture."""
    return {
        "served_entities": [
            {
                "name": "iris_species",
                "entity_name": model,
                "entity_version": version,
                "workload_type": "CPU",
                "workload_size": "Small",
                "scale_to_zero_enabled": True,
            }
        ]
    }


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True)


def _databricks_json(args: list[str]) -> dict:
    result = _run(["databricks", *args, "-o", "json"])
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode or 1)
    return json.loads(result.stdout or "{}")


def apply(endpoint: str, model: str, alias: str) -> str:
    """Create or update the endpoint. Returns created, updated, or current."""
    version = alias_version(
        _databricks_json(["registered-models", "get", model, "--include-aliases"]),
        alias,
    )
    config = endpoint_config(model, version)
    current_proc = _run(["databricks", "serving-endpoints", "get", endpoint, "-o", "json"])
    if current_proc.returncode != 0:
        body = json.dumps({"name": endpoint, "config": config})
        created = _run(["databricks", "serving-endpoints", "create", "--no-wait", "--json", body])
        if created.returncode != 0:
            sys.stderr.write(created.stderr or created.stdout)
            raise SystemExit(created.returncode or 1)
        print(f"created {endpoint} at version {version}")
        return "created"
    current = served_entity_version(json.loads(current_proc.stdout or "{}"))
    if current == version:
        print(f"{endpoint} already serves version {version}")
        return "current"
    updated = _run(
        [
            "databricks",
            "serving-endpoints",
            "update-config",
            endpoint,
            "--no-wait",
            "--json",
            json.dumps(config),
        ]
    )
    if updated.returncode != 0:
        sys.stderr.write(updated.stderr or updated.stdout)
        raise SystemExit(updated.returncode or 1)
    print(f"updated {endpoint} from version {current or 'none'} to {version}")
    return "updated"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--alias", required=True)
    args = parser.parse_args(argv)
    apply(args.endpoint, args.model, args.alias)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
