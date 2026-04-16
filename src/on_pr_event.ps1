#!/usr/bin/env pwsh
$py = if (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } else { 'python' }
& $py (Join-Path $PSScriptRoot 'on_pr_event.py') @args
exit $LASTEXITCODE
