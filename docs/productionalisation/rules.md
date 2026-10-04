# Rules

These are the rules a Databricks or data science project needs before the
first paid deploy. This repository already follows the ones marked
**here**. The rest are the production bar from
[MLOps workflows](https://docs.databricks.com/aws/en/machine-learning/mlops/mlops-workflow),
[developer best practices](https://docs.databricks.com/aws/en/developers/best-practices),
and [Models in Unity Catalog](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/).

Branch specifics for this repo stay in [branch-rules.md](../branch-rules.md).
The cost decision stays in [ADR-001](../decisions/ADR-001-develop-only-serving-path.md).

## Source control

1. **here.** Work on `feature/<short-name>` cut from `develop`. `develop` is the integration branch. `ppe` and `prod` are promotion targets.
2. **here.** Changes reach `develop`, `ppe`, and `prod` only through a pull request. Do not force-push those branches.
3. One repo for the code and the bundle. One bundle covers every environment of that project. Do not make a bundle per environment.
4. Keep the bundle small: one team, one release cadence. A second product gets a second bundle, still in the same repo if the same people own it.
5. Review YAML the same way as Python. A job schedule or an endpoint size is a production change.

## Secrets

6. **here.** No tokens, connection strings, or personal access tokens in git, YAML, docs, or chat. Commit scope names and variable-group names only.
7. **here.** Local values live in `.env` (gitignored). CI reads `DATABRICKS_HOST` and `DATABRICKS_TOKEN` from the `iris-develop` variable group. Workspace code reads Key Vault scope `kv-iris-ml-dev-7405`.
8. CD uses a service principal. A developer token is for `bundle validate` on a laptop, not for the pipeline that deploys prod.
9. Give staging and prod different principals when they share a workspace, so a staging job cannot edit the prod endpoint.

## Data and Unity Catalog

10. Tables are Delta in Unity Catalog, not files on a laptop and not the hive metastore. Raw and features get grants, not world-read.
11. Each environment has its own catalog or schema. This repo uses one catalog, `dbw_iris_ml_dev`, and schemas `develop`, `ppe`, and `prod`.
12. Register with the three-level name `catalog.schema.model`. Do not use Workspace Model Registry stages. They do not exist for Unity Catalog models.
13. Promote with aliases. `Challenger` means "passed validation." `Champion` means "this is what batch and, when you choose, serving load." Environment aliases (`@develop`, `@ppe`, `@prod`) say which version that environment trained.
14. **here.** The HTTP endpoint pins `entity_version`. It does not follow "latest" by accident. Moving the pin is a reviewed YAML change, and the version must already exist.
15. Data scientists can read production models, inference logs, and metric tables. They do not get write or compute in prod unless they are the on-call deployers.
16. **Deploy the training code into each environment and refit there.** Copying a model binary across catalogs is an exception that needs a written reason.

## Compute and cost

17. **here.** No all-purpose cluster and no SQL warehouse in the bundle. Forgotten clusters are the usual surprise bill. Serverless jobs and serverless CPU serving are the path.
18. **here.** Scale-to-zero stays on. A warm Small CPU endpoint is about 4 DBU per hour (1 DBU per hour per concurrent slot, Small allows 4). Idle is ~$0 per hour. A live request resets the idle timer.
19. **here.** Do not deploy, run a job, or POST the endpoint until [cost-tracker.md](../cost-tracker.md) is approved. The cap on this project is $10 per month.
20. **here.** `databricks bundle validate` is free. `databricks bundle deploy` and `databricks bundle run` are not.
21. Inference-table capture and Lakehouse Monitoring are production requirements, and they are also billable. Turn them on only after the cost sheet lists payload GB and monitor DBU.
22. A new Azure region means a new workspace. You cannot edit the region of an existing one.
23. Tag every job and endpoint (`project`, `env`, `owner`, `managed-by`) so the bill can be tied to the YAML.

## Jobs and serving

24. Production tasks are Python files on a job (`spark_python_task` or a notebook that only calls the package). The notebook is not the only copy of the logic.
25. **here.** One job definition is one file. Do not split a job key across includes.
26. Infer depends on train. A failed train does not score.
27. The served model and the batch model document which alias or version they load. Those two are allowed to differ during a canary. They are not allowed to differ because nobody updated one of them.
28. One endpoint per environment. Names include the environment (`develop-iris-species`) when environments share a workspace.
29. Job notifications go to a channel a human reads when validation fails. Silent failure is not a workflow.

## Code and tests

30. **here.** Tests load the saved model or a fixture. They do not call `train` and they do not need a workspace.
31. **here.** `uv.lock` is committed. CI fails if the lock is stale. `requirements.txt` is the compiled file Databricks installs.
32. The feature list is a schema in code (`src/iris_model/schema.py`). Training and scoring both import it. A new column is a contract change, not a silent extra.
33. Log the git SHA on the MLflow run (`code_version` or the bundle's own commit tag) so a served version can be traced to a pull request.
34. Dependencies of the served model are pinned in `requirements-serving.txt`. Do not install the dev extra on the endpoint.

## CI behaviour

35. **here.** CI does not deploy. CD does not run on push.
36. **here.** Docs-only changes do not start a test run.
37. **here.** Superseded CI runs on the same ref are cancelled. There is no cron on CI.
38. Required checks, once the host can enforce them: pytest, ruff, and bundle validate. Branch protection on a private GitHub Free repo cannot enforce this; the team still treats a red check as "do not merge."

## Documentation

39. A behaviour change updates the guide or the ADR in the same pull request. The checklist is in the [pull request template](../../.github/PULL_REQUEST_TEMPLATE.md).
40. An architecture choice that is expensive to reverse (one workspace versus three, pin versus alias, inference tables on or off) is an ADR under `docs/decisions/`.
41. Runbooks are commands in order, including the rollback. They are not a design discussion.

## What this project refuses even if a template includes it

- A second orchestrator beside Lakeflow Jobs
- Kubernetes or a separate FastAPI service for this model
- Poetry or a second lockfile beside uv
- Terraform for the workspace while the budget is a single Bicep file and the resources are a bundle
- A GPU or an always-on cluster for a 150-row CPU model
- Filling a prod host "to see if validate works" before the cost approval
