# Required files

A production Databricks project is reviewable when these files exist and
agree with each other. "Agree" means the model name in the training job is
the model name in the endpoint, and the environment name in the target is
the catalog schema the job writes.

The first column is the role. The second is the MLOps Stacks name. The
third is the file in this repository.

## Repository contract

| Role | MLOps Stacks | This repo | Required |
|---|---|---|---|
| What the project is and how to run it locally | `README.md` | `README.md` | Yes |
| What changed | — | `CHANGELOG.md` | Yes, once more than one person ships |
| Python project, extras, test and lint config | `pytest.ini`, `requirements.txt` | `pyproject.toml` | Yes |
| Locked install | — | `uv.lock` | Yes. CI uses `uv sync --locked` |
| Pins Databricks and serving can pip-install | `<project>/requirements.txt` | `requirements.txt`, `requirements-serving.txt` | Yes. Databricks does not read `uv.lock` |
| Interpreter pin | — | `.python-version` | Yes |
| Ignore secrets and local state | `.gitignore` | `.gitignore` | Yes |
| Example of secret *names* only | — | `.env.example` | Yes |

Regenerate the compiled requirements when dependencies change:

```bash
uv lock
uv pip compile --universal pyproject.toml -o requirements.txt
```

`requirements-serving.txt` stays smaller than the full lock. The endpoint
and serverless jobs install that file, not the dev extra.

## Model code

| Role | MLOps Stacks | This repo | Required |
|---|---|---|---|
| Training entrypoint | `<project>/training/Train.py` | `src/iris_model/train.py`, `notebooks/train_register.py` | Yes |
| Scoring / batch inference | `<project>/deployment/batch_inference/predict.py` | `src/iris_model/score.py`, `notebooks/infer.py` | Yes |
| Feature contract | `<project>/feature_engineering/` | `src/iris_model/schema.py` | Yes. A Feature Store table is required only when features are shared |
| Input validation before register | `<project>/validation/validation.py` | `notebooks/infer.py` known-row gate, plus pytest | Yes. A separate validation job is the production form |
| Explainability or governance artifact | logged in MLflow | `src/iris_model/narratives.py` (SHAP + plain language) | When a reviewer must see why a score happened |
| Local model for tests | — | `models/iris_species/` (`MLmodel`, `conda.yaml`, `python_env.yaml`) | For this repo's pytest. Not a substitute for Unity Catalog |

Production training code logs parameters, metrics, and the model to MLflow,
then registers into the catalog for the environment that ran the job
(`catalog.schema.model`). Stages (`Staging`, `Production`) are not used on
Unity Catalog. Promotion is an alias move: `Challenger`, then `Champion`,
plus an environment alias such as `@develop`.

## Bundle

| Role | MLOps Stacks | This repo | Required |
|---|---|---|---|
| Bundle root | `<project>/databricks.yml` | `databricks.yml` | Yes. Name, variables, `include` only |
| Experiment and registered model | `resources/ml-artifacts-resource.yml` | variables in `databricks.yml` and each target | Yes |
| Training job | `resources/model-workflow-resource.yml` | `databricks/tasks/train_*.yml` | Yes |
| Multi-task pipeline | same family | `databricks/jobs/iris_ml_job_pipeline.yml` | Yes when train must finish before infer |
| Batch inference job | `resources/batch-inference-workflow-resource.yml` | `databricks/tasks/infer_script.yml` | Yes for batch; optional if you only serve HTTP |
| Feature job | `resources/feature-engineering-workflow-resource.yml` | none | When features leave the training script |
| Monitoring job | `resources/monitoring-resource.yml` | none | When the model takes traffic you will keep |
| Serving endpoint | often a separate resource or CD step | `databricks/artifacts/iris_endpoint.yml` | Yes for real-time scoring |
| One target per environment | `targets:` inside `databricks.yml` | `databricks/targets/{develop,ppe,prod}.yml` | Yes |

Each target file sets the workspace host, `root_path`, catalog model name,
alias, experiment name, and endpoint name. This repo prefixes resources
(`develop-iris-species`, `ppe-iris-species`, `prod-iris-species`) because
all three targets currently share one workspace host.

Variables that must exist on the bundle, with defaults safe to commit:

