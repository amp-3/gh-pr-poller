#!/usr/bin/env pwsh
$py = if ($IsWindows) { 'python' } else { 'python3' }

$repo = 'ORGANIZATION/REPO_NAME'
$repoDir = 'C:\REPO_PATH_HERE'

Set-Location $PSScriptRoot
& $py gh_pr_poller.py ./on_pr_event.ps1 `
    --repo $repo `
    --repo-dir $repoDir `
    --interval 10 `
    --recent 1000 `
    --force
