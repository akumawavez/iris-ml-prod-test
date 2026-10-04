# Secrets

Git pull and push in this repo always use a GitHub PAT from git-ignored `.env`
(`GITHUB_USER`, `GITHUB_TOKEN`). The repo-local credential helper does not
fall back to the macOS keychain or the `gh` login. Copy `.env.example` to
`.env` and put a classic PAT with `repo` scope there. Never commit `.env`
and never paste the token into chat or YAML.

Databricks and CI secrets follow one pattern: scope and key names are committed, values never are. The live secret scope is `kv-iris-ml-dev-7405` (backed by Key Vault `kv-iris-ml-dev-7405` in `rg-iris-ml-dev`). Notebooks and scripts read keys at runtime via `dbutils.secrets.get(scope, key)` with an environment-variable fallback so local `uv run` stays log-only. CI maps `DATABRICKS_HOST` and `DATABRICKS_TOKEN` from the `iris-develop` variable group. Local git still reads `GITHUB_TOKEN` from git-ignored `.env`.

| Key Vault secret | What it is |
|---|---|
| `databricks-token` | Current Databricks PAT used by the `ajai-dbx` CLI profile |
| `github-token` | GitHub PAT from local `.env` (`GITHUB_TOKEN`) |
| `azure-client-secret` | Azure service principal secret already stored in the vault |

For *when* a value belongs in Key Vault versus Databricks bundle variables,
compute env, job parameters, or GitHub Actions secrets/inputs, see
[where-to-put-variables.md](guides/where-to-put-variables.md).

For *how* to create, rotate, and revoke every token (CLI first, then MCP,
then UI), see [token-lifecycle.md](guides/token-lifecycle.md).
