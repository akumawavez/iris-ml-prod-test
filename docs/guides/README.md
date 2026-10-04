# Markdown index

Every Markdown file in this repository, grouped by the job it does.
[markdown-catalog.md](../productionalisation/markdown-catalog.md) is the
checklist of pages a production project should have. This page is the map of
the pages that exist.

Agent files are indexed in [agent-index.md](../agent-index.md). The rest of
the tree is in [codebase-index.md](../codebase-index.md).

## Guides

Plain-language walkthroughs (ELI25) and the how-to pages operators follow.

| Page | What it answers |
|---|---|
| [eli25-mlops-lifecycle.md](eli25-mlops-lifecycle.md) | Train, register, serve, and monitor as separate objects |
| [eli25-vechtomova-mlops-frameworks.md](eli25-vechtomova-mlops-frameworks.md) | Which textbook MLOps pieces are in git, and which are still later |
| [eli25-databricks-productionalisation.md](eli25-databricks-productionalisation.md) | This model's names, the $10 cap, and what not to run while reading |
| [eli25-jobs-and-serving.md](eli25-jobs-and-serving.md) | The job and endpoint strings the YAML and the runbooks share |
| [where-to-put-variables.md](where-to-put-variables.md) | Key Vault, bundle vars, compute env, job params, or CI secrets |
| [token-lifecycle.md](token-lifecycle.md) | Create, rotate, and delete PATs and CI secrets |
| [databricks-asset-bundles.md](databricks-asset-bundles.md) | Validate versus deploy, and what the bundle YAML owns |
| [azure-devops.md](azure-devops.md) | Variable groups, environments, and which pipeline may deploy |
| [productionalisation-study-plan.md](productionalisation-study-plan.md) | Four weeks, three days a week, through what agentic coding productionalised and which skill to open |
| [cursor-best-practices.md](cursor-best-practices.md) | How to work in Cursor on this repo |
| [cursor-pro-agent-models.md](cursor-pro-agent-models.md) | Which Cursor Pro models fit agentic work here |

## Start here

| Page | What it answers |
|---|---|
| [README.md](../../README.md) | What the project predicts, how to score locally, where deploy is documented |
| [AGENTS.md](../../AGENTS.md) | Branch path, checks, and what an agent must not do |
| [CHANGELOG.md](../../CHANGELOG.md) | What shipped, newest first |
| [progress.md](../progress.md) | What is done, by date, newest day first |
| [issues.md](../../issues.md) | Defects, newest first. Open and Fixed |

## Rules, secrets, and decisions

| Page | What it answers |
|---|---|
| [branch-rules.md](../branch-rules.md) | `feature/*` → `develop` → `ppe` → `main` |
| [secrets.md](../secrets.md) | Secret names, scopes, and where values live |
| [ADR-001](../decisions/ADR-001-develop-only-serving-path.md) | Develop-only serving path, and why `main` still deploys target `prod` |

## Cost and operations

| Page | What it answers |
|---|---|
| [cost-sheet.md](../cost-sheet.md) | Line items before anything is created |
| [cost-tracker.md](../cost-tracker.md) | $10 cap, alerts, and the signed approval. Status is still proposed |
| [teardown-and-restore.md](../teardown-and-restore.md) | Shutdown order and how to come back |
| [serving-inference-test.md](../serving-inference-test.md) | The POST that proves an endpoint, and the dry-run that does not spend |
| [promote-ppe-prod-and-uae.md](../runbooks/promote-ppe-prod-and-uae.md) | How an environment goes from this host toward ppe, prod, and UAE |

## Production checklist

| Page | What it answers |
|---|---|
| [Productionalisation index](../productionalisation/README.md) | Folders, files, workflows, rules, and this markdown set |
| [folder-structure.md](../productionalisation/folder-structure.md) | MLOps Stacks shape, and how this repo is laid out |
| [required-files.md](../productionalisation/required-files.md) | Files a reviewer expects before a deploy |
| [workflows.md](../productionalisation/workflows.md) | Train, validate, register, deploy, serve, monitor |
| [rules.md](../productionalisation/rules.md) | Branches, secrets, catalogs, cost, and UI clicks to avoid |
| [markdown-catalog.md](../productionalisation/markdown-catalog.md) | The document set a production project needs |

## Plans and the pull request template

| Page | What it answers |
|---|---|
| [2026-09-27 uv migration](../superpowers/plans/2026-09-27-iris-uv-migration.md) | Plan for the uv install path |
| [2026-09-27 CI/CD and shutdown](../superpowers/plans/2026-09-27-iris-cicd-cost-shutdown.md) | Plan for test-only CI, gated CD, and zero-spend shutdown |
| [2026-09-30 jobs and serving](../superpowers/plans/2026-09-30-iris-databricks-jobs-serving.md) | Implementation plan for the train-then-infer job |
| [2026-09-30 design spec](../superpowers/specs/2026-09-30-iris-databricks-jobs-serving-design.md) | Design for that job and the develop serving path |
| [PULL_REQUEST_TEMPLATE.md](../../.github/PULL_REQUEST_TEMPLATE.md) | Merge checklist: target branch, no secrets, no surprise resources |

## Agent Markdown

These pages tell Cursor what to do. The full agent tree, including hooks and
scripts, is [agent-index.md](../agent-index.md).

| Page | What it answers |
|---|---|
| [plugins/iris-agent/README.md](../../plugins/iris-agent/README.md) | What the Iris MLOps plugin installs |
| [mlops-reviewer.md](../../plugins/iris-agent/agents/mlops-reviewer.md) | Review checklist before a pull request |
| [check.md](../../plugins/iris-agent/commands/check.md) | Pytest, ruff, and pre-commit, with no deploy |
| [local-score/SKILL.md](../../plugins/iris-agent/skills/local-score/SKILL.md) | Score one local row from `models/iris_species` |
| [branch-and-secrets.mdc](../../plugins/iris-agent/rules/branch-and-secrets.mdc) | Always-on branch and secret rule |
| [azure-devops-only.mdc](../../.cursor/rules/azure-devops-only.mdc) | Always on. CI and CD run only in Azure DevOps. GitHub Actions stays disabled |
| [python-style.mdc](../../plugins/iris-agent/rules/python-style.mdc) | Ruff settings for Python edits |
| [issues-log.mdc](../../.cursor/rules/issues-log.mdc) | When to add or move a row in `issues.md` |
| [progress-log.mdc](../../.cursor/rules/progress-log.mdc) | When to add a dated bullet in `docs/progress.md` |
