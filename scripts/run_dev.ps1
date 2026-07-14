param(
    [int]$Port = 0,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
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
                # This was only a local availability probe.
            }
        }
    }
}

function Get-FreeLocalPort {
    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    try {
        $listener.Start()
        return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    }
    finally {
        $listener.Stop()
    }
}

if ($Port -gt 0) {
    if (-not (Test-LocalPort -Candidate $Port)) {
        throw "Локальный порт $Port занят или запрещён Windows."
    }
    $SelectedPort = $Port
}
else {
    $SelectedPort = Get-FreeLocalPort
}

$BaseUrl = "http://127.0.0.1:$SelectedPort"
Write-Host ""
Write-Host "Электронная оперативная документация" -ForegroundColor Cyan
Write-Host "Локальный профиль: SQLite" -ForegroundColor DarkYellow
Write-Host "Главная страница: $BaseUrl/" -ForegroundColor Green
Write-Host "Проверка состояния: $BaseUrl/health/" -ForegroundColor Green
Write-Host ""

if ($CheckOnly) {
    Write-Host "Проверка выбора порта выполнена успешно."
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

& ".venv\Scripts\python.exe" manage.py runserver "127.0.0.1:$SelectedPort"
