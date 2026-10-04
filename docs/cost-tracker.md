# Cost tracker — Azure + Databricks (LIVE, signed record)

> **Status: PROPOSED — $10.00/month cap.** Nothing is provisioned by this file.
> Approval happens in a pull-request comment on `docs/cost-sheet.md`; the
> budget itself is created only by `scripts/setup_budget.ps1 -Confirm` after
> that approval.
>
> File ownership: **this `.md` is the signed record** (cap, alerts, snapshots).
> `docs/cost-dashboard.html` is the scratch calculator (same math, runs fully
> in your browser, no data leaves your machine).

## Architecture being priced (develop only)

- 1 resource group, 1 **Premium** Databricks workspace (`eastus` first; UAE
  North later = new workspace, region can't change).
- 1 serverless CPU endpoint `iris-species-dev`, scale-to-zero ON, Small.
- 1 Unity Catalog catalog+schema, inference table writes ON.
- CI: Azure DevOps, 1 free Microsoft-hosted parallel job (1,800 min/mo after
  linking a subscription — link billing only at approval time).

## Assumptions

| # | Assumption | Value | Source |
|---|---|---|---|
| A1 | Serverless real-time inference USD per DBU (East US) | **$0.07 / DBU** | Azure Retail Prices API, live-checked 2026-09-27: `Premium Serverless Realtime Inferencing`, `eastus`, `1 Hour` — query: `serviceName eq 'Azure Databricks' and armRegionName eq 'eastus'` at <https://prices.azure.com/api/retail/prices> |
| A2 | DBU per endpoint-hour (Small, CPU) | **1 – 4 DBU/h** (0 when idle) | [Databricks custom model serving](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/custom-models) |
| A3 | Active endpoint-hours / month (scale-to-zero makes idle ≈ 0) | **35 h** | Team estimate, sized so the cap below holds |
| A4 | Premium workspace base / month (no compute) | **$0.00** | Azure Databricks pricing ($0 base fee) |
| A5 | Storage: model + inference table GB / month | **< 1 GB** (~$0.05) | Azure Blob Storage Standard LRS |
| A6 | Azure DevOps extra parallel jobs | **0** ($0.00) | [Parallel jobs](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs) (1 free job, 1,800 min/mo) |

## Monthly estimate vs cap

```text
endpoint USD/mo = A1 ($0.07/DBU) x A2 (up to 4 DBU/h) x A3 (35 h/mo) = $9.80/mo max
storage USD/mo  = < 1 GB x Azure storage rate ~= $0.05/mo
TOTAL           = ~$9.85 / mo  ->  cap: $10.00 / month
```

| Line | Value |
|---|---|
| Endpoint USD/mo (warm, 35 h max) | $9.80 |
| Storage USD/mo | $0.05 |
| **TOTAL cap USD/mo** | **$10.00 / month** |

If usage would exceed 35 active hours in a month, stop the endpoint (see
`docs/teardown-and-restore.md`) instead of raising the cap. Raising the cap
needs a new approval.

## Budget alerts (created by `scripts/setup_budget.ps1 -Confirm`, see `infra/budget.bicep`)

| Threshold | Pct of $10 cap | Action |
|---|---|---|
| $5.00 | 50% | Email owners: usage is half the cap |
| $8.00 | 80% | Email owners: slow down or stop the endpoint |
| $10.00 | 100% | Email owners **and** follow the zero-spend shutdown in `docs/teardown-and-restore.md` |

Alert recipients are passed as script parameters — no email address lives in git.

## Tracking cadence: every 30 minutes of active use

While the endpoint exists and is warm, refresh the snapshot **every 30 min**:

```powershell
./scripts/cost_snapshot.ps1 -ResourceGroup rg-iris-ml-dev
./scripts/cost_snapshot.ps1 -ResourceGroup rg-iris-ml-dev -UpdateTracker
```

`-UpdateTracker` rewrites only the snapshot block below (between the
`SNAPSHOT` markers). CI never runs this on a schedule — scheduled runs would
spend the free DevOps minutes this budget protects.

<!-- SNAPSHOT:START -->
## Last snapshot

- **When (UTC):** _never — no resources created yet_
- **Posted Azure charges:** _$0.00_
- **Estimated burn this month vs $10 cap:** _$0.00 (0%)_
<!-- SNAPSHOT:END -->

## Guardrails

- Scale-to-zero stays ON; Small workload only; `ppe`/`prod` hosts stay empty.
- CD is `azure-pipelines-cd.yml` only. It stays uncreated until this cap's
  budget exists. GitHub Actions stays disabled.
- Review this file monthly; re-approve if any assumption moves >20%.

## Price-check commands (reads only, safe anytime)

```powershell
./scripts/cost_snapshot.ps1 -ResourceGroup rg-iris-ml-dev
# Databricks: Account console -> Usage -> download DBU CSV, compare with A2
```
