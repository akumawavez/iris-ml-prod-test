# Changelog

Newest on top. Code releases are git tags (`vX.Y.Z`); model versions live in
the MLflow registry. See `docs/releases.md`.

## Unreleased

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
