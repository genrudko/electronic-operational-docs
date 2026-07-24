[CmdletBinding()]
param(
    [Parameter()]
    [string]$Repo = "G:\electronic-operational-docs",

    [Parameter()]
    [string]$BackupRoot = "G:\EOD_BACKUPS"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$Repo = [System.IO.Path]::GetFullPath($Repo)
$BackupRoot = [System.IO.Path]::GetFullPath($BackupRoot)
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Exporter = Join-Path $Repo "scripts\snapshot_presentation_database.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Project Python was not found: $Python"
}

if (-not (Test-Path -LiteralPath $Exporter -PathType Leaf)) {
    throw "Presentation snapshot exporter was not found: $Exporter"
}

& $Python -X utf8 $Exporter --repo $Repo --backup-root $BackupRoot

if ($LASTEXITCODE -ne 0) {
    throw "Presentation snapshot creation failed. Exit code: $LASTEXITCODE"
}
