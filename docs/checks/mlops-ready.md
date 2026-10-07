# MLOps ready

How far this repo is along a normal MLOps loop: code, train, track, evaluate, deploy, serve, watch, retrain. Percentages are completeness of that step on 4 October 2026. **Overall** is the mean of the Progress column, rounded to the nearest percent.

Overall: 68%

| Step | Progress | Now |
|---|---|---|
| Source control and CI | 90% | Feature branches, test-only GitHub and Azure CI, ruff, pytest. Pre-commit secret gates are on `feature/fix-azure-cd`, not on `develop` yet. |
| Reproducible training | 85% | `uv.lock`, `notebooks/train_register.py`, and `requirements-serving.txt`. The dataset is still `load_iris`, not a feature table. |
| MLflow tracking | 90% | One run logs estimator params, holdout metrics, the training dataset, a signature, one input example, a confusion matrix, feature importance, git SHA when the job has one, and a single holdout span. System-metric polling stays off so the task stays short. |
| Registry and aliases | 85% | Train sets the env alias and `Champion`, plus version tags. A live version exists only after the job runs. |
| Evaluation gate | 55% | Infer fails the job when the two known rows are not setosa then virginica. There is no Challenger-versus-Champion compare. |
| Deploy gate | 70% | CD is manual and must be confirmed. `docs/cost-tracker.md` is still proposed, and the budget alerts are not applied. |
| Served version | 85% | After the train job, CD creates the endpoint or moves it to the alias version. It does not keep the first version forever, and it does not follow "latest". |
| Deploy identity | 75% | CD requires a service principal per environment and unsets a personal token. The Azure applications and the secret values are not created by the repo. |
| Monitoring | 25% | The $10 cap is written down. Inference capture and Lakehouse Monitoring are off. |
| Retrain | 20% | Someone starts the job. There is no schedule and no metric trigger. |

## What "ready" would still require

1. Approve the cost sheet and create the budget.
2. Create the three service principals and store only their names in git.
3. Add a Challenger check before `Champion` moves.
4. Turn on inference capture only after the cost sheet lists payload GB.
5. Schedule retrain only after that monitor exists.

The Databricks-specific list is [databricks-mlops-ready.md](databricks-mlops-ready.md). The document list is [productionalisation-ready.md](productionalisation-ready.md).
