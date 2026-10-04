# Secrets

Git pull and push in this repo always use a GitHub PAT from git-ignored `.env`
(`GITHUB_USER`, `GITHUB_TOKEN`). The repo-local credential helper does not
fall back to the macOS keychain or the `gh` login. Copy `.env.example` to
`.env` and put a classic PAT with `repo` scope there. Never commit `.env`
and never paste the token into chat or YAML.

Databricks and CI secrets follow one pattern: scope and key names are committed, values never are. The live secret scope is `kv-iris-ml-dev-7405` (backed by Key Vault `kv-iris-ml-dev-7405`); notebooks and scripts read keys such as `databricks-token` at runtime via `dbutils.secrets.get(scope, key)` with an environment-variable fallback so local `uv run` stays log-only, while CI maps `DATABRICKS_HOST` and `DATABRICKS_TOKEN` from the `iris-develop` variable group for validate-only reads. Gated CD does not use that token. It uses a service principal per environment: GitHub secrets `DATABRICKS_CLIENT_ID_DEVELOP`, `DATABRICKS_CLIENT_SECRET_DEVELOP`, and the same pair with `_PPE` and `_PROD`. Azure groups `iris-develop`, `iris-ppe`, and `iris-prod` hold `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` for that environment. Local development keeps the personal token in git-ignored `.env` only.

For *when* a value belongs in Key Vault versus Databricks bundle variables,
compute env, job parameters, or GitHub Actions secrets/inputs, see
[where-to-put-variables.md](guides/where-to-put-variables.md).

For *how* to create, rotate, and revoke every token (CLI first, then MCP,
then UI), see [token-lifecycle.md](guides/token-lifecycle.md).
