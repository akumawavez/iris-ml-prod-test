"""Who may call Azure and Databricks for each environment.

A person uses a laptop login. The pipeline uses a service principal, one
per environment. Azure resources use a managed identity, which has no
password. Client secrets are not in this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from iris_model.promotion import PROMOTION

CATALOG = "dbw_iris_ml_dev"
RESOURCE_GROUP = "rg-iris-ml-dev"
WORKSPACE_NAME = "dbw-iris-ml-dev"
KEY_VAULT_NAME = "kv-iris-ml-dev-7405"
KEY_VAULT_SERVICE_CONNECTION = "sc-iris-keyvault"
ADO_ORGANIZATION = "https://dev.azure.com/akumawavez"
ADO_PROJECT = "iris-ml-prod-test"
GITHUB_REPOSITORY = "akumawavez/iris-ml-prod-test"
TENANT_ID = "85f70bb6-88ac-4f15-9b5a-b6510e3141c4"
SUBSCRIPTION_ID = "1d8cc420-e891-4710-b1fa-03206d4fde2a"
MANAGED_IDENTITY_NAME = "id-iris-ml"
WORKSPACE_MANAGED_IDENTITY_NAME = "dbmanagedidentity"

# The training identity may write this environment's schema.
SCHEMA_PRIVILEGES: tuple[str, ...] = (
    "USE_SCHEMA",
    "CREATE_MODEL",
    "CREATE_TABLE",
    "MODIFY",
    "SELECT",
    "EXECUTE",
)
# The managed identity may read. It does not train or deploy.
READ_PRIVILEGES: tuple[str, ...] = ("USE_SCHEMA", "SELECT", "EXECUTE")


@dataclass(frozen=True, slots=True)
class PrincipalGrant:
    """One Unity Catalog grant for a named principal."""

    principal_name: str
    securable_type: str
    full_name: str
    privileges: tuple[str, ...]


def service_principal_name(databricks_target: str) -> str:
    """Entra app display name for one Databricks environment."""
    return f"sp-iris-{databricks_target}"


def client_secret_name(databricks_target: str) -> str:
    """Key Vault secret name. The value is never committed."""
    return f"sp-iris-{databricks_target}-client-secret"


def unity_catalog_grants() -> tuple[PrincipalGrant, ...]:
    """Grants applied to the three service principals and the managed identity."""
    grants: list[PrincipalGrant] = []
    for stage in PROMOTION:
        name = service_principal_name(stage.databricks_target)
        grants.append(
            PrincipalGrant(name, "catalog", CATALOG, ("USE_CATALOG",)),
        )
        grants.append(
            PrincipalGrant(
                name,
                "schema",
                f"{CATALOG}.{stage.databricks_target}",
                SCHEMA_PRIVILEGES,
            )
        )
    for stage in PROMOTION:
        grants.append(
            PrincipalGrant(
                MANAGED_IDENTITY_NAME,
                "schema",
                f"{CATALOG}.{stage.databricks_target}",
                READ_PRIVILEGES,
            )
        )
    grants.append(
        PrincipalGrant(MANAGED_IDENTITY_NAME, "catalog", CATALOG, ("USE_CATALOG",)),
    )
    return tuple(grants)
