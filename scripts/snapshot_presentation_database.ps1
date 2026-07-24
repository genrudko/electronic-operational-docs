[CmdletBinding()]
param(
    [Parameter()]
    [string]$Repo = "G:\electronic-operational-docs",

    [Parameter()]
    [string]$BackupRoot = "G:\EOD_BACKUPS"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Repo = [System.IO.Path]::GetFullPath($Repo)
$BackupRoot = [System.IO.Path]::GetFullPath($BackupRoot)
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Exporter = Join-Path $Repo "scripts\snapshot_presentation_database.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python проекта не найден: $Python"
}

if (-not (Test-Path -LiteralPath $Exporter -PathType Leaf)) {
    throw "Экспортёр snapshot не найден: $Exporter"
}

& $Python -X utf8 $Exporter --repo $Repo --backup-root $BackupRoot

if ($LASTEXITCODE -ne 0) {
    throw "Создание presentation snapshot завершилось с ошибкой. Код: $LASTEXITCODE"
}
