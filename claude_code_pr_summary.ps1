#!/usr/bin/env pwsh
param(
    [Parameter(Mandatory=$true)][string]$PrNumber,
    [Parameter(Mandatory=$true)][string]$Action,
    [Parameter(Mandatory=$true)][string]$RepoDir
)

Push-Location $RepoDir
try {
    claude -p "/pr-summary $PrNumber"
} finally {
    Pop-Location
}
exit $LASTEXITCODE
