# iris-ml-prod-test

Private practice project for shipping an iris classifier with MLflow, Unity Catalog, Databricks Asset Bundles, and Azure DevOps.

Nothing in Azure is created by this repository until a cost sheet is approved. The serving endpoint is a later step.

## Branches

`develop` is the default branch. `ppe` and `prod` are reserved and do not deploy. The rules are in [docs/branch-rules.md](docs/branch-rules.md).

## Learning pull requests

These three merge only after approval. Auto-merge comes later.

1. **Repo foundation** — this change. Ignore rules, branch rules, the Azure DevOps guide, the Asset Bundle guide, and the promotion runbook.
2. **Local model** — train once on your machine and check in the saved MLflow model. Inference loads that model. The response includes the input, the predicted species, a SHAP explanation, and a feature-importance explanation. Each explanation has a calculation narrative and a plain-language narrative.
3. **Registry and pipeline** — Unity Catalog layout, the Asset Bundle, and the Azure DevOps pipeline definition. The pipeline file is added. It does not create the endpoint.

## Later, after a separate cost approval

- One resource group, one Premium Databricks workspace, one serverless CPU endpoint with scale-to-zero.
- Inference rows saved to a Unity Catalog table.
- A move to UAE North, which requires a new workspace. The region of an existing workspace cannot be changed.

## Guides

- [Azure DevOps](docs/guides/azure-devops.md)
- [Databricks Asset Bundles](docs/guides/databricks-asset-bundles.md)
- [Promotion and UAE runbook](docs/runbooks/promote-ppe-prod-and-uae.md)
- [ADR-001](docs/decisions/ADR-001-develop-only-serving-path.md)

## Approve a pull request

Comment on the pull request with what you want changed, or approve it and say to merge. Merges wait for that reply.
