# Create, update, and delete tokens

How to mint, rotate, and revoke every credential this project uses.
Companion docs: [secrets.md](../secrets.md) (names and scopes) and
[where-to-put-variables.md](where-to-put-variables.md) (which store).

**Method order for every operation:**

1. **CLI** (preferred) — `gh`, `databricks`, `az`
2. **MCP** (second) — only when a Cursor MCP server exposes the same
   create / update / delete action for that host
3. **UI** (last) — browser console when the CLI cannot create the object
   (common for GitHub PATs) or when you do not have the CLI installed

Never paste a live token into chat, a pull request, YAML, or a notebook cell.
Pipe values from stdin or a local file. Do not `echo` tokens into shell history
when you can avoid it (`read -s`, process substitution, or `gh secret set`
with no `--body` so it prompts).

## Token inventory

| Credential | Used by | Stores that hold a copy |
|---|---|---|
| GitHub PAT (`GITHUB_TOKEN`) + `GITHUB_USER` | Laptop git pull/push for this repo | Local `.env` only |
| Databricks host (`DATABRICKS_HOST`) | CLI, CI, local MLflow | Not secret by nature, but treated as CI config: `.env`, GitHub Actions secret, Azure DevOps variable group |
| Databricks token (`DATABRICKS_TOKEN` / Key Vault `databricks-token`) | Jobs via `dbutils.secrets`, local CLI, GitHub CD, Azure Pipelines | Key Vault `kv-iris-ml-dev-7405`, GitHub Actions secret, Azure DevOps `iris-develop`, optional `.env` |
| Built-in Actions `github.token` | GitHub Actions workflows only | Issued per job by GitHub — do **not** put this in `.env` |

Optional later (not required today): Azure service-principal
`AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_CLIENT_SECRET` for non-PAT
Databricks auth. Same lifecycle rules as `DATABRICKS_TOKEN`.

## Prerequisites (CLI)

```bash
# GitHub CLI — https://cli.github.com
gh auth login
gh auth status

# Databricks CLI 0.272.1+ — https://docs.databricks.com/dev-tools/cli/install.html
databricks -v
databricks auth login --host "$DATABRICKS_HOST"

# Azure CLI — https://learn.microsoft.com/cli/azure/install-azure-cli
az login
az account show
```

Repo constants used below:

```bash
export GH_REPO=akumawavez/iris-ml-prod-test
export KV_NAME=kv-iris-ml-dev-7405
export DBX_SCOPE=kv-iris-ml-dev-7405
export ADO_GROUP=iris-develop
```

## MCP note (second choice)

Use an MCP tool only when it maps 1:1 to a CLI action on the same host
(for example a GitHub MCP `create_or_update_secret`, an Azure MCP
`keyvault_secret_set`, or a Databricks MCP `tokens_create`).

In this Cloud Agent environment there is **no** secrets-management MCP
today — only CI/PR subscriptions and Cursor cloud diagnostics. Until you
connect a GitHub / Azure / Databricks MCP server in Cursor settings and
authenticate it (`mcp_auth` when the server requires it):

- Prefer the CLI commands in this guide.
- Fall back to the UI sections when the CLI cannot create the credential.

Do not confuse MCP server auth (`mcp_auth`) with project tokens. MCP auth
lets the agent call a server; it does not replace `GITHUB_TOKEN` or
`DATABRICKS_TOKEN` in `.env` / Key Vault / Actions.

---

## 1. GitHub PAT for local `.env` (`GITHUB_TOKEN`)

This PAT is for **laptop git only**. It is not the Actions
`${{ secrets.* }}` store and not the per-job `github.token`.

`.env.example` names:

```text
GITHUB_USER=akumawavez
GITHUB_TOKEN=
```

### Create

**CLI (partial):** `gh` can log in and print the token it already stores,
but **creating a new classic or fine-grained PAT is a UI (or API) step**.

