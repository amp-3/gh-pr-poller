#!/usr/bin/env pwsh
param(
    [Parameter(Mandatory=$true)][string]$PrNumber,
    [Parameter(Mandatory=$true)][string]$Action,
    [Parameter(Mandatory=$true)][string]$RepoDir
)

$dir = $PSScriptRoot
& "$dir/claude_code_pr_summary.ps1" $PrNumber $Action $RepoDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$dir/claude_code_pr_review.ps1" $PrNumber $Action $RepoDir
exit $LASTEXITCODE
