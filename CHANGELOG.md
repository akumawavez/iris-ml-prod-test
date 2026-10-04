# Changelog

Newest on top. Code releases are git tags (`vX.Y.Z`); model versions live in
the MLflow registry. See `docs/releases.md`.

## Unreleased

- Train + inference job pipeline: `notebooks/infer.py` batch-scores the known
  setosa/virginica rows; `databricks/tasks/` and `databricks/jobs/` add
  serverless infer job `iris-infer-script-serverless` and multi-task job
  `iris-ml-job-pipeline` (train then infer). Serving endpoint `iris-species-dev`
  stays in `databricks/artifacts/` so CI validates and gated CD deploys jobs +
  endpoint together.
- Databricks Jobs + serving spec and plan: design spec
  (`docs/superpowers/specs/2026-09-30-iris-databricks-jobs-serving-design.md`)
  and implementation plan (`docs/superpowers/plans/2026-09-30-iris-databricks-jobs-serving.md`)
  for a jobs-only training path (notebook Job-A on personal compute, script Job-B
  on serverless) over existing iris logic; no code changes, no deploy/run.
- CD pipeline for Databricks deployment: implemented complete deployment workflow
  in both Azure DevOps (`azure-pipelines-cd.yml`) and GitHub Actions (`.github/workflows/cd.yml`).
  Includes official Databricks CLI setup, bundle validation (`databricks bundle validate -t develop`),
  gated environment deployment (`databricks bundle deploy -t develop`), endpoint status verification
  (`databricks serving-endpoints get iris-species-dev`), and post-deploy inference smoke test.
- Local CD test script (`scripts/test_cd_pipeline.ps1`) for safe offline validation and smoke checks.
- Comprehensive contract tests in `tests/test_pipeline_contract.py` verifying CD pipeline structure,
  CLI setup, bundle validation, deployment steps, and safety constraints.
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
