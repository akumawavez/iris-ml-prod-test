# Runbook: ppe, prod, and later hosts

Git promotion is `feature/*` → `develop` → `ppe` → `main`. `main` is the prod
branch. develop, ppe, and prod are the Databricks Asset Bundle targets. They
share one workspace host today. Resource names, tags, and Unity Catalog aliases
are prefixed by environment so they do not collide.

## Current names

| Git branch | Target | Job prefix | Endpoint | UC model | Aliases |
|---|---|---|---|---|---|
| `develop` | develop | `develop-iris-*` | `develop-iris-species` | `dbw_iris_ml_dev.develop.iris_species` | `@develop`, `Champion` |
| `ppe` | ppe | `ppe-iris-*` | `ppe-iris-species` | `dbw_iris_ml_dev.ppe.iris_species` | `@ppe`, `Champion` |
| `main` | prod | `prod-iris-*` | `prod-iris-species` | `dbw_iris_ml_dev.prod.iris_species` | `@prod`, `Champion` |

Validate (safe):

```bash
databricks bundle validate -t develop
databricks bundle validate -t ppe
databricks bundle validate -t prod
```

Deploy is paid and gated (`azure-pipelines-cd.yml`, `.github/workflows/cd.yml`).
Do not deploy ppe or prod until you accept a second and third scale-to-zero
endpoint on the cost sheet.

## Point ppe or prod at its own Databricks host later

1. In `databricks/targets/ppe.yml` (or `prod.yml`), replace the `workspace.host`
   URL with the new workspace.
2. Keep `env_prefix`, model schema, alias, and endpoint name as they are.
3. Open a pull request into `develop`. Merge, promote `develop` → `ppe` → `main`, then run gated CD for that target from its git branch.

## Enable ppe in the shared workspace

1. Confirm develop predictions look right.
2. Approve the extra endpoint on `docs/cost-sheet.md`.
3. Run gated CD with target `ppe` (Azure environment `iris-ppe`, GitHub
   environment `ppe`).
4. Train/register sets `@ppe` and `Champion` on `dbw_iris_ml_dev.ppe.iris_species`.
5. Score `ppe-iris-species` with `scripts/test_serving.py --dry-run` first.

## Enable prod the same way

Promote `ppe` into `main` first. `main` is the prod git branch. Repeat with
target `prod`, environment `iris-prod` / `prod`, endpoint `prod-iris-species`,
and run CD from `main`. Prod stays scale-to-zero until you explicitly accept an
always-on bill.

## Rollback

Redeploy the previous bundle commit to the same target:

```bash
git checkout <previous-good-commit>
databricks bundle deploy -t <develop|ppe|prod>
```

Then return to the branch you were on. Do not fix a bad deploy only in the UI.