```bash
# Option A — use gh's own login token for interactive git on this machine
# (does not write .env; this repo's helper reads .env instead)
gh auth login
gh auth token   # shows the token gh uses; do not commit it

# Option B — create a fine-grained PAT via API (needs an existing admin token)
# Prefer the UI unless you already automate PAT minting.
gh api \
  --method POST \
  /user/tokens \
  -f note='iris-ml-prod-test-local-git' \
  -f scopes='["repo"]'   # classic-token API shape; org policies may block this
```

**MCP:** If a GitHub MCP exposes PAT creation, use it. Most GitHub MCPs
manage repos/issues/PRs, not PAT minting — expect to use UI.

**UI (usual path for create):**

1. GitHub → profile → **Settings** → **Developer settings** →
   **Personal access tokens**.
2. Prefer **Fine-grained token**: resource owner your user, repository
   access = only `iris-ml-prod-test`, permissions = Contents **Read and
   write** (and Metadata read). Classic alternative: scope `repo` only.
3. Generate, copy once.

**Write into `.env` (CLI file edit, never commit):**

```bash
test -f .env || cp .env.example .env
# paste when prompted — value never goes on the command line
read -s -p "GITHUB_TOKEN: " GITHUB_TOKEN; echo
# macOS/Linux portable upsert
grep -q '^GITHUB_TOKEN=' .env \
  && sed -i.bak "s|^GITHUB_TOKEN=.*|GITHUB_TOKEN=${GITHUB_TOKEN}|" .env \
  || echo "GITHUB_TOKEN=${GITHUB_TOKEN}" >> .env
unset GITHUB_TOKEN
git check-ignore -q .env   # must succeed
```

Prove it:

```bash
git ls-remote origin HEAD
```

### Update (rotate)

1. Create a **new** PAT (UI / API) — do not reuse the old string.
2. Replace `GITHUB_TOKEN=` in `.env` with the new value (same `read -s` flow).
3. Prove with `git ls-remote origin HEAD`.
4. Delete the old PAT (next section).

### Delete (revoke)

**CLI:**

```bash
# List classic PATs (fine-grained listing differs by API)
gh api /user/tokens --jq '.[].id,.[].note'

# Delete classic PAT by id
gh api --method DELETE /user/tokens/TOKEN_ID
```

**UI:** Developer settings → Personal access tokens → **Revoke** / **Delete**
on the old token.

**Local cleanup:** remove or blank `GITHUB_TOKEN=` in `.env`. Do not leave
revoked values lying around.

---

## 2. Databricks personal access token (`DATABRICKS_TOKEN`)

Used as:

| Store | Name |
|---|---|
| Local `.env` (optional) | `DATABRICKS_TOKEN` |
| GitHub Actions | secret `DATABRICKS_TOKEN` |
| Azure DevOps group `iris-develop` | secret `DATABRICKS_TOKEN` |
| Key Vault / secret scope | key `databricks-token` |

CD does not use this PAT. Deploy and CD validate use a service principal:

| Environment | Key Vault secret | Azure variable group |
|---|---|---|
| develop | `sp-iris-develop-client-secret` | `iris-develop` keys `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `DATABRICKS_HOST`, `DATABRICKS_AZURE_RESOURCE_ID` |
| ppe | `sp-iris-ppe-client-secret` | `iris-ppe` |
| prod | `sp-iris-prod-client-secret` | `iris-prod` |

`DATABRICKS_HOST` and `ARM_TENANT_ID` are still required. CI and CD unset `DATABRICKS_TOKEN` so the CLI cannot prefer a user. The applications are `sp-iris-develop`, `sp-iris-ppe`, and `sp-iris-prod`. Azure Databricks signs those apps in with `ARM_CLIENT_ID` and `ARM_CLIENT_SECRET`, not `DATABRICKS_CLIENT_ID`. The pipeline gets `ARM_CLIENT_SECRET` by reading Key Vault secret `sp-iris-<env>-client-secret` after `id-iris-ml` signs in. Client ids are in `infra/identities.json`. Managed identity `id-iris-ml` has no secret. The walk-through is [eli25-identities.md](eli25-identities.md). A user PAT remains the laptop credential. Do not commit a secret, and do not paste the client secret into GitHub.

### Create

**CLI (preferred):**

```bash
# Interactive login first if needed
databricks auth login --host "https://adb-7405619226406985.5.azuredatabricks.net"