- environment name and prefix
- Unity Catalog model name (`catalog.schema.model`)
- model alias
- served model version (a pin, not "whatever was last")
- endpoint name
- experiment name
- owner tag

Cluster IDs and tokens are not defaults. Pass a personal-compute id with
`--var` at deploy time. Tokens stay in the CI variable group.

## Tests

| Role | MLOps Stacks | This repo | Required |
|---|---|---|---|
| Training or feature unit tests | `tests/training/`, `tests/feature_engineering/` | `tests/test_score.py`, `tests/test_training_contract.py` | Yes |
| Bundle contract (job names, depends-on, endpoint pin) | — | `tests/test_jobs_contract.py`, `tests/test_pipeline_contract.py` | Yes once YAML is the deploy path |
| Lint config | — | `[tool.ruff]` in `pyproject.toml` | Yes |
| Live serving smoke | — | `scripts/test_serving.py` | Yes, but not inside CI. Dry-run in CD; a real POST is a separate decision |

## CI/CD files

| Role | MLOps Stacks | This repo | Required |
|---|---|---|---|
| Unit tests on pull request | `.github/workflows/<project>-run-tests.yml` | `.github/workflows/ci.yml` | Yes |
| Bundle validation | `.github/workflows/<project>-bundle-ci.yml` | `azure-pipelines.yml` (`bundle validate`) | Yes. GitHub CI here does not validate, because that workflow has no Databricks auth |
| Deploy staging | `<project>-bundle-cd-staging.yml` | `.github/workflows/cd.yml`, `azure-pipelines-cd.yml` | Yes, and it must be manual or environment-protected |
| Deploy production | `<project>-bundle-cd-prod.yml` | same CD files, `target` input | Yes before prod traffic. Here the prod target exists; dispatch waits on cost approval |
| Azure DevOps equivalents | `.azure/devops-pipelines/*-tests-ci.yml`, `*-bundle-cicd.yml` | `azure-pipelines.yml`, `azure-pipelines-cd.yml` | Pick one CI system as the deployer. This repo keeps both definitions and treats Azure as the one that can see the workspace |
| Pull request template | — | `.github/PULL_REQUEST_TEMPLATE.md` | Yes |

MLOps Stacks also generates `docs/mlops-setup.md` for the person who creates
the service principal, variable groups, and pipeline. This repo splits that
across [Azure DevOps](../guides/azure-devops.md), [secrets](../secrets.md),
and [cost tracker](../cost-tracker.md).

## Cloud objects that are not files

These are created in the workspace or the cloud account. Git only names them.

| Object | Example in this repo | Required |
|---|---|---|
| Resource group and workspace | created once, outside the bundle | Yes before any deploy. `bundle deploy` does not create them |
| Unity Catalog catalog and schema | `dbw_iris_ml_dev.develop` (and `.ppe`, `.prod`) | Yes. One schema (or catalog) per environment |
| Registered model | `dbw_iris_ml_dev.<env>.iris_species` | Yes |
| Secret scope | `kv-iris-ml-dev-7405` | Yes. Values live in Key Vault or a variable group |
| Service principal per environment | `iris-develop` variable group | Yes for CD. A user token is only for local `bundle validate` |
| Budget alert | `infra/budget.bicep` | Yes before the first paid deploy |
| Inference table and monitor | not declared | Required once serving stays up. Off here until the cost sheet lists payload GB |

Permissions on the schema, for the CD principal: `USE CATALOG`,
`USE SCHEMA`, `CREATE MODEL`, `CREATE TABLE`, and `MODIFY` on the objects
that principal writes. Data scientists in production get read, not write.

## Files you add only when the use case needs them

- Lakeflow / Delta Live Tables pipeline YAML, if transformation is a pipeline rather than a job task
- Feature spec YAML, if online lookup must ship inside the logged model
- Dashboard JSON, if SQL alerts are the paging path
- `infra/` Bicep or Terraform for the workspace itself, if the platform team does not already own it
- Postman or HTTP fixtures (`docs/postman/`) for a real-time endpoint

Do not add a second orchestrator (Airflow, Prefect, Kubeflow) or a
Kubernetes serving chart when Lakeflow Jobs and Model Serving already cover
the path. That is a different product, not a missing file.
