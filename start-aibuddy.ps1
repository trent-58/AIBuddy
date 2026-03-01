Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [string]$HelpMessage = ""
    )
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        if ($HelpMessage) {
            throw $HelpMessage
        }
        throw "Required command not found: $Name"
    }
}

function Ensure-Poetry {
    if (Get-Command poetry -ErrorAction SilentlyContinue) {
        Write-Host "Poetry found." -ForegroundColor Green
        return
    }

    Write-Step "Poetry not found. Installing Poetry..."

    $installScript = (Invoke-WebRequest -Uri "https://install.python-poetry.org" -UseBasicParsing).Content

    if (Get-Command py -ErrorAction SilentlyContinue) {
        $installScript | py -
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $installScript | python -
    }
    else {
        throw "Python is required to install Poetry. Install Python (with py launcher) and run again."
    }

    $poetryPath1 = Join-Path $env:APPDATA "Python\Scripts"
    $poetryPath2 = Join-Path $env:USERPROFILE ".local\bin"
    $env:PATH = "$poetryPath1;$poetryPath2;$env:PATH"

    Assert-Command -Name "poetry" -HelpMessage "Poetry installation finished, but poetry command is still unavailable. Open a new terminal and run again."
    Write-Host "Poetry installed." -ForegroundColor Green
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

if (-not (Test-Path $backendPath)) {
    throw "Backend directory not found: $backendPath"
}
if (-not (Test-Path $frontendPath)) {
    throw "Frontend directory not found: $frontendPath"
}

Write-Step "Checking required tools"
Ensure-Poetry
Assert-Command -Name "npm" -HelpMessage "npm is required for frontend setup. Install Node.js and run again."

Write-Step "Installing backend dependencies (Poetry)"
Push-Location $backendPath
poetry install
poetry run python manage.py migrate
Pop-Location

Write-Step "Installing frontend dependencies (npm)"
Push-Location $frontendPath
npm install
Pop-Location

Write-Step "Starting backend and frontend in separate PowerShell windows"

$backendCmd = "Set-Location -LiteralPath '$backendPath'; poetry run python manage.py runserver"
$frontendCmd = "Set-Location -LiteralPath '$frontendPath'; npm run dev"

Start-Process powershell -ArgumentList @("-NoExit", "-Command", $backendCmd) | Out-Null
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $frontendCmd) | Out-Null

Write-Host ""
Write-Host "Backend and frontend are starting in two new windows." -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor Yellow
