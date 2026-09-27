# Cost Sheet: Iris develop serving path

## What would be created later

Creation waits for an explicit approval of this document. The items that would be created:

- Resource group: `rg-iris-ml-dev`
- Azure Databricks workspace (Premium): `dbw-iris-ml-dev`
- Unity Catalog model: `iris_ml.develop.iris_species`
- Model serving endpoint: `iris-species-dev`

## DBU facts and usage estimates

- **CPU model serving**: 1 DBU per hour per concurrent-request slot. Small workload size allows up to 4 concurrent slots, so a warm endpoint consumes up to 4 DBU per hour while handling requests. After 30 minutes with no incoming requests, the endpoint automatically scales to zero (0 DBU/hour).
- **Inference table**: Automatically logs request payloads and predictions at approximately 7.143 DBU per GB of payload data.
- **Azure DevOps parallel jobs**: 1 Microsoft-hosted job with 1,800 free minutes per month (up to 60 minutes per job) once the organization is linked to an Azure subscription.

## Live dollar rate

```text
serverless_real_time_inference_usd_per_dbu_east_us:
```

> **Instruction:** Copy the live number above from the official Azure Databricks pricing page for Premium Serverless Real-Time Inference in East US. If the pricing page shows no number, stop and ask. Do not guess or invent a dollar rate.

## Approval gate

Do not create any Azure or Databricks resource, do not link billing or subscriptions, and do not run `databricks bundle deploy` until this cost sheet is explicitly approved in a pull request comment.
