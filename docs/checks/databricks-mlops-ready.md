# Databricks MLOps ready

How far this repo is along Databricks MLOps: a bundle, Unity Catalog, one job, serverless serving, and gated delivery. Percentages are completeness of that step on 4 October 2026. **Overall** is the mean of the Progress column, rounded to the nearest percent.

Overall: 58%

| Step | Progress | Now |
|---|---|---|
| Bundle and three targets | 90% | `databricks.yml` plus `develop`, `ppe`, and `prod`. They share one workspace host. |
| Unity Catalog names | 85% | `dbw_iris_ml_dev.<env>.iris_species` with aliases `@develop`, `@ppe`, `@prod`, and `Champion`. |
| One train-then-infer job | 90% | `iris-ml-job-pipeline` is the only iris job in the bundle. Infer depends on train. |
| Serverless compute | 85% | The job environment installs `requirements-serving.txt`. No all-purpose cluster. |
| Alias-based HTTP version | 85% | `scripts/apply_served_version.py` reads the alias and creates or updates the endpoint. |
| CI bundle validate | 95% | Azure CI runs `databricks bundle validate` for all three targets. CI does not deploy. |
| Gated CD | 70% | GitHub `workflow_dispatch` and Azure `trigger: none`, confirm `YES`, branch must match the target. |
| Scale-to-zero CPU serving | 80% | Small CPU, scale-to-zero on. A live POST is what warms it. |
| Separate principals | 75% | Develop, ppe, and prod CD each require their own client id and secret. The apps are not provisioned yet. |
| Separate workspaces | 20% | One host. A second region would be a new workspace. |
| Feature tables | 10% | Training still calls `load_iris`. |
| Inference tables and monitoring | 15% | Capture is off. Lakehouse Monitoring is not created. |
| Schedule or trigger | 15% | The pipeline runs when CD or a person starts it. |
| Bundle path off `/Shared` | 30% | Open [ISS-020](../../issues.md). The deploy path is writable by every workspace user. |
| Budget alerts applied | 20% | `infra/budget.bicep` exists. The tracker snapshot still says the budget is not created. |

## What this score is not

58% means the Databricks shape is in git and the dangerous parts are gated. It does not mean ppe and prod are signed off, and it does not mean the endpoint is warm.

When to use a gateway, a Unity Catalog model, or an endpoint: [AI Gateway, models, and serving](../guides/ai-gateway-models-and-serving.md).
