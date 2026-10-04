# Teardown and restore — spend $0 while keeping a path back

Goal: no cost incurred, with everything needed to recreate the setup checked
in or exported first. Order matters: **backup → stop → disable → (only if
asked) delete**. Deletion is the last resort, never the first step.

> Nothing on this page runs by itself. The script version
> (`scripts/teardown_dev.ps1`) refuses to run without `-Confirm`, stops and
> disables by default, and needs a second flag (`-IncludeDelete`) to delete
> anything. Deleting the resource group is irreversible — the backup step
> exists so recreation is copy-paste.

## 0. What "off" means (disable-first, delete-last)

| Level | Off state | Spend after |
|---|---|---|
| Endpoint `iris-species-dev` | Stopped (or scales to zero, then stopped) | $0 DBU |
| Pipelines (AzDO + GitHub) | Disabled, CD never created | $0 minutes |
| Workspace `dbw-iris-ml-dev` | No running compute | $0 (no base fee) |
| Resource group `rg-iris-ml-dev` | Deleted — **only with `-IncludeDelete`** | $0 |

Stopping + disabling is enough for $0. Delete the resource group only if you
want the subscription to forget the workspace entirely.

## 1. Backup first (recreate from this)

1. Endpoint config (needs a live workspace; skip if already deleted):
   ```powershell
   databricks serving-endpoints get iris-species-dev | Out-File backup/iris-species-dev.json
   ```
2. Confirm the recipe is in git (it is, on `develop`):
   - `databricks.yml` + `databricks/artifacts/iris_endpoint.yml` — bundle description
   - `infra/budget.bicep` — the $10 budget definition
   - `models/iris_species/` — the committed MLflow model (no re-train needed)
   - Unity Catalog lineage: catalog `iris_ml`, schema `develop`, model
     `iris_species` — re-created by `scripts/setup_unity_catalog.sql` notes.
3. Copy the last `docs/cost-tracker.md` snapshot block into the restore PR.

`scripts/teardown_dev.ps1 -Confirm` does step 1 automatically into
`backup/<date>/` before it stops anything.

## 2. Stop the endpoint (spend → $0 DBU)

Portal: Databricks workspace → Serving → `iris-species-dev` → Stop.
CLI: `databricks serving-endpoints delete iris-species-dev`
(serving has no "pause"; delete is the stop — the bundle recreates it).
Scale-to-zero alone is $0/hour only while nobody calls it; deleting is the
certain $0. Either way, run a final `./scripts/cost_snapshot.ps1` 30 min later
to confirm burn stops.

## 3. Disable the pipelines (spend → $0 minutes)

- Azure DevOps: Pipelines → `iris-ml-prod-test-ci` → ⋯ → **Disable**.
  Do NOT create `azure-pipelines-cd.yml` as a pipeline (it is `trigger: none`
  by design; leaving it uncreated is the disabled state).
- GitHub Actions is already disabled in git. Leave `.github/workflows/ci.yml`
  and `cd.yml` that way (`if: false` on every job). Do not turn them back on.

## 4. Delete the resource group (optional, irreversible)

Only when steps 1–3 are done AND you pass a second explicit flag:

```powershell
./scripts/teardown_dev.ps1 -ResourceGroup rg-iris-ml-dev -Confirm -IncludeDelete
```

Portal equivalent: Resource groups → `rg-iris-ml-dev` → Delete resource group
(type the name to confirm). Key Vault has soft-delete + purge protection notes
in `docs/secrets.md` — purging a vault is a separate portal action.

## 5. Verify $0

1. `az consumption usage list -g rg-iris-ml-dev` → empty (or resource group gone).
2. `docs/cost-tracker.md` snapshot block stamped `$0.00` via
   `./scripts/cost_snapshot.ps1 -ResourceGroup rg-iris-ml-dev -UpdateTracker`.
3. Azure portal → Cost Management → no new DBU rows after 24 h (ingestion lag).

## 6. Restore (reverse order)

1. Re-run the gated setup: `scripts/setup_azure.ps1 -Confirm` (needs fresh
   cost approval), then `scripts/setup_budget.ps1 -Confirm`.
2. Re-create the endpoint: `databricks bundle deploy -t develop`
   (or re-apply `backup/iris-species-dev.json` settings first).
3. Re-enable pipelines (AzDO enable; GitHub enable workflow).
4. POST one inference check: `docs/serving-inference-test.md`.
5. Stamp a new snapshot in `docs/cost-tracker.md`.
