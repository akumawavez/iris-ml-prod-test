# Changelog

Newest on top. Code releases are git tags (`vX.Y.Z`); model versions live in
the MLflow registry. See `docs/releases.md`.

## Unreleased

- uv-only toolchain: real `[project]` + dev extras in `pyproject.toml`,
  committed `uv.lock`, `.python-version` 3.13; `requirements.txt` is now the
  output of `uv pip compile --universal` (Windows-only pins carry markers, so
  Linux CI installs cleanly). CI syncs with `uv sync --locked` and also runs
  ruff check + format. Python floor is >=3.12 (pinned `shap` requires it).
- CI runs only when required: GitHub Actions test-only CI plus batched,
  path-filtered Azure DevOps triggers; docs-only edits skip both.
- Manual-only gated CD (`azure-pipelines-cd.yml`, `.github/workflows/cd.yml`);
  uncreated and undispatched until cost approval.
- $10/month spend cap with 50/80/100% budget alerts (`docs/cost-tracker.md`,
  `docs/cost-dashboard.html`, `infra/budget.bicep`, `scripts/setup_budget.ps1`)
  and read-only 30-minute snapshots (`scripts/cost_snapshot.ps1`).
- Zero-spend shutdown and restore guide (`docs/teardown-and-restore.md`,
  `scripts/teardown_dev.ps1`); nothing deleted by default.
- Serving POST inference check (`scripts/test_serving.py --dry-run`,
  `docs/serving-inference-test.md`).
