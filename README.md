# iris-ml-prod-test

Private practice project for shipping an iris classifier with MLflow, Unity Catalog, Databricks Asset Bundles, and Azure DevOps.

Nothing in Azure is created by this repository until a cost sheet is approved. The serving endpoint is a later step.

## Branches

`develop` is the default branch. `ppe` and `prod` are reserved and do not deploy. The rules are in [docs/branch-rules.md](docs/branch-rules.md).

## Learning pull requests

These three merge only after approval. Auto-merge comes later.

1. **Repo foundation** — merged. Ignore rules, branch rules, the Azure DevOps guide, the Asset Bundle guide, and the promotion runbook.
2. **Local model** — this change. Train once on your machine and check in the saved MLflow model. Inference loads that model. The response includes the input, the predicted species, a SHAP explanation, and a feature-importance explanation. Each explanation has a calculation narrative and a plain-language narrative.
3. **Registry and pipeline** — Unity Catalog layout, the Asset Bundle, and the Azure DevOps pipeline definition. The pipeline file is added. It does not create the endpoint.

## Score locally

```text
uv sync --extra dev
uv run pytest -q
uv run pre-commit run --all-files
uv run python -m iris_model.score --model models/iris_species --sepal-length-cm 5.1 --sepal-width-cm 3.5 --petal-length-cm 1.4 --petal-width-cm 0.2
```

Install the git hook once with `uv run pre-commit install`. Agent instructions are in [AGENTS.md](AGENTS.md). Cursor project hooks live in `.cursor/hooks.json`, and the review plugin is `plugins/iris-agent`.

`uv sync --locked` is the only install step (`uv.lock` is committed;
`requirements.txt` is its compiled output for Databricks/AML readers —
regenerate with `uv pip compile --universal pyproject.toml -o requirements.txt`).
Pytest loads `models/iris_species`. It does not train. Run `uv run python -m iris_model.train` only when you intend to replace that saved model and commit the new directory.

## Later, after a separate cost approval

- One resource group, one Premium Databricks workspace, one serverless CPU endpoint with scale-to-zero.
- Inference rows saved to a Unity Catalog table.
- A move to UAE North, which requires a new workspace. The region of an existing workspace cannot be changed.

## Guides

ELI25 (plain-language walkthroughs with diagrams):

- [MLOps lifecycle](docs/guides/eli25-mlops-lifecycle.md)
- [Vechtomova MLOps frameworks (Databricks map)](docs/guides/eli25-vechtomova-mlops-frameworks.md)
- [Databricks productionalisation](docs/guides/eli25-databricks-productionalisation.md)
- [Jobs and serving](docs/guides/eli25-jobs-and-serving.md)

How-to and ops:

- [Azure DevOps](docs/guides/azure-devops.md)
- [Databricks Asset Bundles](docs/guides/databricks-asset-bundles.md)
- [Cursor Pro agent models](docs/guides/cursor-pro-agent-models.md)
- [Promotion and UAE runbook](docs/runbooks/promote-ppe-prod-and-uae.md)
- [ADR-001](docs/decisions/ADR-001-develop-only-serving-path.md)
- [Cost tracker ($10 cap, signed record)](docs/cost-tracker.md) + [calculator](docs/cost-dashboard.html)
- [Teardown and restore ($0 spend)](docs/teardown-and-restore.md)
- [Serving inference test (POST)](docs/serving-inference-test.md)

## Pipelines

- CI is test-only and runs only when required: `.github/workflows/ci.yml`
  (GitHub) and `azure-pipelines.yml` (Azure DevOps, PRs into `develop`).
  Neither deploys.
- CD is manual-only and gated: `azure-pipelines-cd.yml` (`trigger: none`,
  `iris-develop` environment) and `.github/workflows/cd.yml`
  (`workflow_dispatch`, `develop` environment). Do not create or dispatch
  either until `docs/cost-tracker.md` is approved and the $10 budget exists.

## Approve a pull request

Comment on the pull request with what you want changed, or approve it and say to merge. Merges wait for that reply.
