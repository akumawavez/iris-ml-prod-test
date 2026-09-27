# Runbook: ppe, prod, and UAE

Use this when the develop endpoint already works and you want the next environment. Do not follow it during the first three learning pull requests.

## Current state

- One future resource group: `rg-iris-ml-dev`
- One future workspace: `dbw-iris-ml-dev`
- One future endpoint: `iris-species-dev`
- `ppe` and `prod` are Git branches only
- Region plan: cheapest available region first, East US unless the cost sheet names a cheaper region that still offers CPU model serving

## Enable ppe in the same workspace

1. Confirm develop predictions and the Unity Catalog inference table look right.
2. Approve a cost sheet for a second endpoint. A second Small CPU endpoint has the same shape of bill as the first: about 4 DBU per hour while warm, then zero after 30 idle minutes, plus inference-table payload.
3. In `databricks.yml`, set the `ppe` target host to the same workspace host as `develop`.
4. Add a served endpoint named `iris-species-ppe`, copying the develop endpoint settings, including scale-to-zero and its own inference table.
5. Change the Azure DevOps pipeline so a push to `ppe` deploys `-t ppe` only after an environment approval named `ppe`.
6. Open that change as a pull request into `develop`, then merge `develop` into `ppe` so the reserved branch contains the same commit.
7. Run one manual approval in Azure DevOps and call the ppe endpoint.

## Enable prod the same way

Repeat the ppe steps with the names `prod`, `iris-species-prod`, and an Azure DevOps environment named `prod`. Prod still uses scale-to-zero until you explicitly accept an always-on bill. Scale-to-zero has a cold start and is not a latency guarantee. Source: [custom model serving](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/custom-models).

No separate resource group is required for this step.

## Move the workspace to UAE North

An Azure Databricks workspace region cannot be edited after creation. UAE means a new workspace.

1. Approve a cost sheet that uses UAE North prices from the Azure Databricks pricing page. Prices differ by region.
2. Confirm CPU model serving and Unity Catalog are offered in UAE North. If they are not, stop and pick the nearest region that offers both.
3. Create `rg-iris-ml-uae` and `dbw-iris-ml-uae` in UAE North.
4. Register the same saved MLflow model into that workspace's Unity Catalog. Do not retrain it.
5. Point the bundle target you are moving at the new workspace host and deploy one endpoint there.
6. Call the new endpoint, confirm the inference table is receiving rows, then delete the old endpoint in East US so it cannot wake and bill.
7. Leave the old workspace only if you still want its model history. An idle workspace still has a storage account. Delete the old resource group when you no longer need that history.

## Rollback

If a deploy breaks the develop endpoint, redeploy the previous bundle commit:

```bash
git checkout <previous-good-commit>
databricks bundle deploy -t develop
```

Then return your checkout to the branch you were on. Do not fix a bad deploy by editing the endpoint only in the workspace UI. The bundle file has to match the workspace, or the next deploy will overwrite the repair.
