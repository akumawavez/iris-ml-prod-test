# Productionalisation ready

How far this repo is along the move from a notebook to a system someone else can run, promote, and shut off. Percentages are completeness of that step on 4 October 2026. **Overall** is the mean of the Progress column, rounded to the nearest percent.

Overall: 73%

| Step | Progress | Now |
|---|---|---|
| Folder structure | 90% | `src/iris_model`, `notebooks`, `databricks`, `tests`, `docs`, `infra`. |
| Required code and YAML | 85% | Package, lockfile, one job, three targets, endpoint shape, CI, and gated CD. |
| CI versus CD split | 90% | CI tests and validates. CD is the only place that deploys, and it does not run on push. |
| Rules written and followed | 80% | [rules.md](../productionalisation/rules.md). Branch protection cannot be enforced on this private GitHub plan. |
| Runbooks | 75% | Promote and teardown exist. They still assume a human reads them. |
| Cost approval | 35% | The cap is $10 and the status is still proposed. Jobs have been deployed while the signed snapshot says nothing was created. |
| Secret names and Key Vault | 80% | Names are in git. Values are in Key Vault `kv-iris-ml-dev-7405` and local `.env`. |
| Who deploys | 75% | CD is wired to a service principal per environment. Creating those apps is still an Azure step. |
| Docs match the code | 80% | This change updates the served-version and deploy-identity pages. Older design notes under `docs/superpowers/` stay historical. |
| Monitor and retrain | 25% | Cost text and a dry-run POST. No drift monitor and no schedule. |
| Readiness pages | 90% | This file, [mlops-ready.md](mlops-ready.md), and [databricks-mlops-ready.md](databricks-mlops-ready.md). The percentages are the status, not a claim that the loop is finished. |

## Read these next

- Checklist of folders and files: [productionalisation](../productionalisation/README.md)
- When to use a gateway, a model, or an endpoint: [AI Gateway, models, and serving](../guides/ai-gateway-models-and-serving.md)
- Open defect: [ISS-020](../../issues.md)
