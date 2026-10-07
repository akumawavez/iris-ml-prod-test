# Where to put variables and secrets

One decision tree for this repo: pick the store by *who needs the value*,
*whether it is secret*, and *whether it changes per run*. Names and scopes
are committed. Values are never committed.

Companion files:

- Secret *names* and the live Key Vault scope: [secrets.md](../secrets.md)
- Create / rotate / revoke tokens (CLI → MCP → UI): [token-lifecycle.md](token-lifecycle.md)
- Azure DevOps variable groups: [azure-devops.md](azure-devops.md)
- Bundle variables and targets: [databricks-asset-bundles.md](databricks-asset-bundles.md)
- Branch → Databricks env map: [branch-rules.md](../branch-rules.md)

## Quick chooser

| Ask this | If yes → put it here |
|---|---|
| Is it a password, token, PAT, private key, or connection string? | **Azure Key Vault** (Databricks secret scope) and/or **GitHub Actions secret** / **Azure DevOps secret variable**. Never git. |
| Does CI/CD need it to talk to Databricks? | **GitHub Actions secret** (and the Azure DevOps `iris-develop` variable group). Same logical value as Key Vault's `databricks-token`. |
| Is it a non-secret name that differs by environment (`develop` / `ppe` / `prod`)? | **Databricks Asset Bundle variable** in `databricks.yml` + `databricks/targets/<env>.yml`. |
| Does one job run need a different experiment name, model URI, or flag? | **Job parameter** (CLI args / widgets on the task). |
| Does every process on a cluster need the same non-secret setting? | **Compute / job environment variable** (Spark env or serverless environment). Rare in this repo — we prefer job parameters. |
| Is it only for your laptop (`uv run`, git push)? | **Local `.env`** (gitignored). Names only in `.env.example`. |
| Is it a workflow toggle ("type YES", pick target)? | **GitHub Actions `workflow_dispatch` input** (parameter), not a secret. |
| Is it a pinned tool version used by every workflow run? | **GitHub Actions `env:`** at workflow level (non-secret). |

If two rows both fit, prefer the higher row for secrets, and prefer
**bundle variables** over **compute env vars** for non-secrets that are
environment-shaped.

## Store-by-store guide

### 1. Azure Key Vault (+ Databricks secret scope)

**Where in this project**

- Key Vault / secret scope name: `kv-iris-ml-dev-7405`
- Read at runtime: `dbutils.secrets.get(scope="kv-iris-ml-dev-7405", key="...")`
- Notebooks and scripts fall back to `os.getenv(...)` so local `uv run` works
  without Databricks ([`notebooks/train_register.py`](../../notebooks/train_register.py)).

**When to use**

- Workspace jobs, notebooks, or serving-adjacent code must read a credential
  *inside Databricks*.
- The same secret must be rotatable without editing YAML or opening a PR.
- More than one job in the workspace should share one credential.

**What to store**

| Kind | Example key name | Notes |
|---|---|---|
| Workspace / SP token | `databricks-token` | Used today via `_get_secret(...)` |
| External API keys | `openai-api-key`, `snowflake-password` | Only if a job calls that service |
| Storage / JDBC strings | `blob-connection-string` | Prefer UC + SP auth when you can |

**What not to store**

- Environment names, endpoint names, model aliases → bundle variables
- Per-run flags (`--register`, experiment name) → job parameters
- GitHub PAT for laptop git stays in local `.env` for the credential helper, and a copy is also in Key Vault as `github-token` ([secrets.md](../secrets.md))

**Rules**

- Commit the *scope name* and *key name*. Never the value.
- Do not print secrets. Do not put them in MLflow params, tags, or logs.
- Prefer one Key Vault-backed scope per workspace. Split keys by purpose,
  not by inventing a second store for the same token.

### 2. Databricks environment / bundle variables

**Where in this project**

- Defaults: [`databricks.yml`](../../databricks.yml) under `variables:`
- Per-env overrides: [`databricks/targets/develop.yml`](../../databricks/targets/develop.yml),
  `ppe.yml`, `prod.yml`
- Consumed as `${var.env_suffix}` on the end of job, endpoint, and model names

**When to use**

- Non-secret values that change by promotion stage (`develop` → `ppe` → `prod`).
- Names that must stay identical across jobs, endpoints, and docs.
- Anything CD should bake in at `bundle deploy` / `bundle run` time.

**What to store (this repo today)**

