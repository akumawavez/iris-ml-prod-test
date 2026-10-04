# Agent notes

`develop` is the integration branch. Open pull requests against `develop`. Do not force-push `develop`, `ppe`, or `prod`.

## Checks

```text
uv sync --locked --extra dev
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
```

`uv.lock` is the install source. `requirements.txt` is compiled for Databricks and Azure ML readers. Do not pip-install it in CI.

## Do not

- Commit `.env`, tokens, private keys, or connection strings. Variable names live in `.env.example`.
- Add `databricks bundle deploy` to `azure-pipelines.yml` or `.github/workflows/ci.yml`.
- Dispatch CD unless `docs/cost-tracker.md` is approved. CD is manual and gated.
- Train a replacement model unless the task is to update `models/iris_species`.

## Cursor files

- Project hooks: `.cursor/hooks.json` (cloud agents load these).
- Plugin: `plugins/iris-agent/` and `.cursor-plugin/marketplace.json`.
- Pre-commit: `.pre-commit-config.yaml`.
