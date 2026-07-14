$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker не найден. Для локального запуска используйте scripts\run_dev.ps1."
}

$env:DB_ENGINE = "postgresql"
docker compose up -d db
& ".venv\Scripts\python.exe" manage.py migrate --noinput
& ".venv\Scripts\python.exe" manage.py check
& ".venv\Scripts\python.exe" manage.py runserver
