# Managed identity and service principal, ELI25

Two kinds of non-human account are now in this Azure subscription.
A **service principal** is an application with a password. A **managed
identity** is an Azure resource account with no password. You still sign
in as yourself on the laptop. The pipeline does not.

The client ids and the access each account has are in
[`infra/identities.json`](../../infra/identities.json). The passwords are
not in git. Re-apply the same access with
[`scripts/grant_identity_access.py`](../../scripts/grant_identity_access.py).

## The three doors

| Who | What it is | Password | Used for |
|---|---|---|---|
| You | Your Entra user | Your login | Laptop `bundle validate`, the workspace UI |
| `sp-iris-develop`, `sp-iris-ppe`, `sp-iris-prod` | Service principal, one per environment | Client secret in Key Vault only | Databricks CLI after the pipeline has read Key Vault |
| `id-iris-ml` | User-assigned managed identity | None | An Azure resource that calls this workspace |
| `dbmanagedidentity` | The managed identity Databricks already created for the workspace | None | Key Vault `get` and `list` only |

Microsoft-hosted Azure DevOps agents do not have a managed identity
of their own. Service connection `sc-iris-keyvault` lets the agent sign
in as `id-iris-ml` without a password. After that login, the pipeline
reads `sp-iris-<env>-client-secret` from Key Vault and uses it as
`ARM_CLIENT_SECRET`. `id-iris-ml` is also ready for a virtual machine
or another Azure resource you attach it to. Do not create that virtual
machine until the cost tracker is approved.

## Which principal deploys which environment

| Git branch | Variable group | Service principal | Schema it may write |
|---|---|---|---|
| `develop` | `iris-develop` | `sp-iris-develop` | `dbw_iris_ml_dev.develop` |
| `ppe` | `iris-ppe` | `sp-iris-ppe` | `dbw_iris_ml_dev.ppe` |
| `main` | `iris-prod` | `sp-iris-prod` | `dbw_iris_ml_dev.prod` |

Each of those three can use the catalog (`USE_CATALOG`) and, on its own
schema, `USE_SCHEMA`, `CREATE_MODEL`, `CREATE_TABLE`, `MODIFY`, `SELECT`,
and `EXECUTE`. On the Azure side each one is **Reader** on the workspace
`dbw-iris-ml-dev`. Reader lets it see the workspace. It does not let it
delete the resource group.

Jobs `iris-ml-train-<env>` and `iris-ml-infer-<env>` run as that
environment's service principal (`run_as` in the job YAML). A Databricks
run does not load `databricks-token` over the top of that identity.

CI validates all three targets as `sp-iris-develop`. Validate does not
deploy. CD still starts only when you run it by hand, type `YES`, and the
branch is `develop`, `ppe`, or `main`. The stage loads only its own
variable group.

The pipeline passes `ARM_CLIENT_ID` and `ARM_CLIENT_SECRET`. Those are
the Entra application id and its password. `DATABRICKS_CLIENT_ID` is a
different login and rejects this password, so the pipeline unsets it.
The check that enforces that is
[eli25-cd-require-service-principal.md](eli25-cd-require-service-principal.md).

## What the managed identity may do

`id-iris-ml` lives in `rg-iris-ml-dev`.

| Access | Why |
|---|---|
| Contributor on workspace `dbw-iris-ml-dev` only | Azure requires this before that identity can call the workspace API |
| Key Vault `kv-iris-ml-dev-7405`, secret `get` and `list` | It can read a secret without a password of its own |
| `USE_CATALOG` plus `USE_SCHEMA`, `SELECT`, and `EXECUTE` on `develop`, `ppe`, and `prod` | It can read. It cannot train or register a model |

`dbmanagedidentity` is in the Databricks-managed resource group. This
repo does not change that group. The grant is only Key Vault `get` and
`list`, so the workspace identity can read secrets.

## Where the secret lives

| Store | Name | In git |
|---|---|---|
| Key Vault `kv-iris-ml-dev-7405` | `sp-iris-develop-client-secret`, and the same pattern for `ppe` and `prod` | The name only |
| Variable group `iris-develop` | `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `DATABRICKS_HOST`, `DATABRICKS_AZURE_RESOURCE_ID` | No |
| `infra/identities.json` | Client ids | Yes. A client id is not a password |

The groups `iris-ppe` and `iris-prod` hold the same public values for
their own principal. The password is not in the group. Rotate a secret
by replacing the Key Vault value. The next pipeline run reads the new
value. Do not commit it, and do not paste it into GitHub.
[token-lifecycle.md](token-lifecycle.md) is the rotation habit for the
personal token.

## What you do not do

- Do not put a client secret in YAML, `.env` committed to git, or this guide.
- Do not give `sp-iris-develop` write access on the `ppe` or `prod` schema.
- Do not use `id-iris-ml` as the Microsoft-hosted pipeline login. Those
  agents cannot present a managed identity.
- Do not dispatch CD from this page. The cost tracker is still the gate.
