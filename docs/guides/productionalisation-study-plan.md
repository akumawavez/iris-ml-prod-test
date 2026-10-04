# Productionalisation study plan

Date: 4 October 2026

An interactive Databricks MLOps course, six sittings over two weeks, is
[agentic-productionalisation/index.html](../courses/agentic-productionalisation/index.html).
Open that file in a browser. This page is the longer four-week reading list.

Study this repo three days a week for four weeks. Each week is one
productionalisation slice: what is in git, which skill the agent used to
build it, and a free check. Do not run `databricks bundle deploy` or a live
score while you study. Those spend money, and the $10 budget in
[cost-tracker.md](../cost-tracker.md) is still only proposed.

The checklist those weeks walk is
[productionalisation/README.md](../productionalisation/README.md). The
plain-language names are in
[eli25-databricks-productionalisation.md](eli25-databricks-productionalisation.md).

## How the agentic work was done

A human locked the decisions in a spec or an ADR. An implementation plan
under `docs/superpowers/plans/` then told the agent the branch, the files,
the "done when" check, and the hard stops: feature branch, pull request
into `develop`, tests only, no secrets, no cloud create. The agent wrote
the files. Contract tests in `tests/` froze those rules so a later agent
could not quietly put `bundle deploy` into CI.

Three layers told the agent what to do:

| Layer | Where | Job |
|---|---|---|
| Always-on rules | `AGENTS.md`, `.cursor/rules/issues-log.mdc`, `plugins/iris-agent/rules/` | Promotion path, no secrets, no deploy in CI, record defects in `issues.md` |
| Skills | `.agents/skills/*/SKILL.md` (on this machine, not in git) | Databricks and Azure procedures, loaded only when the task matches |
| Hooks | `.cursor/hooks.json` → `plugins/iris-agent/scripts/` | Block force-push of `develop` / `ppe` / `main`, block reading `.env`, format Python with ruff |

The plans that drove the build, in order:

1. [2026-09-27 uv migration](../superpowers/plans/2026-09-27-iris-uv-migration.md) — uv as the only installer.
2. [2026-09-27 CI/CD and shutdown](../superpowers/plans/2026-09-27-iris-cicd-cost-shutdown.md) — test-only CI, gated CD, $10 cap, teardown.
3. [2026-09-30 jobs and serving design](../superpowers/specs/2026-09-30-iris-databricks-jobs-serving-design.md) plus [its plan](../superpowers/plans/2026-09-30-iris-databricks-jobs-serving.md) — one train-then-infer job and one serving endpoint, described in YAML, not deployed as part of that work.

When two docs disagree, trust [codebase-index.md](../codebase-index.md),
[CHANGELOG.md](../../CHANGELOG.md), and
[promote-ppe-prod-and-uae.md](../runbooks/promote-ppe-prod-and-uae.md).
Older pages still say `iris-species-dev` and empty ppe/prod hosts. The
current shape is three targets (`develop`, `ppe`, `prod`) on one workspace
host, with names prefixed by the environment (`develop-iris-species`, and
the same pattern for ppe and prod).

## Which skills to open

Open a skill on the day it is listed. Read `SKILL.md`, then the one
reference file that day's task names. The packs live under `.agents/skills/`
on this machine. They are listed in [agent-index.md](../agent-index.md).

| Skill | Use it to learn |
|---|---|
| `databricks-dabs` | Bundle layout, targets, `validate` versus `deploy`. This is the main productionalisation skill. |
| `databricks-jobs` | The train-then-infer job: task types, `depends_on`, serverless. |
| `databricks-ml-training` | Train, MLflow log, Unity Catalog register, aliases. Notice what this repo left out: feature tables and `spark_udf`. |
| `databricks-model-serving` | Endpoint YAML: CPU, Small, scale-to-zero, pinned version. |
| `databricks-unity-catalog` | `catalog.schema.model`, aliases in place of the old stage names. |
| `mlflow-onboarding` | This project is traditional ML (scikit-learn), not a GenAI app. |
| `azure-devops` | Variable groups, manual CD, the `iris-develop` environment. |
| `azure-databricks` | Only `deployment.md` and the cost and security sections, when a Databricks doc and the repo seem to conflict. |
| Plugin skill `plugins/iris-agent/skills/local-score/SKILL.md` | Score one row from the checked-in model. Free, no workspace. |

`databricks-core` is the parent of the jobs, training, serving, and catalog
skills. Read its CLI and auth section once in week 1, then leave it.
`databricks-docs` and `searching-mlflow-docs` are lookup tools.
`databricks-serverless-migration` does not match this repo: the jobs were
written serverless from the start.

## Week 1 — The production loop and the agent rules

**Day 1. What "done" means here.** Read
[productionalisation/README.md](../productionalisation/README.md) and
[workflows.md](../productionalisation/workflows.md). You should be able to
say the loop in one pass: git, then CI (free), then human-gated CD, then a
train job that registers a Unity Catalog version, then infer or the
endpoint serving that version. The rule the agent was held to is deploy the
training code and refit in each environment. The folder `models/iris_species`
is the copy pytest loads on a laptop.

**Day 2. How the agent was constrained.** Read `AGENTS.md`,
[agent-index.md](../agent-index.md),
[plugins/iris-agent/README.md](../../plugins/iris-agent/README.md), and
[cursor-best-practices.md](cursor-best-practices.md) from "Rules, skills,
and commands" through the hooks section. Trace one hook: `guard_shell.py`
refuses a force-push of `main`. Then read the opening of
[the CI/CD plan](../superpowers/plans/2026-09-27-iris-cicd-cost-shutdown.md)
and notice the line "For agentic workers" plus the global constraints. That
plan was the brief. The skill supplied the Databricks procedure.

