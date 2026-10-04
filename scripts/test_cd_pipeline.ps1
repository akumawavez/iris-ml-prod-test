#Requires -Version 5.1
<#
.SYNOPSIS
  Local validation and smoke test of the Databricks CD pipeline steps.
  Safe by default — validates the bundle and runs the dry-run inference test.
.EXAMPLE
  ./scripts/test_cd_pipeline.ps1
  ./scripts/test_cd_pipeline.ps1 -Live   # requires live DATABRICKS_HOST and DATABRICKS_TOKEN
#>
[CmdletBinding()]
param(
  [string]$Target = "develop",
  [switch]$Live
)
$ErrorActionPreference = "Stop"

Write-Host "=== 1. Checking Databricks CLI ===" -ForegroundColor Cyan
if (-not (Get-Command databricks -ErrorAction SilentlyContinue)) {
  Write-Warning "databricks CLI not found in PATH."
} else {
  $ver = databricks version
  Write-Host "Found: $ver" -ForegroundColor Green
}

Write-Host "=== 2. Validating Databricks Asset Bundle ($Target) ===" -ForegroundColor Cyan
databricks bundle validate -t $Target
Write-Host "Bundle validation passed." -ForegroundColor Green

Write-Host "=== 3. Running train-infer job (live only) ===" -ForegroundColor Cyan
if ($Live) {
  databricks bundle run iris-ml-job-pipeline -t $Target
} else {
  Write-Host "Skipped bundle run (pass -Live to execute iris-ml-job-pipeline)."
}

Write-Host "=== 4. Running Serving Endpoint Smoke Check ===" -ForegroundColor Cyan
if ($Live) {
  uv run python scripts/test_serving.py --endpoint iris-species-dev --live
} else {
  uv run python scripts/test_serving.py --endpoint iris-species-dev --dry-run
}
Write-Host "CD pipeline smoke check completed successfully." -ForegroundColor Green
