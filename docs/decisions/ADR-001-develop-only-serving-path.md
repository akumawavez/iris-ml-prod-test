# ADR-001: Develop-only serving path

## Status

Accepted for the $10 cap and scale-to-zero. Branch names were updated on 4 October 2026: the prod git branch is `main`, and the Databricks target for that branch remains `prod`. Later work superseded two lines in the decision below: the train job does run on Databricks, and ppe/prod targets share this workspace. Served version and deploy identity are in [the checks](../checks/productionalisation-ready.md).

## Date

2026-09-27

## Context

The goal is to learn a production release path for an iris classifier: feature branch, pull request, `develop`, then later `ppe` and `prod`. The Azure account has no subscription. Databricks and Azure DevOps are not set up. The bill has to stay as low as possible, and no paid resource is created before a cost approval.

GitHub is the only account that exists. The repo is private. GitHub MCP and Azure MCP were not connected when this decision was made, so GitHub setup uses the GitHub CLI until those connectors are available.

## Decision

- Train the model once on a local machine and keep the saved MLflow model. Inference loads that model. Pipelines do not train it again.
- Register the model with MLflow in Unity Catalog when a workspace exists.
- Use Databricks Asset Bundles to describe deployment.
- Use Azure DevOps, triggered by GitHub, as the pipeline.
- Run one Premium workspace in the cheapest region that offers CPU model serving, planned as East US, after the cost sheet is approved.
- Serve one endpoint, `iris-species-dev`, on serverless CPU, workload size Small, with scale-to-zero enabled.
- Save inference requests and responses in a Unity Catalog inference table when that endpoint is deployed.
- Keep `ppe` and `prod` as branches and as runbook steps. Do not create resource groups or endpoints for them now.
- Treat a later UAE North deployment as a new workspace. Do not plan to edit the region of the first workspace.
- Merge the first three learning pull requests only after an explicit approval.

## Alternatives considered

- Train on every deploy inside a Databricks job. Rejected because the dataset has 150 rows and the job would spend compute on each merge.
- Three workspaces and three resource groups now. Rejected because the current lesson is the release path, and the extra accounts add setup before the first prediction.
- Terraform and a classic job cluster. Rejected because a forgotten cluster is the expensive failure mode. Asset Bundles plus serverless serving avoid leaving a cluster up.
- Turn inference tables off to save the per-gigabyte charge. Rejected because saving each inference in Unity Catalog is a requirement. The charge stays on the cost sheet.

## Consequences

- The endpoint and the inference table do not exist until a later approved step.
- Idle serving cost depends on scale-to-zero. A warm Small CPU endpoint consumes about 4 DBU per hour, because CPU serving is 1 DBU per hour per concurrent-request slot and Small allows up to 4. After 30 minutes without requests the endpoint scales to zero. Source: [serverless DBU rates](https://learn.microsoft.com/en-us/azure/databricks/resources/pricing) and [custom model serving](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/custom-models).
- Inference tables bill about 7.143 DBU per GB of payload. Source: the same DBU rates page, AI Gateway section.
- The dollar rate per DBU is read from the live Azure Databricks pricing page for the chosen region at cost-approval time. It is not fixed in this record.
- Azure DevOps stays inside the free tier: one Microsoft-hosted parallel job and 1,800 minutes per month after the organization is linked to a subscription. Source: [parallel jobs](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs).
- Branch protection cannot be enforced by GitHub on a private Free repository. The team follows the rules in `docs/branch-rules.md` until the account can enforce them.