# Mint a PAT (comment helps you find it later)
databricks tokens create --comment "iris-ml-prod-test-$(date +%Y%m%d)" --lifetime-seconds 7776000
# Save the token_value from the JSON once — it is shown only at creation.
```

**MCP:** Use a Databricks MCP `tokens create` equivalent if connected.

**UI:** Workspace → click user email → **Settings** → **Developer** →
**Access tokens** → **Generate new token**.

Also set the non-secret host everywhere you store the token:

```bash
export DATABRICKS_HOST=https://adb-7405619226406985.5.azuredatabricks.net
```

### Update (rotate) — do stores in this order

Create the new token first (CLI above). Then write the **new** value to
every store that still has the old one. Only after all stores work, delete
the old Databricks token.

1. **Key Vault** (workspace jobs read this) — see [§4](#4-azure-key-vault-secret-databricks-token).
2. **GitHub Actions secret** — see [§3](#3-github-actions-secrets-databricks_host--databricks_token).
3. **Azure DevOps variable group** — see [§5](#5-azure-devops-variable-group-iris-develop).
4. **Local `.env`** — same `read -s` upsert as `GITHUB_TOKEN`, keys
   `DATABRICKS_HOST` / `DATABRICKS_TOKEN`.

Prove each layer:

```bash
# Local / CLI identity
DATABRICKS_HOST=... DATABRICKS_TOKEN=... databricks current-user me
databricks bundle validate -t develop

# GitHub: empty dry run that at least sees the secret name
gh secret list --repo "$GH_REPO"
```

### Delete (revoke old PAT)

**CLI:**

```bash
databricks tokens list
databricks tokens delete --token-id TOKEN_ID
```

**UI:** same Access tokens page → **X** on the old token.

---

## 3. GitHub Actions secrets (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`)

Used by [`.github/workflows/cd.yml`](../../.github/workflows/cd.yml).
CD also binds environments `develop` / `ppe` / `prod` — put secrets on the
**environment** when you want per-env approval isolation; otherwise
repository secrets are enough for a single shared workspace host.

### Create or update

**CLI (preferred):** `gh secret set` creates or overwrites.

```bash
# Prompted (no value in shell history)
printf '%s' "$DATABRICKS_HOST" | gh secret set DATABRICKS_HOST --repo "$GH_REPO"
printf '%s' "$DATABRICKS_TOKEN" | gh secret set DATABRICKS_TOKEN --repo "$GH_REPO"

# Or environment-scoped (recommended once iris CD environments exist)
printf '%s' "$DATABRICKS_TOKEN" | gh secret set DATABRICKS_TOKEN --repo "$GH_REPO" --env develop
printf '%s' "$DATABRICKS_TOKEN" | gh secret set DATABRICKS_TOKEN --repo "$GH_REPO" --env ppe
printf '%s' "$DATABRICKS_TOKEN" | gh secret set DATABRICKS_TOKEN --repo "$GH_REPO" --env prod
```

List (names only):

```bash
gh secret list --repo "$GH_REPO"
gh secret list --repo "$GH_REPO" --env develop
```

**MCP:** GitHub MCP secret set/update if available.

**UI:** repo → **Settings** → **Secrets and variables** → **Actions** →
**New repository secret** (or Environment → environment secrets).

### Delete

**CLI:**

```bash
gh secret delete DATABRICKS_TOKEN --repo "$GH_REPO"
gh secret delete DATABRICKS_TOKEN --repo "$GH_REPO" --env develop
```

**UI:** same Secrets page → **Delete**.

Do not delete `DATABRICKS_HOST` / `DATABRICKS_TOKEN` while gated CD still
needs them unless you are decommissioning deploy.

