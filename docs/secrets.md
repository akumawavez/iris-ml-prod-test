# Secrets

Git pull and push in this repo always use a GitHub PAT from git-ignored `.env`
(`GITHUB_USER`, `GITHUB_TOKEN`). The repo-local credential helper does not
fall back to the macOS keychain or the `gh` login. Copy `.env.example` to
`.env` and put a classic PAT with `repo` scope there. Never commit `.env`
and never paste the token into chat or YAML.

Databricks and CI secrets follow one pattern: scope and key names are committed, values never are. The live secret scope is `kv-iris-ml-dev-7405` (backed by Key Vault `kv-iris-ml-dev-7405`). Notebooks read keys such as `databricks-token` at runtime via `dbutils.secrets.get(scope, key)`. CI and CD sign in as managed identity `id-iris-ml` through service connection `sc-iris-keyvault`, then read `sp-iris-<env>-client-secret` from that vault and pass it as `ARM_CLIENT_SECRET`. The variable groups `iris-develop`, `iris-ppe`, and `iris-prod` hold the host, tenant, and client id. They do not hold the password. A laptop may still use a personal token in git-ignored `.env`. `id-iris-ml` has no password. Names and client ids are in `infra/identities.json`. See [eli25-identities.md](guides/eli25-identities.md). The disabled GitHub workflow uses the same Key Vault read after `azure/login`. It does not use GitHub secrets.

For *when* a value belongs in Key Vault versus Databricks bundle variables,
compute env, job parameters, or GitHub Actions secrets/inputs, see
[where-to-put-variables.md](guides/where-to-put-variables.md).

For *how* to create, rotate, and revoke every token (CLI first, then MCP,
then UI), see [token-lifecycle.md](guides/token-lifecycle.md).
