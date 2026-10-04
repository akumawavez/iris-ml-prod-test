# Codebase index

Map of this repository. Guides are listed in
[guides/README.md](guides/README.md). Agent hooks, the plugin, and local
skill packs are listed in [agent-index.md](agent-index.md).

Promotion is `feature/*` → `develop` → `ppe` → `main`. `main` deploys
Databricks target `prod`. CI tests. CD is manual and stays closed until
[cost-tracker.md](cost-tracker.md) is approved.

```text
.
├── README.md, AGENTS.md, CHANGELOG.md, issues.md
├── pyproject.toml, uv.lock, requirements.txt, requirements-serving.txt
├── databricks.yml
├── src/iris_model/          train, score, schema, narratives
├── notebooks/               train and infer entrypoints, one teaching notebook
├── tests/                   score, job, pipeline, and hook contracts
├── models/iris_species/     saved MLflow model pytest loads
├── databricks/              one job, endpoint artifact, three targets
├── .github/workflows/       disabled GitHub Actions
├── azure-pipelines.yml      the only CI
├── azure-pipelines-cd.yml   the only CD, manual
├── infra/budget.bicep       $10 budget, applied only by a confirmed script
├── scripts/                 budget, teardown, dry-run score
├── docs/                    rules, guides, runbooks, plans
└── plugins/iris-agent/      Cursor hooks, rules, review agent
```

Git does not store `.env`, `.venv/`, `.agents/`, `*.egg-info/`, or local
MLflow tracking. Names of variables live in `.env.example`.

## Root

| File | Role |
|---|---|
| [README.md](../README.md) | What the classifier does, the local score command, links onward |
| [AGENTS.md](../AGENTS.md) | Agent notes: checks and hard stops |
| [CHANGELOG.md](../CHANGELOG.md) | Shipped changes, newest first |
| [issues.md](../issues.md) | Defect log |
| [pyproject.toml](../pyproject.toml) | Package `iris_model`, Python `>=3.12`, ruff, pytest |
| [.python-version](../.python-version) | Python 3.13 for uv |
| [uv.lock](../uv.lock) | Locked install. CI uses this, not pip |
| [requirements.txt](../requirements.txt) | Compiled lock output for Databricks and Azure ML readers |
| [requirements-serving.txt](../requirements-serving.txt) | Pins for the endpoint and serverless jobs |
| [.env.example](../.env.example) | Variable names only |
| [.gitignore](../.gitignore) | Secrets, virtualenv, `.agents/`, local MLflow |
| [.pre-commit-config.yaml](../.pre-commit-config.yaml) | Ruff and the repo hooks |
| [databricks.yml](../databricks.yml) | Bundle name, variables, and includes |

## Model code

| File | Role |
|---|---|
| [src/iris_model/train.py](../src/iris_model/train.py) | Fit one random forest on `load_iris` and save `models/iris_species` |
| [src/iris_model/score.py](../src/iris_model/score.py) | Load that model and return the prediction plus SHAP and importance narratives |
| [src/iris_model/schema.py](../src/iris_model/schema.py) | Four feature names, three species, row validation |
| [src/iris_model/narratives.py](../src/iris_model/narratives.py) | Calculation text and plain-language text for one flower |
| [src/iris_model/_version.py](../src/iris_model/_version.py) | Package version |
| [src/iris_model/__init__.py](../src/iris_model/__init__.py) | Package marker |

## Notebooks and the saved model

| File | Role |
|---|---|
| [notebooks/train_register.py](../notebooks/train_register.py) | Databricks train task. Fits, logs, and registers when asked |
| [notebooks/infer.py](../notebooks/infer.py) | Batch score of known rows, local path or a Unity Catalog URI |
| [notebooks/01_train_and_register.ipynb](../notebooks/01_train_and_register.ipynb) | Same train path, cell by cell |
| [models/iris_species/](../models/iris_species/) | Checked-in MLflow pyfunc (`MLmodel`, `python_model.pkl`, forest artifact, env files). Pytest loads it and does not train |

## Bundle