**Day 3. Free check.** Run the local score the plugin skill describes, then:

```bash
uv sync --locked --extra dev
uv run pytest -q
```

Open `databricks-dabs` and read `references/bundle-structure.md` beside
`databricks.yml`. Stop at validate. Leave deploy alone.

## Week 2 — Toolchain, CI, and the cost gate

**Day 1. What was built.** Read the
[uv plan](../superpowers/plans/2026-09-27-iris-uv-migration.md), then
`pyproject.toml`,
[folder-structure.md](../productionalisation/folder-structure.md), and
[required-files.md](../productionalisation/required-files.md). uv is the
installer. `uv.lock` is what CI installs. `requirements.txt` is a compiled
copy for Databricks readers.

**Day 2. How CI stays free.** Read `azure-pipelines.yml` and
`tests/test_pipeline_contract.py`. CI runs pytest, ruff, and
`databricks bundle validate`. Validate reads YAML. It does not create
jobs. CD is `azure-pipelines-cd.yml`, manual, and the caller must confirm.
`.github/workflows/ci.yml` and `cd.yml` are disabled. Azure DevOps is the
only pipeline. The rule is `.cursor/rules/azure-devops-only.mdc`.
Open the `azure-devops` skill only for variable groups and environments,
then read [azure-devops.md](azure-devops.md) and
[where-to-put-variables.md](where-to-put-variables.md).

**Day 3. The $10 decision.** Read
[ADR-001](../decisions/ADR-001-develop-only-serving-path.md),
[cost-tracker.md](../cost-tracker.md), and
[teardown-and-restore.md](../teardown-and-restore.md). ADR-001 wanted an
inference table. Later cost work turned payload capture off, because that
table is a bill. [rules.md](../productionalisation/rules.md) items 17–21
are the current rule: serverless only, scale-to-zero on, no deploy until
the tracker is approved. The skill behind the "no forgotten cluster" choice
is `azure-databricks`, in the deployment and cost sections.

## Week 3 — Train, register, serve

**Day 1. The model the jobs call.** Read `src/iris_model/train.py`,
`src/iris_model/score.py`, and `src/iris_model/schema.py`. Then open
`mlflow-onboarding` and confirm this is the traditional-ML path:
experiment, logged metric, pyfunc model. The teaching notebook
`notebooks/01_train_and_register.ipynb` is the same path, cell by cell.

**Day 2. The one job.** Read
`databricks/jobs/iris_ml_job_pipeline.yml`, `notebooks/train_register.py`,
and `notebooks/infer.py` with the `databricks-jobs` skill open at task
types. Train runs, then infer. Infer does not start if train fails. Infer
checks two known flowers, setosa then virginica. Standalone train and infer
jobs were removed from the bundle. Open `databricks-ml-training` and mark
what is absent on purpose: no feature table, no `spark_udf`, no
Champion-versus-Challenger compare job.

**Day 3. The endpoint and the catalog name.** Read
`databricks/artifacts/iris_endpoint.yml` and the three files in
`databricks/targets/` with `databricks-model-serving` and
`databricks-unity-catalog`. The endpoint is CPU, Small, scale-to-zero,
version pinned. It stays out of the job include, because including it made
`bundle deploy` wait on container startup. The Unity Catalog name is
`dbw_iris_ml_dev.<env>.iris_species`. Aliases (`@develop`, `@ppe`, `@prod`,
`Champion`) are how a version is selected. The checked-in
`models/iris_species` folder is a different copy.

## Week 4 — What is real, what is still a sketch

**Day 1. Maturity, in the author's own words.** Read
[eli25-vechtomova-mlops-frameworks.md](eli25-vechtomova-mlops-frameworks.md)
sections 2 through 5. Honest level: local training works (level 0), the
train-then-infer job is declared (level 1, not a proven scheduled run), and
CI/CD is sketched and gated (level 2). Live serving is still below level 1
until an endpoint is healthy. The next Databricks-only slice, in that
page's order, is: one healthy `develop-iris-species` endpoint, a train run
that creates `@develop` and `Champion`, a pin to that version, then
inference tables and monitoring only after the cost sheet lists them.

**Day 2. Promotion without a second workspace.** Read
[promote-ppe-prod-and-uae.md](../runbooks/promote-ppe-prod-and-uae.md) and
[branch-rules.md](../branch-rules.md). Git is `feature/*` → `develop` →
`ppe` → `main`. `main` deploys Databricks target `prod`. All three targets
share one host today. A new region, including UAE, means a new workspace.
Read [token-lifecycle.md](token-lifecycle.md) and
[secrets.md](../secrets.md) for where a PAT is allowed to live. Values stay
in `.env` and in the `iris-develop` variable group.

**Day 3. Repeat the agent's loop on paper.** Pick one small doc fix you
already understand, for example a stale endpoint name. Write the brief the
way the plans do: outcome, files, the check (`uv run pytest -q` and
`uv run ruff check .`), and the stops (no deploy, no secrets). Then read
[cursor-pro-agent-models.md](cursor-pro-agent-models.md) and pick one model
from the Cursor pool for that brief.
[cursor-best-practices.md](cursor-best-practices.md) says a change with
more than one reasonable design starts in Plan mode.

After four weeks you should be able to walk a reviewer through this
sentence: the iris classifier is packaged Python, locked with uv, tested in
CI, described as one serverless train-then-infer job plus one
scale-to-zero endpoint in a Databricks bundle, and held behind a human
`YES` until the $10 tracker is approved.
