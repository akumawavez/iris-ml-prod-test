# Agent notes

Promotion is `feature/*` → `develop` → `ppe` → `main`. `main` is the prod branch and deploys Databricks target `prod`. Open feature pull requests against `develop`. Do not force-push `develop`, `ppe`, or `main`.

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
- Add `databricks bundle deploy` to `azure-pipelines.yml`.
- Enable GitHub Actions. CI and CD run only in Azure DevOps. The rule is `.cursor/rules/azure-devops-only.mdc`.
- Dispatch CD unless `docs/cost-tracker.md` is approved. CD is `azure-pipelines-cd.yml` only, manual and gated.
- Train a replacement model unless the task is to update `models/iris_species`.

## Issues

Record defects in `issues.md`. Add an open row when you find one. Move it to Fixed in the same change as the fix. The rule is `.cursor/rules/issues-log.mdc`.

## Cursor files

- Project hooks: `.cursor/hooks.json` (cloud agents load these).
- Plugin: `plugins/iris-agent/` and `.cursor-plugin/marketplace.json`.
- Pre-commit: `.pre-commit-config.yaml`.
