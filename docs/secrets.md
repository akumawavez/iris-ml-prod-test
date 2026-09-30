# Secrets

Databricks and CI secrets follow one pattern: scope and key names are committed, values never are. The live secret scope is `kv-iris-ml-dev-7405` (backed by Key Vault `kv-iris-ml-dev-7405`); notebooks and scripts read keys such as `databricks-token` at runtime via `dbutils.secrets.get(scope, key)` with an environment-variable fallback so local `uv run` stays log-only, while CI maps the same names (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`) from the `iris-develop` variable group and local development keeps them in git-ignored `.env` only.
