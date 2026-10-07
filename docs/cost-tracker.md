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

- **When (UTC):** 2026-10-07 19:25 UTC
- **Posted Azure charges (MTD):** **$27.04 USD** (₹2,596.01 INR)
- **Estimated burn this month vs $10 cap:** **$27.04 (270.4%) — ▲ OVER CAP**

### MTD Breakdown (Azure Cost Management)
| Resource Group / Scope | Service | Cost (INR) | Cost (USD) | Status |
|---|---|---|---|---|
| `rg-iris-ml-dev` | Azure Databricks (Workspaces + Serverless Compute) | ₹1,786.94 | $18.62 | Scaled to zero / 0 active clusters |
| `rg-iris-ml-dev` | NAT Gateway | ₹44.21 | $0.46 | Active provisioned |
| `rg-iris-ml-dev` | Key Vault | ₹0.00 | $0.00 | Provisioned (< $0.01) |
| `databricks-rg-dbw-iris-ml-dev-bpjytdnacwiyl` | NAT Gateway (Managed VNet) | ₹678.17 | $7.07 | Active provisioned (~$1.08/day) |
| `databricks-rg-dbw-iris-ml-dev-bpjytdnacwiyl` | Virtual Network | ₹75.35 | $0.79 | Provisioned |
| `databricks-rg-dbw-iris-ml-dev-bpjytdnacwiyl` | Azure Storage (Blob Standard LRS / ADLS) | ₹11.35 | $0.12 | Provisioned |
| `VisualStudioOnline-*` | Azure DevOps CI/CD Hosted Pipeline | ₹0.00 | $0.00 | Free grant (1,800 min) |
| **Total MTD Posted** | | **₹2,596.01** | **$27.04** | **▲ Over $10.00 cap** |

*Note: All 4 custom serving endpoints (`dev_ajaikm_hello-world-dev`, `dev_sp_helloworld_dab_dev_hello-world-dev`, `ppe-iris-species`, `prod-iris-species`) are verified `READY` and scaled to zero (0 compute idle). Baseline ongoing idle burn (~$1.20/day) is primarily driven by the Azure NAT Gateway hourly charge (~$0.045/hr).*
<!-- SNAPSHOT:END -->

## Guardrails

- The idle floor is the Databricks-managed NAT gateway, not a running cluster.
  Checked 2026-10-08: `rg-iris-ml-dev` has the workspace, Key Vault, and
  `id-iris-ml`. The managed resource group
  `databricks-rg-dbw-iris-ml-dev-bpjytdnacwiyl` has StandardV2 `nat-gateway`
  and a static public IP in `eastus`. That is the ~$1.08/day line in the
  snapshot above. Do not delete resources in the managed group. Removing
  that hourly charge means deleting the workspace, which is
  [teardown-and-restore.md](teardown-and-restore.md), and it was not done.
- Same check: no all-purpose clusters. The serverless SQL warehouse is
  stopped. Iris custom endpoints that exist are Small CPU with scale-to-zero.
  The bundle names `iris-species-develop`, `iris-species-ppe`, and
  `iris-species-prod` are not created yet. Creating one is a paid step.
  Hello-world endpoints belong to another project. Leave them.
- Default CD `serve` does not start train or infer. Both jobs allow one run
  and stop on their own (train 20 minutes, infer 10 minutes). A second click
  does not queue another run.
- Scale-to-zero stays ON; Small workload only; `ppe`/`prod` hosts stay empty.
- CD is `azure-pipelines-cd.yml` only. It stays uncreated until this cap's
  budget exists. GitHub Actions stays disabled.
- Review this file monthly; re-approve if any assumption moves >20%.

## Price-check commands (reads only, safe anytime)

```powershell
./scripts/cost_snapshot.ps1 -ResourceGroup rg-iris-ml-dev
# Databricks: Account console -> Usage -> download DBU CSV, compare with A2
```
