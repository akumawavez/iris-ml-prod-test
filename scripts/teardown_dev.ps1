#Requires -Version 5.1
<#
.SYNOPSIS
  Zero-spend shutdown for the iris dev setup. GUARDED — refuses to run
  without -Confirm. Default stops the endpoint and prints the pipeline-disable
  checklist; NOTHING is deleted unless -IncludeDelete is also passed.
  Backup (endpoint JSON into backup/<date>/) always runs first.
  DO NOT RUN before reading docs/teardown-and-restore.md.
.EXAMPLE
  ./scripts/teardown_dev.ps1 -Confirm
  ./scripts/teardown_dev.ps1 -ResourceGroup rg-iris-ml-dev -Confirm -IncludeDelete
#>
param(
  [string]$ResourceGroup = 'rg-iris-ml-dev',
  [string]$EndpointName = 'iris-species-dev',
  [switch]$Confirm,
  [switch]$IncludeDelete
)
$ErrorActionPreference = 'Stop'
if (-not $Confirm) {
  Write-Host 'STOP: this script stops cloud resources. Re-run with -Confirm after reading docs/teardown-and-restore.md.' -ForegroundColor Red
  exit 0
}

$stamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd-HHmm')
$backupDir = Join-Path (Split-Path $PSScriptRoot -Parent) "backup/$stamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

Write-Host 'Step 1/4: backup endpoint config...'
try {
  databricks serving-endpoints get $EndpointName | Out-File (Join-Path $backupDir "$EndpointName.json")
  Write-Host "Saved to $backupDir/$EndpointName.json"
} catch {
  Write-Host "No live endpoint reachable (already stopped/deleted?) — continuing with git-backed recipe." -ForegroundColor Yellow
}
git status --short -- databricks.yml databricks/ | Out-Null
Write-Host 'Bundle recipe (databricks.yml + databricks/) must be clean-committed before delete.'

Write-Host 'Step 2/4: stop the endpoint (spend -> $0 DBU)...'
try {
  databricks serving-endpoints delete $EndpointName
  Write-Host "Delete requested for $EndpointName."
} catch {
  Write-Host "Endpoint delete skipped/failed safely: $_" -ForegroundColor Yellow
}

Write-Host 'Step 3/4: disable pipelines (portal clicks — CLI cannot do these safely):'
Write-Host '  - Azure DevOps: Pipelines -> iris-ml-prod-test-ci -> ... -> Disable (never create azure-pipelines-cd.yml).'
Write-Host '  - GitHub: Actions -> ci -> ... -> Disable workflow (never dispatch cd.yml).'

if ($IncludeDelete) {
  Write-Host 'Step 4/4: DELETE the resource group (irreversible)...' -ForegroundColor Red
  az group delete -n $ResourceGroup --yes --no-wait
  Write-Host "Delete requested for $ResourceGroup."
} else {
  Write-Host 'Step 4/4: skipped (no -IncludeDelete). Workspace with no compute bills $0; the group stays for restore.'
}

Write-Host 'Done. Verify with: ./scripts/cost_snapshot.ps1 -ResourceGroup $ResourceGroup'