---

## 4. Azure Key Vault secret (`databricks-token`)

Scope `kv-iris-ml-dev-7405` is **Azure Key Vault-backed**. Databricks can
*read* it (`dbutils.secrets.get`); you **create / update / delete the value
in Key Vault**, not with `databricks secrets put-secret`.

### Create or update

**CLI (preferred):**

```bash
# Create or set a new version
az keyvault secret set \
  --vault-name "$KV_NAME" \
  --name databricks-token \
  --value "$DATABRICKS_TOKEN"

# Confirm metadata only (value is redacted / requires show)
az keyvault secret show \
  --vault-name "$KV_NAME" \
  --name databricks-token \
  --query "{name:name,updated:attributes.updated,enabled:attributes.enabled}"
```

If the Databricks secret scope does not exist yet:

```bash
# Azure Key Vault-backed scope — DNS and resource id from your vault
databricks secrets create-scope "$DBX_SCOPE" \
  --scope-backend-type AZURE_KEYVAULT \
  --resource-id "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/$KV_NAME" \
  --dns-name "https://$KV_NAME.vault.azure.net/"
```

(Exact flags follow your installed Databricks CLI version; UI alternative
below if the CLI rejects Key Vault flags.)

**MCP:** Azure MCP Key Vault secret set, if connected.

**UI:**

1. Azure Portal → Key Vault `kv-iris-ml-dev-7405` → **Secrets** →
   **Generate/Import** → name `databricks-token`.
2. Databricks workspace → **Settings** → **Secrets** (or the secrets UI /
   `#secrets/createScope` URL) to attach the Key Vault-backed scope if it
   is missing.

Prove from a workspace notebook or job (never print the value):

```python
bool(dbutils.secrets.get(scope="kv-iris-ml-dev-7405", key="databricks-token"))
```

### Delete

**CLI:**

```bash
# Soft-delete (recoverable until purge)
az keyvault secret delete --vault-name "$KV_NAME" --name databricks-token

# Permanent (only if vault soft-delete + purge are allowed and you mean it)
az keyvault secret purge --vault-name "$KV_NAME" --name databricks-token
```

**UI:** Key Vault → Secrets → secret → **Delete**.

Rotating is better than deleting: `az keyvault secret set` adds a new
version; disable the old version if you need a kill switch without removing
the name jobs expect.

```bash
az keyvault secret set-attributes \
  --vault-name "$KV_NAME" \
  --name databricks-token \
  --version OLD_VERSION \
  --enabled false
```

---

## 5. Azure DevOps variable group `iris-develop`

Pipeline YAML reads `$(DATABRICKS_HOST)` and `$(DATABRICKS_TOKEN)` from
group `iris-develop` ([azure-pipelines.yml](../../azure-pipelines.yml)).

### Create group (once)

**CLI (preferred):**

```bash
# Set defaults once per machine/org
az devops configure --defaults organization=https://dev.azure.com/<your-org> project=iris-ml-prod-test

az pipelines variable-group create \
  --name "$ADO_GROUP" \
  --authorize true \
  --variables DATABRICKS_HOST="$DATABRICKS_HOST"
```

### Create or update secret variables

**CLI:**

```bash
GROUP_ID=$(az pipelines variable-group list --group-name "$ADO_GROUP" --query "[0].id" -o tsv)

# Create secret
az pipelines variable-group variable create \
  --group-id "$GROUP_ID" \
  --name DATABRICKS_TOKEN \
  --value "$DATABRICKS_TOKEN" \
  --secret true

# Update secret
az pipelines variable-group variable update \
  --group-id "$GROUP_ID" \
  --name DATABRICKS_TOKEN \
  --value "$DATABRICKS_TOKEN" \
  --secret true

# Update host (non-secret is fine)
az pipelines variable-group variable update \
  --group-id "$GROUP_ID" \
  --name DATABRICKS_HOST \
  --value "$DATABRICKS_HOST"
```

**MCP:** Azure DevOps MCP variable-group tools, if connected.

