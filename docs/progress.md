# Progress

What has been built, newest day first. Add a bullet in the same change that
finishes the work. The rule is `.cursor/rules/progress-log.mdc`.

Defects stay in [issues.md](../issues.md). Release tags stay in
[CHANGELOG.md](../CHANGELOG.md). This page is the chronology.

Paid CD has not been dispatched. The $10 budget in
[cost-tracker.md](cost-tracker.md) is still proposed. A row here means the
description is in git, not that a workspace resource is live.

## 2026-10-10

- Release packaging is `scripts/release_package.py` (`uv build --wheel`).
  Azure CI and GitHub test CI build that wheel. Gated CD deploys it with
  `scripts/bundle_deploy.py --allow-missing`, which skips a missing
  workspace. `databricks bundle run` stays commented.

- Bundle checks follow `learning/MLOPS_MLE_PORTABILITY_SPEC.md` for the free
  lane: `scripts/bundle_validate.py` validates develop, ppe, and prod, and
  skips a target when the workspace or a catalog, model, or endpoint is
  missing. Local infer falls back to `models/iris_species`.

- `databricks.yml` includes `databricks/variables.yml`,
  `databricks/artifacts/*.yml`, `databricks/jobs/*.yml`, and
  `databricks/targets/*.yml`. Variable defaults moved out of the bundle root.



- Project pre-commit now fixes whitespace and line endings, and a pre-push
  hook runs pytest. Install both with `uv run pre-commit install`. GitHub
  Actions `.github/workflows/ci.yml` runs the same tests on pull requests
  and pushes to `develop`, `ppe`, and `main`. `.github/workflows/cd.yml`
  stays disabled. Deploy stays `azure-pipelines-cd.yml`, manual and gated.
  Project skills live in `.agents/skills/`: the Databricks, Azure, and MLflow
  packs, plus the Addy Osmani agent-skills pack
  (commit `1be8e34187e34647bb83adc3a1323b26ae6f6abe`). Checklists are in
  `.agents/references/`. `.agents/mcp_config.json` stays gitignored.
  `codebase-to-course` stays in `.cursor/skills/`. `.agents/skills/` is tracked
  in git. The pre-commit hooks and GitHub Actions test workflow are in git.

## 2026-10-08

- Zero-cost pause steps are in
  [zero-cost-until-next-run.md](zero-cost-until-next-run.md). Restore
  metadata without secret values is in
  `infra/restore/2026-10-08-metadata.json`. The delete order is in
  [deletion-summary-2026-10-08.md](deletion-summary-2026-10-08.md). Key Vault
  values are only in gitignored `backup/2026-10-08-zero-cost/`. Hello-world
  jobs and endpoints were exported first. `rg-iris-ml-dev` and the managed
  Databricks group were then deleted, the vault name was purged, and Azure
  DevOps pipelines 1, 2, and 3 were disabled. Vault values and personal
  names stay in the gitignored `backup/` directory. Pre-commit refuses that
  directory and `keyvault-secrets.json`. Working tree only, not committed.
- October charges are split by meter and by day in
  [cost-tracker.md](cost-tracker.md). With nothing running, the remaining
  charge is the managed NAT gateway and its public IP, about $1.20/day.
  Working tree only, not committed.
- Remaining feature branches are merged into `develop`. The current CI and CD
  pipelines stay. Pre-commit now blocks secret filenames, token literals, and
  deploy commands in the test pipeline. `ppe` and `main` already match
  `develop` and stay as the promotion branches. Committed on
  feature/merge-remaining-branches.
- Default CD `serve` does not start the train or infer jobs. Both jobs allow
  one run and stop on their own (train 20 minutes, infer 10 minutes). The
  idle charge is the StandardV2 NAT gateway in the Databricks-managed
  resource group. The warehouse is stopped, no clusters are running, and
  the iris endpoints that exist are Small CPU with scale-to-zero. That NAT
  was left in place. Committed on feature/manual-cd-and-cost. Paid CD was not run.
- A manual CD run selects the commit, `serve` or `train-and-serve`, and
  `Champion`, the env alias, or a model version. Train no longer moves
  Champion. That alias moves only when `promoteChampion` is `YES`. The
  guide is [databricks-champion-and-manual-run.md](guides/databricks-champion-and-manual-run.md).
  Committed on feature/manual-cd-and-cost. Paid CD was not run.
- CI and CD steps run only after the previous step succeeds. Publishing
  test results still runs when the tests fail. Infer runs only when
  `runMode` is `train-and-serve`, and only after train succeeds. Working
  tree only, not committed.
- CI and CD read the service principal secret from Key Vault
  `kv-iris-ml-dev-7405` after service connection `sc-iris-keyvault` signs
  in as `id-iris-ml`. The password is not a GitHub secret. The disabled
  GitHub workflow uses the same login and vault read. Working tree only,
  not committed.
- CD uses one `envSuffix` variable, set from the queued branch (`main` becomes
  `prod`). One deploy stage and one Databricks command step use that suffix
  for the target, the variable group, and the approval environment. Working
  tree only, not committed.
- [eli25-cd-require-service-principal.md](guides/eli25-cd-require-service-principal.md)
  explains `scripts/cd_require_service_principal.py`: the step must have
  the Entra service principal, and a personal token is refused. Working
  tree only, not committed.
- Train and infer are separate serverless jobs, `iris-ml-train-<env>` and
  `iris-ml-infer-<env>`. CD runs train, then infer, only when `runMode` is
  `train-and-serve`. Develop was deployed
  and both jobs passed: train registered version 13 at accuracy 1.0, infer
  scored setosa then virginica. Committed on feature/manual-cd-and-cost.
- Service principals `sp-iris-develop`, `sp-iris-ppe`, and `sp-iris-prod`,
  and managed identity `id-iris-ml`, are granted in Azure and Databricks.
  Client ids are in `infra/identities.json`. Secrets stay in Key Vault and
  the variable groups. The walk-through is
  [eli25-identities.md](guides/eli25-identities.md). Working tree only,
  not committed. Paid CD was not dispatched.
- Azure DevOps CI and CD follow the branch line. CI runs on pull requests
  into `develop`, `ppe`, and `main`, and on pushes to those branches.
  CD is manual, requires `YES`, and fails unless the branch is one of
  those three. The deploy stage loads only `iris-<envSuffix>`.
  Committed on feature/manual-cd-and-cost.
- Environment names are the `env_suffix` variable, appended to jobs,
  endpoints, experiments, and the CD stage (`iris-species-develop`,
  `iris-ml-job-pipeline-develop`). Committed on feature/manual-cd-and-cost.
- Databricks bundle best practices are in
  [databricks-bundle-best-practices.md](guides/databricks-bundle-best-practices.md):
  one bundle, target overrides, the uv wheel, and validate versus gated
  deploy. Committed on feature/manual-cd-and-cost.
- The uv package in `src/iris_model` is a bundle wheel (`uv build --wheel`).
  Job compute installs that wheel. `notebooks/train_register.py` and
  `notebooks/infer.py` import `iris_model` from the installed library.
  Committed on feature/manual-cd-and-cost.
- Code movement from `develop` to `ppe` to `main`, and the Databricks
  environment each branch deploys, is written up in
  [eli25-code-movement.md](guides/eli25-code-movement.md). The same pairs
  live in `src/iris_model/promotion.py`. CD calls
  `scripts/assert_deploy_branch.py` and stops when the branch does not match
  the target. Committed on feature/manual-cd-and-cost.

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
