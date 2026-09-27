#Requires -Version 5.1
<#
.SYNOPSIS
  Read-only cost snapshot for the iris dev resource group. SAFE anytime:
  queries posted Azure costs and prints burn vs the $10 cap. Creates nothing.
  Run every 30 minutes of active endpoint use; add -UpdateTracker to stamp
  the snapshot block in docs/cost-tracker.md (that block only).
.EXAMPLE
  ./scripts/cost_snapshot.ps1 -ResourceGroup rg-iris-ml-dev
  ./scripts/cost_snapshot.ps1 -ResourceGroup rg-iris-ml-dev -UpdateTracker
#>
param(
  [Parameter(Mandatory)][string]$ResourceGroup,
  [decimal]$MonthlyCap = 10,
  [switch]$UpdateTracker
)
$ErrorActionPreference = 'Stop'

$rows = @()
try {
  $json = az consumption usage list -g $ResourceGroup --query '[].{name:instanceName, cost:pretaxCost}' -o json 2>$null
  if ($json) { $rows = $json | ConvertFrom-Json }
} catch {
  Write-Host 'Cost Management has no posted rows yet (8-24 h ingestion lag on new resources).' -ForegroundColor Yellow
}

$posted = 0
foreach ($row in $rows) { $posted += [decimal]$row.cost }
$pct = if ($MonthlyCap -gt 0) { [math]::Round(100 * $posted / $MonthlyCap, 1) } else { 0 }

Write-Host "Resource group : $ResourceGroup"
Write-Host "Posted charges : $posted USD"
Write-Host "Burn vs cap    : $posted / $MonthlyCap USD ($pct%)"
if ($pct -ge 100) {
  Write-Host 'OVER CAP: follow docs/teardown-and-restore.md now.' -ForegroundColor Red
} elseif ($pct -ge 80) {
  Write-Host 'Above 80%: slow down or stop the endpoint.' -ForegroundColor Yellow
}

if ($UpdateTracker) {
  $tracker = Join-Path (Split-Path $PSScriptRoot -Parent) 'docs/cost-tracker.md'
  $text = Get-Content $tracker -Raw
  $now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm') + ' UTC'
  $block = '## Last snapshot' + "`r`n`r`n" + '- **When (UTC):** ' + $now + "`r`n" + '- **Posted Azure charges:** _' + $posted + '_`r`n' + '- **Estimated burn this month vs ' + $MonthlyCap + ' cap:** _' + $posted + ' (' + $pct + '%)_'
  $pattern = '<!-- SNAPSHOT:START -->[\s\S]*?<!-- SNAPSHOT:END -->'
  $replacement = '<!-- SNAPSHOT:START -->' + "`r`n" + $block + "`r`n" + '<!-- SNAPSHOT:END -->'
  $text = [regex]::Replace($text, $pattern, $replacement)
  Set-Content $tracker $text -NoNewline
  Write-Host "Tracker snapshot block updated ($now)."
}
