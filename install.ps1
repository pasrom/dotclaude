# ----------------------------------------------------------------------
# install.ps1 — Set up dotclaude skills and aliases on Windows
# ----------------------------------------------------------------------
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"

function Write-Ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "  → $msg (already exists)" -ForegroundColor Yellow }

# -- Install skills (junction) ------------------------------------------
Write-Host "Installing skills..."

$SkillsDir = Join-Path $ClaudeDir "skills"
if (-not (Test-Path $SkillsDir)) {
    New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null
}

Get-ChildItem -Path (Join-Path $ScriptDir "skills") -Directory | ForEach-Object {
    $target = Join-Path $SkillsDir $_.Name
    if ($Force -and (Test-Path $target)) {
        Remove-Item -Path $target -Recurse -Force
    }
    if (Test-Path $target) {
        Write-Skip "skills/$($_.Name)"
    } else {
        cmd /c mklink /J "$target" "$($_.FullName)" | Out-Null
        Write-Ok "skills/$($_.Name)"
    }
}

# -- Check prerequisites ------------------------------------------------
Write-Host ""
Write-Host "Checking prerequisites..."

foreach ($cmd in @("claude", "glab", "python3", "python")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        Write-Ok $cmd
    } else {
        Write-Host "  ✗ $cmd not found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Done. Skills are now available in Claude Code."
