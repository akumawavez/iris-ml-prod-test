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
- Add `databricks bundle deploy` or `databricks bundle run` to `azure-pipelines.yml` or `.github/workflows/ci.yml`. GitHub Actions CI may run tests. The rule is `.cursor/rules/azure-devops-only.mdc`.
- Dispatch CD unless `docs/cost-tracker.md` is approved. CD is `azure-pipelines-cd.yml` only, manual and gated. `.github/workflows/cd.yml` stays disabled.
- Train a replacement model unless the task is to update `models/iris_species`.

## Issues

Record defects in `issues.md`. Add an open row when you find one. Move it to Fixed in the same change as the fix. The rule is `.cursor/rules/issues-log.mdc`.

## Progress

Record finished work in `docs/progress.md`, newest day first. Add the bullet in the same change. The rule is `.cursor/rules/progress-log.mdc`. Defects stay in `issues.md`.

## Cursor files

- Project hooks: `.cursor/hooks.json` (cloud agents load these).
- Project skills: `.agents/skills/` (the shared pack). `codebase-to-course` stays in `.cursor/skills/`. Checklists are in `.agents/references/`. Do not commit `.agents/mcp_config.json`.
- Plugin: `plugins/iris-agent/` and `.cursor-plugin/marketplace.json`.
- Pre-commit: `.pre-commit-config.yaml`. `uv run pre-commit install` installs the commit hook and the pre-push pytest hook.
