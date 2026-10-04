# Folder structure

One repository holds the source and the workspace description. Databricks'
developer guidance is: keep every bundle a team owns in that one repo, and
let one bundle cover development, staging, and production. Do not split
environments into three repos.

Official starter: `databricks bundle init mlops-stacks` from
[databricks/mlops-stacks](https://github.com/databricks/mlops-stacks).
The tree below is that template with the `.tmpl` suffix removed. Names in
angle brackets are the project name you type at init.

## What MLOps Stacks generates

```text
.
├── README.md
├── .gitignore
├── test-requirements.txt
├── docs/
│   ├── mlops-setup.md                 # how CI/CD is wired
│   └── ml-pull-request.md             # how to change training code
├── .github/workflows/                 # or .azure/devops-pipelines/ or .gitlab/
│   ├── <project>-run-tests.yml
│   ├── <project>-bundle-ci.yml
│   ├── <project>-bundle-cd-staging.yml
│   └── <project>-bundle-cd-prod.yml
└── <project>/                         # Python package and bundle root
    ├── README.md
    ├── databricks.yml                 # name, includes, targets
    ├── requirements.txt
    ├── pytest.ini
    ├── resources/
    │   ├── README.md
    │   ├── ml-artifacts-resource.yml          # experiment + Unity Catalog model
    │   ├── model-workflow-resource.yml        # training job
    │   ├── feature-engineering-workflow-resource.yml
    │   ├── batch-inference-workflow-resource.yml
    │   └── monitoring-resource.yml
    ├── feature_engineering/
    ├── training/
    │   ├── Train.py
    │   └── TrainWithFeatureStore.py
    ├── validation/
    │   ├── ModelValidation.py
    │   └── validation.py
    ├── deployment/
    │   ├── batch_inference/
    │   └── model_deployment/
    ├── monitoring/
    └── tests/
```

That is the production shape. A teaching project can use shorter names, as
this repo does. It still needs a home for each of those responsibilities.

## Minimum folders, and what belongs in them

| Folder | Required for | Put here | Leave out |
|---|---|---|---|
| `src/<package>/` or `<project>/` | Every project | Importable training, scoring, and schema code. Production jobs call this package. | Notebook experiments, tokens |
| `tests/` | Every project | Unit tests and contract tests that load a saved model or a fixture. They must not train and must not call a live workspace. | Live POST smoke tests that spend money |
| `notebooks/` or `training/` | Exploration, and any job that still runs a notebook | Thin entrypoints. A notebook that only calls the package is fine. | The only copy of the model logic |
| `resources/` or `databricks/` | Every Databricks project | Job, pipeline, model, and endpoint YAML. One complete resource per file. | Python, secrets, a second copy of the notebook |
| Bundle targets (`resources` overrides or `databricks/targets/`) | Every environment you will deploy | `dev` / `staging` / `prod` (here: `develop`, `ppe`, `prod`) with host, catalog, and name prefixes | A target you are not prepared to pay for, unless its host is intentionally unset |
| `.github/workflows/` and/or Azure Pipelines YAML | Every project that merges through git | Test workflow and a separate deploy workflow | A deploy step inside the test workflow |
| `docs/` | Every project someone else will operate | Rules, runbooks, ADRs, cost, secrets *names* | Secret values |
| `infra/` | When the cloud account is yours to create | Budget, resource group, workspace. Created once, outside the bundle. | Job definitions (those stay in the bundle) |
| `models/` or `fixtures/` | Local tests | A small saved model or sample rows so pytest has an input | The production model as the source of truth. Unity Catalog is that shelf |
| `scripts/` | Repeatable operator commands | Teardown, budget, dry-run score | Anything imported by the model |

Feature engineering and monitoring folders are required once the model
reads a shared table or the endpoint takes live traffic. They are optional
while the dataset is a fixed teaching set and monitoring is only a cost cap.

## How this repository is laid out

```text
.
├── README.md
├── CHANGELOG.md
├── pyproject.toml
├── uv.lock
├── requirements.txt              # compiled for Databricks readers
├── requirements-serving.txt      # pins the endpoint and serverless jobs
├── databricks.yml                # bundle root: name, variables, include
├── src/iris_model/               # train, score, schema, narratives
├── notebooks/                    # train_register.py, infer.py, one teaching notebook
├── tests/
├── models/iris_species/          # local MLflow folder for pytest
├── databricks/
│   ├── jobs/                     # multi-task train → infer job
│   ├── tasks/                    # one complete job per file
│   ├── artifacts/                # serving endpoint YAML
│   └── targets/                  # develop.yml, ppe.yml, prod.yml
├── .github/workflows/            # ci.yml (tests), cd.yml (manual deploy)
├── azure-pipelines.yml           # CI including bundle validate
├── azure-pipelines-cd.yml        # manual CD
├── infra/                        # budget.bicep
├── scripts/
└── docs/
```

`databricks.yml` includes jobs, tasks, and targets. The endpoint file stays
under `databricks/artifacts/` and is applied by the gated CD path. Putting
it in the bundle include made `bundle deploy` wait on container startup and
blocked the job run. That split is intentional.

Notebooks stay in `notebooks/`. The bundle points at them. It does not copy
them under `databricks/`.

A Databricks Asset Bundle cannot split one job key across files. Each file
under `databricks/tasks/` is a whole job. The chained pipeline is its own
file under `databricks/jobs/`.

## Deploy location

Databricks recommends deploying a bundle to a folder the team owns, with
`CAN_MANAGE` only for that team, rather than `/Workspace/Shared`. This
repo's targets still use:

```text
/Shared/.bundle/${bundle.name}/${bundle.target}
```

That is acceptable for a single-learner workspace. A shared production
workspace should move `root_path` off `/Shared` before a second team can
see the bundle. See
[developer best practices](https://docs.databricks.com/aws/en/developers/best-practices).

## What never goes in the tree

Ignored on purpose (see `.gitignore`):

- `.env` and any token, pem, or key
- `.venv/`, `__pycache__/`, `.pytest_cache/`
- `mlruns/` and `mlartifacts/` (local MLflow tracking)
- `.databricks/`, `.azure/`, Terraform state

Unity Catalog tables, experiments, and served endpoints are workspace
objects. Git stores the YAML that creates them, not the rows.
