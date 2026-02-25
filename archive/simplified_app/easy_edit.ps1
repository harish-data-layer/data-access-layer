$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   TAI DATA EDITOR" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$pythonPath = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$scriptPath = Join-Path $PSScriptRoot "db\utils\auto_editor.py"

if (Test-Path $pythonPath) {
    Write-Host "Launching editor..." -ForegroundColor Green
    & $pythonPath $scriptPath
} else {
    Write-Host "ERROR: Python environment not found!" -ForegroundColor Red
    Write-Host "Looking for: $pythonPath"
    Write-Host "Please run setup_db.bat first to create the environment."
}

Write-Host "`nPress any key to close..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
