#!/usr/bin/env pwsh
$py = if ($IsWindows) { 'python' } else { 'python3' }
& $py (Join-Path $PSScriptRoot 'on_pr_event.py') @args
exit $LASTEXITCODE