| Variable | Purpose |
|---|---|
| `env` | Logical env name (`develop` / `ppe` / `prod`). Same value as `env_suffix` |
| `git_branch` | Git branch allowed to deploy that target |
| `env_suffix` | Appended to jobs, endpoints, experiments, schema, and alias (`iris-species-develop`) |
| `owner` | Cost/ownership tag only |
| `personal_compute_id` | Optional; pass with `--var` at deploy if needed |
| `model_version` | Fallback note in the endpoint shape file. CD serves the alias version instead. |

**What not to store**

- Tokens or connection strings
- One-off values for a single manual run (use job parameters or `--var`)

**Rules**

- Override per target under `databricks/targets/`, not by editing job YAML
  for each environment.
- CD deploys target `develop` only from branch `develop`, `ppe` from `ppe`,
  and `prod` from `main`.

### 3. Compute variables (cluster / Spark / serverless env)

**Where this would live**

- Classic jobs cluster: `spark_env_vars` / `spark_conf` on the cluster spec
- Serverless job environment: task `environment_key` + dependency spec
  (this repo already uses that for `requirements-serving.txt` pins)
- All-purpose cluster UI → Environment variables (avoid for production;
  this project does not deploy all-purpose clusters)

**When to use**

- A library must see an env var (`MLFLOW_TRACKING_URI=databricks`) for every
  task on that compute, and you cannot pass it as a CLI arg.
- Spark config that is truly cluster-wide (`spark.sql.shuffle.partitions`).

**What to store**

| Kind | Example | Secret? |
|---|---|---|
| Framework mode | `MLFLOW_TRACKING_URI=databricks` | No |
| Non-secret feature flags | `LLM_EXPLANATION_STYLE=concise` | No |
| Spark tuning | `spark.databricks...` | No |

**What not to store**

- Secrets. Put secrets in Key Vault and read with `dbutils.secrets`, or
  inject from CI into the *pipeline* process, not into a long-lived cluster
  definition in git.
- Env-specific resource names. Those belong in bundle variables so `ppe`
  and `prod` cannot silently share `iris-species-develop`.

**How this repo prefers to work**

Serverless tasks take **job parameters** for experiment / model / alias /
env. The compute library is the uv wheel (`uv build --wheel`), pushed by
bundle deploy. There is no all-purpose cluster in the
bundle on purpose ([productionalisation rules](../productionalisation/rules.md)).

### 4. Job parameters

**Where in this project**

- Task `spark_python_task.parameters` in
  [`databricks/jobs/iris_ml_job_pipeline.yml`](../../databricks/jobs/iris_ml_job_pipeline.yml)
  and [`databricks/tasks/*.yml`](../../databricks/tasks/)
- Script argparse: `--experiment`, `--registered-name`, `--alias`, `--env`, …
- Notebook widgets via `_get_param` (widget → env → default)

**When to use**

- Values that describe *this run*: which experiment, which model, whether
  to register, which alias to set.
- Anything an operator might override on a single `bundle run` without
  redeploying the whole env.
- Non-secret inputs you want visible in the Jobs UI run details.

**What to store**

| Kind | Example |
|---|---|
| Paths / names | `--experiment iris-species-develop` |
| Model identity | `--registered-name dbw_iris_ml_dev.develop.iris_species` |
| Behaviour flags | `--register`, `--tracking-uri databricks` |
| Style / mode | `--env develop`, explanation style widgets |

**What not to store**

- Tokens (they show up in run configuration and logs)
- Host-wide defaults that never change per run → bundle variables

**Rules**

- Wire parameters from `${var.*}` in YAML so each target stays consistent.
- Keep defaults safe: registering or deploying should require an explicit flag
  or CD step, not an accidental default.

### 5. GitHub Actions: secrets, `env`, and parameters

GitHub has three different knobs. Use the right one.

#### 5a. Repository / environment **secrets**

**Where**

- Repo → **Settings** → **Secrets and variables** → **Actions**
- Or on a GitHub **Environment** (`develop`, `ppe`, `prod`) for approval-gated CD
- Referenced as `${{ secrets.DATABRICKS_HOST }}` in
  [`.github/workflows/cd.yml`](../../.github/workflows/cd.yml)

**When to use**

- The GitHub-hosted runner must authenticate to Databricks (or Azure).
- Values must never appear in logs, PRs, or workflow files.

**What to store**

| Secret name | Purpose |
|---|---|
| `DATABRICKS_HOST` | Workspace URL for CLI `bundle validate` / `deploy` / `run` |
| `DATABRICKS_TOKEN` | PAT or service-principal token for that host |

**What not to store**

