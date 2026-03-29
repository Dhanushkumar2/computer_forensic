# PowerShell setup script for Windows
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $RootDir ".venv"

function Require-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Write-Host "Missing $name. Please install it and re-run." -ForegroundColor Red
    exit 1
  }
}

Write-Host "Checking system dependencies..." -ForegroundColor Cyan
Require-Command python
Require-Command node
Require-Command npm

Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path $VenvDir)) {
  python -m venv $VenvDir
}

& "$VenvDir\Scripts\Activate.ps1"
python -m pip install --upgrade pip

Write-Host "Installing backend Python dependencies..." -ForegroundColor Cyan
python -m pip install -r "$RootDir\backend\requirements.txt"

Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location "$RootDir\frontend"
npm install
Pop-Location

Write-Host "Running Django migrations..." -ForegroundColor Cyan
Push-Location "$RootDir\backend"
python manage.py migrate
Pop-Location

Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1) Start backend:  cd backend; ..\.venv\Scripts\Activate.ps1; python manage.py runserver"
Write-Host "2) Start frontend: cd frontend; npm start"
