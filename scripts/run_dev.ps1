param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

# Windows PowerShell 5.1 requires an UTF-8 BOM in this file.
# Explicit encodings keep PowerShell and Django output readable.
$Utf8Encoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $Utf8Encoding
[Console]::OutputEncoding = $Utf8Encoding
$OutputEncoding = $Utf8Encoding
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:DB_ENGINE = "sqlite"

function Test-LocalPort {
    param([int]$Candidate)

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new(
            [System.Net.IPAddress]::Loopback,
            $Candidate
        )
        $listener.Start()
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($null -ne $listener) {
            try {
                $listener.Stop()
            }
            catch {
                # Availability probe only.
            }
        }
    }
}

if (-not (Test-LocalPort -Candidate $Port)) {
    throw "Локальный порт $Port занят или запрещён Windows. Освободите порт или укажите другой через -Port."
}

$BaseUrl = "http://127.0.0.1:$Port"
Write-Host ""
Write-Host "Электронная оперативная документация" -ForegroundColor Cyan
Write-Host "Локальный профиль: SQLite" -ForegroundColor DarkYellow
Write-Host "Постоянный адрес: $BaseUrl/" -ForegroundColor Green
Write-Host "Проверка состояния: $BaseUrl/health/" -ForegroundColor Green
Write-Host ""

if ($CheckOnly) {
    Write-Host "Проверка запуска выполнена успешно." -ForegroundColor Cyan
    exit 0
}

& ".venv\Scripts\python.exe" manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) {
    throw "Django migrate завершился с ошибкой."
}

& ".venv\Scripts\python.exe" manage.py check
if ($LASTEXITCODE -ne 0) {
    throw "Django check завершился с ошибкой."
}

& ".venv\Scripts\python.exe" manage.py runserver "127.0.0.1:$Port"