**UI:** Azure DevOps → **Pipelines** → **Library** → variable group
`iris-develop` → add / update `DATABRICKS_HOST`, lock `DATABRICKS_TOKEN`
as secret → **Save**.

### Delete

**CLI:**

```bash
az pipelines variable-group variable delete \
  --group-id "$GROUP_ID" \
  --name DATABRICKS_TOKEN \
  --yes
```

**UI:** Library → group → delete variable → Save.

---

## 6. Local `.env` maintenance (all keys)

Template: [`.env.example`](../../.env.example). Expected keys over time:

```text
GITHUB_USER=
GITHUB_TOKEN=
DATABRICKS_HOST=
DATABRICKS_TOKEN=
MLFLOW_TRACKING_URI=   # optional; often "databricks" or a local sqlite URI
```

**CLI:**

```bash
cp -n .env.example .env
${EDITOR:-nano} .env          # or the read -s upsert pattern above
chmod 600 .env
grep -E '^(GITHUB_|DATABRICKS_|MLFLOW_)' .env | sed 's/=.*/=***/'   # names only
```

**MCP:** do not ask an agent to read or rewrite `.env` (project hooks block
secret-file reads). Edit locally.

**UI:** not applicable — it is a local file.

**Delete local copies:** wipe values or `rm .env` when leaving a machine.
Revoking the upstream PAT/token is what actually disables access.

---

## End-to-end rotation runbook

When a Databricks token may be leaked, or on a scheduled rotation:

1. **Create** a new Databricks token (CLI `databricks tokens create`).
2. **Update Key Vault** `databricks-token` (CLI `az keyvault secret set`).
3. **Update GitHub Actions** `DATABRICKS_TOKEN` (CLI `gh secret set`).
4. **Update Azure DevOps** group secret (CLI `az pipelines variable-group variable update`).
5. **Update local `.env`** if you keep a laptop copy.
6. **Prove:** `databricks current-user me`, `databricks bundle validate -t develop`,
   and a workspace secret read that returns non-empty without printing it.
7. **Delete** the old Databricks token (`databricks tokens delete`).
8. Record *that* a rotation happened in your ops notes — never record the value.
   A one-line `CHANGELOG` note is optional and must not include the token.

GitHub PAT rotation is independent: mint new PAT → update `.env` → revoke old
PAT. It does not touch Key Vault or Actions Databricks secrets.

## Quick command index

| Action | CLI |
|---|---|
| Set Actions secret | `gh secret set NAME --repo "$GH_REPO"` |
| Delete Actions secret | `gh secret delete NAME --repo "$GH_REPO"` |
| List Actions secrets | `gh secret list --repo "$GH_REPO"` |
| Create Databricks PAT | `databricks tokens create --comment '...'` |
| List / delete Databricks PAT | `databricks tokens list` / `databricks tokens delete --token-id ID` |
| Set Key Vault secret | `az keyvault secret set --vault-name "$KV_NAME" --name databricks-token --value ...` |
| Delete Key Vault secret | `az keyvault secret delete --vault-name "$KV_NAME" --name databricks-token` |
| Update ADO secret | `az pipelines variable-group variable update --group-id ID --name DATABRICKS_TOKEN --secret true --value ...` |
| Show gh login token | `gh auth token` (not a substitute for repo `.env` unless you change the helper) |

## Anti-patterns

1. Putting the laptop `GITHUB_TOKEN` into GitHub Actions secrets — Actions
   already has `github.token`; CD needs `DATABRICKS_*`, not your git PAT.
2. Using `databricks secrets put-secret` on a Key Vault-backed scope — use
   `az keyvault secret set` instead.
3. Rotating Actions but forgetting Key Vault (or the reverse) — jobs and CD
   break at different times.
4. Asking Cursor / MCP to "read `.env` and fix the token" — blocked on
   purpose; paste into the secret CLI prompt yourself.
5. Committing `.env` or putting tokens in `workflow_dispatch` inputs.
