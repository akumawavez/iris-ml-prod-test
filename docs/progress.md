# Progress

What has been built, newest day first. Add a bullet in the same change that
finishes the work. The rule is `.cursor/rules/progress-log.mdc`.

Defects stay in [issues.md](../issues.md). Release tags stay in
[CHANGELOG.md](../CHANGELOG.md). This page is the chronology.

Paid CD has not been dispatched. The $10 budget in
[cost-tracker.md](cost-tracker.md) is still proposed. A row here means the
description is in git, not that a workspace resource is live.

## 2026-10-04

- The interactive course now teaches Databricks MLOps instead of flower
  scoring. Six sittings, three days a week: the loop, Asset Bundles, jobs,
  MLflow and the Unity Catalog registry, model serving endpoints, and the
  practices this repo follows. Open
  [the course](courses/agentic-productionalisation/index.html).
  Finished work is recorded in this file.
- GitHub Actions is disabled. CI and CD stay in Azure DevOps
  (`azure-pipelines.yml`, `azure-pipelines-cd.yml`).
- Cursor skill `codebase-to-course` is in `.cursor/skills/codebase-to-course/`.
  The four-week reading list is
  [productionalisation-study-plan.md](guides/productionalisation-study-plan.md).
- MLOps readiness scores and the gateway guide landed with the merge of
  `feature/mlops-readiness`.
- Gated CD serves the environment alias version and deploys as a
  per-environment service principal. A personal access token is unset for
  that deploy.
- Standalone train and infer jobs that never ran were removed from the
  bundle. The only job is `iris-ml-job-pipeline`. Defects from that pass
  are in `issues.md`.
- Guides: where to put variables, and how to create, rotate, and delete tokens.
- Productionalisation checklist: `docs/productionalisation/` (folders, files,
  workflows, rules, markdown).
- Promotion is `feature/*` → `develop` → `ppe` → `main`. `main` deploys
  Databricks target `prod`. CI validates. CD deploys a target only from its
  matching git branch.
- Pre-commit, Cursor project hooks, and the `iris-agent` plugin: no
  force-push of `develop`, `ppe`, or `main`, no secret files in agent
  context, ruff on edited Python.
- CD creates a missing endpoint with `serving-endpoints create --no-wait`
  and does not wait on the container inside `bundle deploy`.
- Serverless train falls back to `/Shared/<experiment>` when the job has no
  Databricks username. `python-dotenv` is optional on the job. Serving pins
  install with `-r`.
- PPE and prod targets share one workspace host, with env prefixes, tags,
  and Unity Catalog aliases (`@develop`, `@ppe`, `@prod`, plus Champion).
- The bundle is split under `databricks/` (jobs, targets, artifacts). The
  train-then-infer pipeline is the deployed job.
- ELI25 guides: lifecycle, productionalisation, jobs and serving, and the
  Vechtomova / Databricks map.
- Postman collection for a serving smoke test. The token stays empty in git.

## 2026-09-30

- Design spec and implementation plan for Databricks jobs and serving.
  No deploy in that pass.
- Two job shapes: a notebook path on personal compute, and a script path on
  serverless. `bundle validate` runs in CI. Secrets stay named, not valued,
  in `docs/secrets.md`.

## 2026-09-27

- Repo foundation: `develop` as the integration branch, branch rules, secret
  ignore rules, ADR-001 (develop-only serving path), and the Azure DevOps,
  Asset Bundle, and promotion guides.
- Local model: `models/iris_species` checked in. Score loads it and returns
  the species plus both explanations. Tests do not train.
- Bundle and pipeline description. CI runs pytest and does not deploy.
  Cost sheet and approval gate written.
- Test-only CI on GitHub and Azure DevOps, path-filtered so docs-only edits
  skip the run.
- Manual gated CD in `azure-pipelines-cd.yml` and `.github/workflows/cd.yml`,
  present and not dispatched until the cost tracker is approved.
- $10/month cap, alerts, cost dashboard, and 30-minute snapshots.
- Teardown and restore guide. Serving POST check defaults to dry-run.
- uv is the only installer. `uv.lock` is committed. `requirements.txt` is
  compiled for Databricks readers.
- CD workflow implemented and covered by contract tests: CLI setup,
  `bundle validate`, gated `bundle deploy`, endpoint status, smoke step.
- Legacy serving `auto_capture_config` removed so endpoint create is not
  rejected.
