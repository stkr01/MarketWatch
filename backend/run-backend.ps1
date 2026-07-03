# Start the Pre-Market backend robustly, regardless of where it's launched from.
# Uses the venv's python directly (no activation needed) and always runs from
# the backend directory so `app.main` resolves.
$ErrorActionPreference = 'Stop'
$backend = $PSScriptRoot
$python = Join-Path $backend 'venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    Write-Host "ERROR: venv not found at $python" -ForegroundColor Red
    Write-Host "Create it first:  python -m venv venv ; .\venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Warn if something already holds port 8000 (a stale server = bind failure).
$busy = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    $pid8000 = ($busy.OwningProcess | Select-Object -Unique) -join ', '
    Write-Host "WARNING: port 8000 is already in use (PID $pid8000)." -ForegroundColor Yellow
    Write-Host "Stop it first:  Get-Process -Id $pid8000 | Stop-Process -Force" -ForegroundColor Yellow
    exit 1
}

Set-Location $backend
Write-Host "Starting backend on http://localhost:8000  (Ctrl+C to stop)" -ForegroundColor Cyan
& $python -m uvicorn app.main:app --reload --port 8000
