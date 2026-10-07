# Runbook: ppe, prod, and later hosts

Git promotion is `feature/*` → `develop` → `ppe` → `main`. `main` is the prod
branch. develop, ppe, and prod are the Databricks Asset Bundle targets. They
share one workspace host today. Resource names end with the environment
(`env_suffix`) so they do not collide.

## Current names

| Git branch | Target | Job | Endpoint | UC model | Aliases |
|---|---|---|---|---|---|
| `develop` | develop | `iris-ml-train-develop`, then `iris-ml-infer-develop` | `iris-species-develop` | `dbw_iris_ml_dev.develop.iris_species` | `@develop` from train. `@Champion` only if the manual run says YES |
| `ppe` | ppe | `iris-ml-train-ppe`, then `iris-ml-infer-ppe` | `iris-species-ppe` | `dbw_iris_ml_dev.ppe.iris_species` | `@ppe` from train. `@Champion` only if the manual run says YES |
| `main` | prod | `iris-ml-train-prod`, then `iris-ml-infer-prod` | `iris-species-prod` | `dbw_iris_ml_dev.prod.iris_species` | `@prod` from train. `@Champion` only if the manual run says YES |

Those jobs start only when the manual CD `runMode` is `train-and-serve`.
The default `serve` deploys the bundle and points the endpoint. It does not
start a serverless job.

Validate (safe):

```bash
databricks bundle validate -t develop
databricks bundle validate -t ppe
databricks bundle validate -t prod
```

Deploy is paid and gated (`azure-pipelines-cd.yml` only). GitHub Actions is disabled.
Do not deploy ppe or prod until you accept a second and third scale-to-zero
endpoint on the cost sheet.

## Point ppe or prod at its own Databricks host later

1. In `databricks/targets/ppe.yml` (or `prod.yml`), replace the `workspace.host`
   URL with the new workspace.
2. Keep `env_suffix`, model schema, alias, and endpoint name as they are.
3. Open a pull request into `develop`. Merge, promote `develop` → `ppe` → `main`, then run gated CD for that target from its git branch.

## Enable ppe in the shared workspace

1. Confirm develop predictions look right.
2. Approve the extra endpoint on `docs/cost-sheet.md`.
3. Run gated CD with target `ppe` (Azure environment `iris-ppe`, GitHub
   environment `ppe`).
4. Train/register sets `@ppe` and `Champion` on `dbw_iris_ml_dev.ppe.iris_species`.
5. Score `iris-species-ppe` with `scripts/test_serving.py --dry-run` first.

## Enable prod the same way

Promote `ppe` into `main` first. `main` is the prod git branch. Repeat with
target `prod`, environment `iris-prod` / `prod`, endpoint `iris-species-prod`,
and run CD from `main`. Prod stays scale-to-zero until you explicitly accept an
always-on bill.

## Rollback

Redeploy the previous bundle commit to the same target:

```bash
git checkout <previous-good-commit>
databricks bundle deploy -t <develop|ppe|prod>
```

Then return to the branch you were on. Do not fix a bad deploy only in the UI.