- Non-secret config (`DATABRICKS_CLI_VERSION`, target names) → workflow `env`
  or `inputs`
- Laptop-only `GITHUB_TOKEN` for git push → local `.env`, not Actions secrets
  (Actions already provides `github.token` for its own API calls)

#### 5b. Repository / environment **variables** (non-secret)

**When to use**

- Non-secret values shared across workflows that you want to edit in the
  GitHub UI without a PR (for example a notification channel name).
- Prefer committing the value in workflow `env:` when the team reviews it
  like code — that is what this repo does for `DATABRICKS_CLI_VERSION`.

#### 5c. Workflow `env:` (committed)

**When to use**

- Pinned tool versions and constant non-secrets every job needs.
- Example in CD: `DATABRICKS_CLI_VERSION: "0.272.1"`.

#### 5d. Workflow **parameters** (`workflow_dispatch` inputs / `workflow_call` inputs)

**When to use**

- A human or a calling workflow must choose something *per run*.
- Examples in CD: `confirm` (type `YES`), `target` (`develop` / `ppe` / `prod`).

**What to store**

| Input | Purpose |
|---|---|
| `confirm` | Explicit budget gate |
| `target` | Which Databricks bundle target to deploy |

**What not to store**

- Secrets. Inputs are visible on the run summary.
- Long-lived credentials. Those are Actions secrets.

### 6. Azure DevOps variable group (same secrets, other CI host)

**Where**

- Variable group `iris-develop` (names only in YAML; see
  [azure-pipelines.yml](../../azure-pipelines.yml) and [secrets.md](../secrets.md))
- Mapped into the job as `DATABRICKS_HOST` / `DATABRICKS_TOKEN`

Treat this as the Azure DevOps twin of GitHub Actions secrets. Same values,
different host. Do not invent a third copy in pipeline YAML.

### 7. Local `.env` (laptop only)

**Where**

- File: `.env` (gitignored)
- Template: [`.env.example`](../../.env.example)
- Documented in [secrets.md](../secrets.md)

**What belongs here**

| Name | Purpose |
|---|---|
| `GITHUB_USER` / `GITHUB_TOKEN` | Repo-local git credential helper |
| `DATABRICKS_HOST` / `DATABRICKS_TOKEN` | Optional local `bundle validate` / MLflow |
| `MLFLOW_TRACKING_URI` | Local tracking when not using Databricks |

Never copy `.env` into Actions secrets wholesale. Promote only the names CI
needs, through the GitHub / Azure DevOps secret UI.

## Decision examples

| Value | Store |
|---|---|
| Service principal token for workspace jobs | Key Vault key `databricks-token` |
| Same token for GitHub CD runner | GitHub Actions secret `DATABRICKS_TOKEN` |
| Same token for Azure Pipelines | Azure DevOps secret in group `iris-develop` |
| Workspace URL for CI | GitHub secret + Azure DevOps secret `DATABRICKS_HOST` |
| Endpoint `iris-species-ppe` | Built from `env_suffix: ppe` in `databricks/targets/ppe.yml` |
| `--alias ppe` on the train task | Job parameter fed from `${var.model_alias}` |
| `DATABRICKS_CLI_VERSION=0.272.1` | GitHub workflow `env:` (and Azure pipeline variable) |
| CD target choice `prod` | `workflow_dispatch` input `target` |
| Laptop GitHub PAT | `.env` only |
| Snowflake password used by a notebook | Key Vault (not a job parameter, not git) |

## Anti-patterns

1. **Secret in job parameters** — visible in the Runs UI.
2. **Secret in bundle variables committed to git** — still in history after you delete it.
3. **Env name only in a compute `spark_env_vars` block** — easy to forget when promoting `ppe` / `main`.
4. **Different token copies with different names and no doc** — rotate one, break the other. Keep names aligned (`DATABRICKS_TOKEN` vs Key Vault `databricks-token`) and document both in [secrets.md](../secrets.md).
5. **Putting promotion config only in GitHub variables** — Databricks jobs run without GitHub; env names must live in the bundle.

## Checklist before you add a new value

1. Secret? → Key Vault for workspace code; GitHub / Azure DevOps secret for CI. Update [secrets.md](../secrets.md) with the *name* only.
2. Differs by `develop` / `ppe` / `prod`? → bundle variable + target override.
3. Differs by a single run? → job parameter (or workflow input if the chooser is CI).
4. Needed on the laptop only? → `.env` + `.env.example` name.
5. Open the PR with empty values in examples. Paste real values only into the secret UI or Key Vault.
