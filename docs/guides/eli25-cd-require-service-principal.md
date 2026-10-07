# The pipeline identity check, ELI25

[`scripts/cd_require_service_principal.py`](../../scripts/cd_require_service_principal.py)
is a bouncer. It stands in front of the Databricks CLI and refuses to
open the door unless this step is signed in as the Entra service
principal for that environment.

It does not log in. It does not create the principal, and it does not
grant access. It only reads the environment variables already in the
shell, then exits. Who those principals are is
[eli25-identities.md](eli25-identities.md).

## When it runs

CI and CD call it in the same shell step as the Databricks command, after
they have cleared the variables that would sign in as somebody else:

```text
unset DATABRICKS_TOKEN
unset DATABRICKS_CLIENT_ID
unset DATABRICKS_CLIENT_SECRET
unset ARM_USE_MSI
python scripts/cd_require_service_principal.py
databricks bundle validate ...
```

`set -euo pipefail` is on, so an exit code of `1` stops the step. The CLI
never starts.

| Pipeline | Step |
|---|---|
| `azure-pipelines.yml` | Validate the three bundle targets. No deploy |
| `azure-pipelines-cd.yml` | Validate, then each deploy, job run, and endpoint check |
| `.github/workflows/cd.yml` | The same checks. That workflow stays disabled (`if: false`) |

Each Azure DevOps step is a new shell. `unset` in an earlier step does
not stick. The unset and this script have to sit in the same step as
`databricks`.

## What it looks for

Four names must be set, and none of them may be blank or only spaces:

| Variable | What it is |
|---|---|
| `DATABRICKS_HOST` | The workspace URL |
| `ARM_CLIENT_ID` | The Entra application id, such as `sp-iris-develop` |
| `ARM_CLIENT_SECRET` | That application's password |
| `ARM_TENANT_ID` | The Entra tenant that issued the application |

Those four are how Azure Databricks accepts an Entra service principal.
The host, tenant, and client id come from variable group `iris-<env>`.
`ARM_CLIENT_SECRET` is read from Key Vault after service connection
`sc-iris-keyvault` signs in. CD sets `envSuffix` from the branch
(`develop`, `ppe`, or `main` → `prod`) and fetches
`sp-iris-<envSuffix>-client-secret`.

If any name is missing, the script prints the missing names to stderr
and exits `1`. It never prints the secret.

## What makes it fail even when those four are set

The Databricks CLI picks the first login it finds. Two other logins
would win, or would fail in a confusing way, so this script rejects them.

| Variable | Why it is refused |
|---|---|
| `DATABRICKS_TOKEN` | A personal access token. The CLI prefers it, so the pipeline would act as a person |
| `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` | A different OAuth client. This repo's Entra password is rejected there with `invalid_client` |

The right pair for this app is `ARM_CLIENT_ID` and `ARM_CLIENT_SECRET`.
The pipeline unsets the other pair before it calls the script. If either
name is still set, the script exits `1` and says to unset them.

`ARM_USE_MSI` is unset in the same step. That flag means "use a managed
identity." Microsoft-hosted agents do not have one. The script itself
does not read `ARM_USE_MSI`. The shell clears it so the CLI cannot try
that login.

## What a pass looks like

When the four names are present and the two refused logins are absent,
it prints one line and exits `0`:

```text
Pipeline identity: Entra service principal (ARM client id is set, token is unset).
```

The client id is not in that line. The secret is not in that line.

## The one function tests call

`missing()` returns the required names that are absent or blank. Tests
pass it a dictionary so they do not need a real tenant or a real secret.
`main()` is what the pipeline runs. It uses the process environment,
checks the two refused logins, and returns `0` or `1`.

## What you do not do

- Do not put the client secret in this script, in YAML, or in this page.
- Do not call Databricks before this script in the same step. The check
  has to fail first.
- Do not treat a green run of this script as a deploy. CI only validates.
  CD is still manual, and it still requires `YES`.
