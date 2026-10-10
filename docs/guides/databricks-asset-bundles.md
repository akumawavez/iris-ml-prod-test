# Databricks Asset Bundles guide

New to the loop? Start with [ELI25: Databricks productionalisation](eli25-databricks-productionalisation.md).
The rules for how this bundle is written are
[Databricks bundle best practices](databricks-bundle-best-practices.md).

A Databricks Asset Bundle is the YAML description of the workspace resources for this project. The bundle file itself is added in the third learning pull request. This guide is how to read it and how to deploy it later without leaving a cluster running.

Official reference: [Databricks Asset Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/).

## What the bundle will declare

One model-serving endpoint per target. Names are env-prefixed so develop, ppe, and prod can share one workspace today:

- Names: `iris-species-develop`, `iris-species-ppe`, `iris-species-prod`
- Model: Unity Catalog `dbw_iris_ml_dev.<env>.iris_species` with alias `@<env>` and `Champion`
- Compute: CPU, workload size Small
- `scale_to_zero_enabled: true`
- No all-purpose cluster and no SQL warehouse

Git branch `develop` matches target `develop`, `ppe` matches `ppe`, and `main` matches target `prod`. `ppe` and `prod` use the same `workspace_host` as develop until you change the host in `databricks/targets/ppe.yml` or `databricks/targets/prod.yml`. See the [promotion runbook](../runbooks/promote-ppe-prod-and-uae.md).

The bundle root stays `databricks.yml` (name, wheel build, and `include`). Definitions live under `databricks/`:

- `databricks/variables.yml` — shared variable defaults
- `databricks/artifacts/` — model serving endpoint
- `databricks/jobs/` — train and infer jobs
- `databricks/targets/` — `develop`, `ppe`, and `prod`

The shape of `databricks/targets/develop.yml`:

```yaml
targets:
  develop:
    mode: production
    default: true
    workspace:
      host: https://adb-<id>.azuredatabricks.net
```

`databricks/targets/ppe.yml` and `databricks/targets/prod.yml` use the same host URL as develop today. Change only that host when those workspaces exist.

The real endpoint block is added with the pipeline pull request. Do not invent a second endpoint beside it.

## Commands you will use later

Install the Databricks CLI from the official install page, then authenticate as a user once on your machine. The Azure DevOps service principal is a separate credential, stored in the `iris-develop` variable group, and it is created only with the cost-approved deploy.

From the repository root:

```bash
databricks bundle validate -t develop
databricks bundle deploy -t develop
```

`validate` checks the YAML. `deploy` creates or updates workspace resources and is a paid step once an endpoint is in the bundle. Do not run `deploy` until the cost sheet is approved.

Do not run either command with `-t ppe` or `-t prod` until the runbook's enablement steps are done. An empty host should fail validation, which is what we want.

## Cost controls inside the bundle

- Scale-to-zero is on. CPU model serving bills 1 DBU per hour per concurrent-request slot. Small allows up to 4 slots, so a warm endpoint is about 4 DBU per hour. After 30 minutes with no calls it scales to zero and that charge stops. Sources: [DBU rates](https://learn.microsoft.com/en-us/azure/databricks/resources/pricing), [custom models](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/custom-models).
- The inference table bills about 7.143 DBU per GB of logged payload. Iris rows are small. The charge is still listed on the cost sheet before the endpoint is created.
- Usage-tracking beyond the inference table stays off.
- Workspace region for the first deploy is the cheapest region that offers this CPU endpoint, planned as East US. The live dollar rate is copied onto the cost sheet from the Azure pricing page before deploy.

## What deploy does not do

`bundle deploy` does not create the Azure resource group or the Databricks workspace. Those are created once, in the portal or with the Azure CLI, during the approved setup step. The bundle then deploys into that workspace.
