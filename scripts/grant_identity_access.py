#!/usr/bin/env python3
"""Create the iris service principals and managed identity, then grant access.

Safe to run again. Existing apps, role assignments, and Key Vault secrets
are left in place. A new client secret is created only when that Key Vault
secret is missing. The secret stays in Key Vault. It is not copied into a
variable group and it is not printed.

Microsoft-hosted agents have no managed identity of their own. They sign in
as id-iris-ml through workload identity federation, then read the environment
service principal secret from Key Vault.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from iris_model.identities import (  # noqa: E402
    ADO_ORGANIZATION,
    ADO_PROJECT,
    GITHUB_REPOSITORY,
    KEY_VAULT_NAME,
    KEY_VAULT_SERVICE_CONNECTION,
    MANAGED_IDENTITY_NAME,
    READ_PRIVILEGES,
    RESOURCE_GROUP,
    WORKSPACE_MANAGED_IDENTITY_NAME,
    WORKSPACE_NAME,
    client_secret_name,
    service_principal_name,
    unity_catalog_grants,
)
from iris_model.promotion import PROMOTION  # noqa: E402

IDENTITIES_PATH = ROOT / "infra" / "identities.json"
WORKSPACE_HOST = "https://adb-7405619226406985.5.azuredatabricks.net"
MANAGED_RG = "databricks-rg-dbw-iris-ml-dev-bpjytdnacwiyl"


def _run(args: list[str], *, secret: str = "") -> str:
    """Run a command. Never include a secret in the error text."""
    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "command failed").strip()
        if secret:
            detail = detail.replace(secret, "***")
        raise SystemExit(f"{args[0]} {args[1] if len(args) > 1 else ''} failed: {detail}")
    return completed.stdout.strip()


def _az_json(args: list[str]) -> object:
    return json.loads(_run([*args, "-o", "json"]))


def _account() -> tuple[str, str]:
    shown = _az_json(["az", "account", "show", "--query", "{id:id,tenantId:tenantId}"])
    assert isinstance(shown, dict)
    return str(shown["id"]), str(shown["tenantId"])


def _workspace_resource_id(subscription_id: str) -> str:
    return (
        f"/subscriptions/{subscription_id}/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.Databricks/workspaces/{WORKSPACE_NAME}"
    )


def _ensure_managed_identity() -> dict[str, str]:
    created = _az_json(
        [
            "az",
            "identity",
            "create",
            "-g",
            RESOURCE_GROUP,
            "-n",
            MANAGED_IDENTITY_NAME,
            "--query",
            "{clientId:clientId,principalId:principalId,name:name}",
        ]
    )
    assert isinstance(created, dict)
    print(f"Managed identity {MANAGED_IDENTITY_NAME} client {created['clientId']}")
    return {key: str(created[key]) for key in ("clientId", "principalId", "name")}


def _workspace_mi_principal() -> str:
    shown = _az_json(
        [
            "az",
            "identity",
            "show",
            "-g",
            MANAGED_RG,
            "-n",
            WORKSPACE_MANAGED_IDENTITY_NAME,
            "--query",
            "principalId",
        ]
    )
    return str(shown)


def _ensure_app(display_name: str) -> str:
    listed = _az_json(
        [
            "az",
            "ad",
            "app",
            "list",
            "--filter",
            f"displayName eq '{display_name}'",
            "--query",
            "[].appId",
        ]
    )
    assert isinstance(listed, list)
    if listed:
        app_id = str(listed[0])
        print(f"Service principal {display_name} already exists ({app_id})")
        return app_id
    app_id = _run(
        [
            "az",
            "ad",
            "app",
            "create",
            "--display-name",
            display_name,
            "--query",
            "appId",
            "-o",
            "tsv",
        ]
    )
    print(f"Created app {display_name} ({app_id})")
    return app_id


def _ensure_service_principal(app_id: str) -> str:
    shown = subprocess.run(
        ["az", "ad", "sp", "show", "--id", app_id, "--query", "id", "-o", "tsv"],
        capture_output=True,
        text=True,
        check=False,
    )
    if shown.returncode == 0 and shown.stdout.strip():
        return shown.stdout.strip()
    return _run(["az", "ad", "sp", "create", "--id", app_id, "--query", "id", "-o", "tsv"])


def _key_vault_has(secret_name: str) -> bool:
    shown = subprocess.run(
        [
            "az",
            "keyvault",
            "secret",
            "show",
            "--vault-name",
            KEY_VAULT_NAME,
            "--name",
            secret_name,
            "--query",
            "id",
            "-o",
            "tsv",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return shown.returncode == 0 and bool(shown.stdout.strip())


def _ensure_client_secret(app_id: str, secret_name: str) -> None:
    """Store a client secret in Key Vault. Skip when the secret already exists."""
    if _key_vault_has(secret_name):
        print(f"Key Vault secret {secret_name} already present")
        return
    completed = subprocess.run(
        [
            "az",
            "ad",
            "app",
            "credential",
            "reset",
            "--id",
            app_id,
            "--display-name",
            "iris-cd",
            "--years",
            "1",
            "--query",
            "password",
            "-o",
            "tsv",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    password = completed.stdout.strip()
    if completed.returncode != 0 or not password:
        detail = (completed.stderr or "credential reset failed").replace(password, "***")
        raise SystemExit(detail.strip())
    fd, path = tempfile.mkstemp(prefix="iris-sp-")
    os.close(fd)
    try:
        os.chmod(path, 0o600)
        Path(path).write_text(password)
        set_secret = subprocess.run(
            [
                "az",
                "keyvault",
                "secret",
                "set",
                "--vault-name",
                KEY_VAULT_NAME,
                "--name",
                secret_name,
                "--file",
                path,
                "--query",
                "id",
                "-o",
                "tsv",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if set_secret.returncode != 0:
            detail = (set_secret.stderr or "key vault set failed").replace(password, "***")
            raise SystemExit(detail.strip())
    finally:
        Path(path).unlink(missing_ok=True)
        del password
    print(f"Stored {secret_name} in {KEY_VAULT_NAME}")


def _role(principal_id: str, role: str, scope: str) -> None:
    existing = subprocess.run(
        [
            "az",
            "role",
            "assignment",
            "list",
            "--assignee",
            principal_id,
            "--role",
            role,
            "--scope",
            scope,
            "--query",
            "[0].id",
            "-o",
            "tsv",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if existing.returncode == 0 and existing.stdout.strip():
        print(f"Role {role} already assigned")
        return
    _run(
        [
            "az",
            "role",
            "assignment",
            "create",
            "--assignee-object-id",
            principal_id,
            "--assignee-principal-type",
            "ServicePrincipal",
            "--role",
            role,
            "--scope",
            scope,
            "--query",
            "id",
            "-o",
            "tsv",
        ]
    )
    print(f"Granted {role} on the workspace")


def _key_vault_policy(object_id: str, label: str) -> None:
    _run(
        [
            "az",
            "keyvault",
            "set-policy",
            "--name",
            KEY_VAULT_NAME,
            "--object-id",
            object_id,
            "--secret-permissions",
            "get",
            "list",
            "--query",
            "id",
            "-o",
            "tsv",
        ]
    )
    print(f"Key Vault get/list for {label}")


def _databricks(args: list[str]) -> str:
    return _run(["databricks", *args])


def _workspace_service_principals() -> list[dict[str, object]]:
    raw = _databricks(["service-principals", "list", "-o", "json"])
    parsed = json.loads(raw)
    if isinstance(parsed, list):
        return parsed
    resources = parsed.get("Resources", [])
    assert isinstance(resources, list)
    return resources


def _ensure_workspace_principal(app_id: str, display_name: str) -> None:
    principals = _workspace_service_principals()
    for principal in principals:
        if principal.get("applicationId") == app_id:
            print(f"Workspace already has {display_name}")
            return
    _databricks(
        [
            "service-principals",
            "create",
            "--application-id",
            app_id,
            "--display-name",
            display_name,
            "--active",
            "-o",
            "json",
        ]
    )
    print(f"Added {display_name} to the Databricks workspace")
    _ensure_workspace_access(app_id)


def _ensure_workspace_access(app_id: str) -> None:
    """Workspace API calls fail until the principal has workspace-access."""
    for principal in _workspace_service_principals():
        if principal.get("applicationId") != app_id:
            continue
        entitlements = principal.get("entitlements") or []
        if any(
            isinstance(item, dict) and item.get("value") == "workspace-access"
            for item in entitlements
        ):
            return
        sp_id = str(principal["id"])
        payload = {
            "displayName": principal.get("displayName"),
            "applicationId": app_id,
            "active": True,
            "entitlements": [{"value": "workspace-access"}],
        }
        _databricks(
            [
                "service-principals",
                "update",
                sp_id,
                "--json",
                json.dumps(payload),
                "-o",
                "json",
            ]
        )
        print(f"Granted workspace-access to {principal.get('displayName')}")
        return


def _grant_model_function(principal_app_id: str, full_name: str) -> None:
    """Registered models are functions. Schema CREATE MODEL does not cover a new version."""
    payload = {"changes": [{"principal": principal_app_id, "add": ["ALL_PRIVILEGES", "MANAGE"]}]}
    completed = subprocess.run(
        [
            "databricks",
            "grants",
            "update",
            "function",
            full_name,
            "--json",
            json.dumps(payload),
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if "does not exist" in detail.lower() or "not found" in detail.lower():
            print(f"Model {full_name} is not registered yet")
            return
        raise SystemExit(f"grant function {full_name} failed: {detail}")
    print(f"Granted ALL_PRIVILEGES on function {full_name}")


def _grant(
    principal_app_id: str, securable_type: str, full_name: str, privileges: tuple[str, ...]
) -> None:
    payload = {
        "changes": [
            {
                "principal": principal_app_id,
                "add": list(privileges),
            }
        ]
    }
    completed = subprocess.run(
        [
            "databricks",
            "grants",
            "update",
            securable_type,
            full_name,
            "--json",
            json.dumps(payload),
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "grant failed").strip()
        raise SystemExit(f"grant {securable_type} {full_name} failed: {detail}")
    print(f"Granted {', '.join(privileges)} on {full_name}")


def _group_id(name: str) -> str | None:
    listed = _az_json(
        ["az", "pipelines", "variable-group", "list", "--query", "[].{name:name,id:id}"]
    )
    assert isinstance(listed, list)
    for item in listed:
        if isinstance(item, dict) and item.get("name") == name:
            return str(item["id"])
    return None


def _upsert_variable(group_id: str, name: str, value: str, *, secret: bool) -> None:
    shown = _az_json(
        ["az", "pipelines", "variable-group", "show", "--id", group_id, "--query", "variables"]
    )
    assert isinstance(shown, dict)
    verb = "update" if name in shown else "create"
    args = [
        "az",
        "pipelines",
        "variable-group",
        "variable",
        verb,
        "--group-id",
        group_id,
        "--name",
        name,
        "--value",
        value,
        "--query",
        "name",
        "-o",
        "tsv",
    ]
    if secret:
        args.extend(["--secret", "true"])
    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or "variable update failed").replace(value, "***")
        raise SystemExit(detail.strip())


def _delete_variable(group_id: str, name: str) -> None:
    shown = _az_json(
        ["az", "pipelines", "variable-group", "show", "--id", group_id, "--query", "variables"]
    )
    assert isinstance(shown, dict)
    if name not in shown:
        return
    completed = subprocess.run(
        [
            "az",
            "pipelines",
            "variable-group",
            "variable",
            "delete",
            "--group-id",
            group_id,
            "--name",
            name,
            "--yes",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Could not remove {name} from the variable group")
    print(f"Removed {name}. Key Vault is the source for that value.")


def _ensure_federated_credential(name: str, issuer: str, subject: str) -> None:
    listed = _az_json(
        [
            "az",
            "identity",
            "federated-credential",
            "list",
            "-g",
            RESOURCE_GROUP,
            "-n",
            MANAGED_IDENTITY_NAME,
            "--query",
            "[].name",
        ]
    )
    assert isinstance(listed, list)
    if name in listed:
        print(f"Federated credential {name} already present")
        return
    _run(
        [
            "az",
            "identity",
            "federated-credential",
            "create",
            "--name",
            name,
            "--identity-name",
            MANAGED_IDENTITY_NAME,
            "-g",
            RESOURCE_GROUP,
            "--issuer",
            issuer,
            "--subject",
            subject,
            "--audiences",
            "api://AzureADTokenExchange",
            "--query",
            "name",
            "-o",
            "tsv",
        ]
    )
    print(f"Federated credential {name}")


def _ensure_keyvault_trust() -> None:
    """Let id-iris-ml sign in from Azure DevOps and from the three git branches."""
    listed = _az_json(
        [
            "az",
            "devops",
            "service-endpoint",
            "list",
            "--organization",
            ADO_ORGANIZATION,
            "--project",
            ADO_PROJECT,
            "--query",
            "[].{name:name,id:id}",
        ]
    )
    assert isinstance(listed, list)
    endpoint_id = next(
        (str(item["id"]) for item in listed if item.get("name") == KEY_VAULT_SERVICE_CONNECTION),
        None,
    )
    if endpoint_id is None:
        raise SystemExit(
            f"Service connection {KEY_VAULT_SERVICE_CONNECTION} is missing. "
            "Create the workload-identity connection for id-iris-ml before granting."
        )
    trust = _az_json(
        [
            "az",
            "devops",
            "service-endpoint",
            "show",
            "--id",
            endpoint_id,
            "--organization",
            ADO_ORGANIZATION,
            "--project",
            ADO_PROJECT,
            "--query",
            "{issuer:authorization.parameters.workloadIdentityFederationIssuer,"
            "subject:authorization.parameters.workloadIdentityFederationSubject}",
        ]
    )
    assert isinstance(trust, dict)
    _ensure_federated_credential(
        "ado-sc-iris-keyvault",
        str(trust["issuer"]),
        str(trust["subject"]),
    )
    for stage in PROMOTION:
        _ensure_federated_credential(
            f"github-{stage.git_branch}",
            "https://token.actions.githubusercontent.com",
            f"repo:{GITHUB_REPOSITORY}:ref:refs/heads/{stage.git_branch}",
        )


def _ensure_variable_group(
    name: str,
    *,
    app_id: str,
    tenant_id: str,
    workspace_id: str,
) -> None:
    group_id = _group_id(name)
    public = {
        "DATABRICKS_HOST": WORKSPACE_HOST,
        "ARM_CLIENT_ID": app_id,
        "ARM_TENANT_ID": tenant_id,
        "DATABRICKS_AZURE_RESOURCE_ID": workspace_id,
    }
    if group_id is None:
        variables = [f"{key}={value}" for key, value in public.items()]
        group_id = _run(
            [
                "az",
                "pipelines",
                "variable-group",
                "create",
                "--name",
                name,
                "--authorize",
                "true",
                "--variables",
                *variables,
                "--query",
                "id",
                "-o",
                "tsv",
            ]
        )
        print(f"Created variable group {name}")
    else:
        for key, value in public.items():
            _upsert_variable(group_id, key, value, secret=False)
        print(f"Updated variable group {name}")
    _delete_variable(group_id, "ARM_CLIENT_SECRET")
    current = _az_json(
        ["az", "pipelines", "variable-group", "show", "--id", group_id, "--query", "variables"]
    )
    assert isinstance(current, dict)
    for stale in ("DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET"):
        if stale not in current:
            continue
        subprocess.run(
            [
                "az",
                "pipelines",
                "variable-group",
                "variable",
                "delete",
                "--group-id",
                group_id,
                "--name",
                stale,
                "--yes",
            ],
            capture_output=True,
            text=True,
            check=False,
        )


def main() -> int:
    subscription_id, tenant_id = _account()
    workspace_id = _workspace_resource_id(subscription_id)
    managed = _ensure_managed_identity()
    workspace_mi = _workspace_mi_principal()
    _key_vault_policy(managed["principalId"], MANAGED_IDENTITY_NAME)
    _key_vault_policy(workspace_mi, WORKSPACE_MANAGED_IDENTITY_NAME)
    _role(managed["principalId"], "Contributor", workspace_id)
    _ensure_workspace_principal(managed["clientId"], MANAGED_IDENTITY_NAME)
    _ensure_workspace_access(managed["clientId"])

    applications: dict[str, str] = {}
    for stage in PROMOTION:
        display = service_principal_name(stage.databricks_target)
        app_id = _ensure_app(display)
        principal_id = _ensure_service_principal(app_id)
        applications[stage.databricks_target] = app_id
        secret_name = client_secret_name(stage.databricks_target)
        _ensure_client_secret(app_id, secret_name)
        _role(principal_id, "Reader", workspace_id)
        _ensure_workspace_principal(app_id, display)
        _ensure_workspace_access(app_id)

    app_ids = {
        service_principal_name(stage.databricks_target): applications[stage.databricks_target]
        for stage in PROMOTION
    }
    app_ids[MANAGED_IDENTITY_NAME] = managed["clientId"]
    for grant in unity_catalog_grants():
        _grant(
            app_ids[grant.principal_name], grant.securable_type, grant.full_name, grant.privileges
        )
    for stage in PROMOTION:
        _grant_model_function(applications[stage.databricks_target], stage.model_name)

    for stage in PROMOTION:
        _ensure_variable_group(
            stage.variable_group,
            app_id=applications[stage.databricks_target],
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )
    _ensure_keyvault_trust()

    record = {
        "workspace_host": WORKSPACE_HOST,
        "workspace_resource_id": workspace_id,
        "managed_identity": {
            "name": MANAGED_IDENTITY_NAME,
            "client_id": managed["clientId"],
            "azure_role": "Contributor on the workspace",
            "key_vault": f"get, list on {KEY_VAULT_NAME}",
            "service_connection": KEY_VAULT_SERVICE_CONNECTION,
            "unity_catalog": list(READ_PRIVILEGES),
        },
        "workspace_managed_identity": {
            "name": WORKSPACE_MANAGED_IDENTITY_NAME,
            "key_vault": f"get, list on {KEY_VAULT_NAME}",
        },
        "service_principals": [
            {
                "databricks_target": stage.databricks_target,
                "git_branch": stage.git_branch,
                "name": service_principal_name(stage.databricks_target),
                "client_id": applications[stage.databricks_target],
                "variable_group": stage.variable_group,
                "key_vault_secret": client_secret_name(stage.databricks_target),
                "azure_role": "Reader on the workspace",
                "schema": f"{stage.model_name.rsplit('.', 1)[0]}",
            }
            for stage in PROMOTION
        ],
    }
    IDENTITIES_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {IDENTITIES_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