| File | Role |
|---|---|
| [databricks/jobs/iris_ml_job_pipeline.yml](../databricks/jobs/iris_ml_job_pipeline.yml) | One serverless job: train, then infer. Name `${env_prefix}-iris-ml-job-pipeline` |
| [databricks/artifacts/iris_endpoint.yml](../databricks/artifacts/iris_endpoint.yml) | Serving endpoint `${endpoint_name}`. Applied by gated CD, not by the job include |
| [databricks/targets/develop.yml](../databricks/targets/develop.yml) | Default target. Catalog schema `develop`, endpoint `develop-iris-species` |
| [databricks/targets/ppe.yml](../databricks/targets/ppe.yml) | PPE target on the same workspace host |
| [databricks/targets/prod.yml](../databricks/targets/prod.yml) | Prod target. Git branch `main` selects env `prod` |

All three targets share `https://adb-7405619226406985.5.azuredatabricks.net`
and write under `/Shared/.bundle/iris-ml-prod-test/<target>`.

## Tests

| File | Role |
|---|---|
| [tests/test_score.py](../tests/test_score.py) | Saved model returns input, species, and both narratives. Bad rows fail |
| [tests/test_training_contract.py](../tests/test_training_contract.py) | Registered model runtime requirements stay Linux-compatible |
| [tests/test_jobs_contract.py](../tests/test_jobs_contract.py) | Only the train-infer pipeline is deployed. Aliases, targets, and notebook parity |
| [tests/test_pipeline_contract.py](../tests/test_pipeline_contract.py) | CI does not deploy. CD is manual. Cost cap and teardown script stay guarded |
| [tests/test_agent_hooks.py](../tests/test_agent_hooks.py) | Force-push, `--no-verify`, and secret-file guards |

## Pipelines and cloud

| File | Role |
|---|---|
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | Disabled. GitHub Actions does not run CI |
| [.github/workflows/cd.yml](../.github/workflows/cd.yml) | Disabled. GitHub Actions does not deploy |
| [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md) | Merge checklist |
| [azure-pipelines.yml](../azure-pipelines.yml) | Azure DevOps CI, including bundle validate |
| [azure-pipelines-cd.yml](../azure-pipelines-cd.yml) | Azure DevOps CD. `trigger: none`. Deploy stages follow the branch |
| [infra/budget.bicep](../infra/budget.bicep) | Resource-group budget at $10, with mail at 50%, 80%, and 100% |
| [scripts/setup_budget.ps1](../scripts/setup_budget.ps1) | Applies the budget only with `-Confirm` after the tracker is approved |
| [scripts/cost_snapshot.ps1](../scripts/cost_snapshot.ps1) | Writes the cost snapshot block |
| [scripts/teardown_dev.ps1](../scripts/teardown_dev.ps1) | Shutdown path back to $0 |
| [scripts/test_cd_pipeline.ps1](../scripts/test_cd_pipeline.ps1) | Checks the CD definition |
| [scripts/test_serving.py](../scripts/test_serving.py) | Dry-run by default. `--live` POSTs and can wake a scale-to-zero endpoint |
| [docs/postman/iris-dev.postman_collection.json](postman/iris-dev.postman_collection.json) | Two scored requests for the develop endpoint |
| [docs/postman/iris-dev.postman_environment.json](postman/iris-dev.postman_environment.json) | Postman environment names for that collection |
| [docs/cost-dashboard.html](cost-dashboard.html) | Calculator next to the cost tracker |

## Docs, agents, and the plugin

| Path | Role |
|---|---|
| [docs/guides/](guides/README.md) | ELI25 walkthroughs and how-to guides. Index on that folder's README |
| [docs/productionalisation/](productionalisation/README.md) | Checklist: folders, required files, workflows, rules |
| [docs/runbooks/](runbooks/promote-ppe-prod-and-uae.md) | Promotion runbook |
| [docs/decisions/](decisions/ADR-001-develop-only-serving-path.md) | ADR-001 |
| [docs/superpowers/](superpowers/plans/2026-09-30-iris-databricks-jobs-serving.md) | Implementation plans and the jobs design spec |
| [docs/agent-index.md](agent-index.md) | Hooks, plugin, rules, and local `.agents/skills/` packs |
| [plugins/iris-agent/](../plugins/iris-agent/README.md) | Review agent, check command, local-score skill, hook scripts |
| [.cursor/hooks.json](../.cursor/hooks.json) | Project hook manifest |
| [.cursor-plugin/marketplace.json](../.cursor-plugin/marketplace.json) | Marketplace entry for the plugin |
