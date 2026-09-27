#Requires -Version 5.1
<#
.SYNOPSIS
  Create the $10/month budget + email alerts for the iris dev resource group.
  GUARDED — refuses to run without -Confirm. DO NOT RUN before
  docs/cost-tracker.md is approved in a pull-request comment.
.EXAMPLE
  ./scripts/setup_budget.ps1 -ResourceGroup rg-iris-ml-dev -AlertEmail you@example.com -Confirm
#>
param(
  [Parameter(Mandatory)][string]$ResourceGroup,
  [Parameter(Mandatory)][string[]]$AlertEmail,
  [int]$MonthlyCap = 10,
  [switch]$Confirm
)
$ErrorActionPreference = 'Stop'
if (-not $Confirm) {
  Write-Host 'STOP: cost approval required. Re-run with -Confirm after docs/cost-tracker.md is approved.' -ForegroundColor Red
  exit 0
}
if ($MonthlyCap -ne 10) {
  throw "Team policy caps spend at 10 USD/month. Raising the cap needs a new approval (see docs/cost-tracker.md)."
}

$startDate = (Get-Date -Day 1).ToString('yyyy-MM-dd')
$emails = $AlertEmail -join ' '

az group show -n $ResourceGroup --query name -o tsv | Out-Null

az monitor action-group create `
  -g $ResourceGroup `
  --name ag-iris-dev-budget `
  --short-name irisbudget `
  --action email owner0 $AlertEmail[0] | Out-Null

az consumption budget create `
  --budget-name iris-dev-monthly `
  -g $ResourceGroup `
  --category Cost `
  --amount $MonthlyCap `
  --time-grain Monthly `
  --start-date $startDate `
  --end-date 2030-12-31 | Out-Null

Write-Host "Budget iris-dev-monthly created: $MonthlyCap USD/month on $ResourceGroup (alerts: 50/80/100%)."
Write-Host 'Next: wire the 50/80/100% notification emails in the portal, or deploy infra/budget.bicep for the full definition.'
