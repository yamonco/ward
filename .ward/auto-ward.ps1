# auto-ward.ps1 - PowerShell 와드 자동 통합
# PowerShell 5.1+ 및 PowerShell Core 지원

param(
    [string]$Action = "auto",
    [string]$WardRoot = $null,
    [switch]$Help
)

# 스크립트 디렉터리 찾기
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $WardRoot) {
    $WardRoot = Split-Path -Parent $ScriptDir
}

# 색상 정의
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Cyan = "Cyan"
    White = "White"
}

function Write-WardInfo {
    param([string]$Message)
    Write-Host "[WARD AUTO] $Message" -ForegroundColor $Colors.Cyan
}

function Write-WardSuccess {
    param([string]$Message)
    Write-Host "[WARD AUTO] ✓ $Message" -ForegroundColor $Colors.Green
}

function Write-WardWarning {
    param([string]$Message)
    Write-Host "[WARD AUTO] ⚠ $Message" -ForegroundColor $Colors.Yellow
}

function Write-WardError {
    param([string]$Message)
    Write-Host "[WARD AUTO] ✗ $Message" -ForegroundColor $Colors.Red
}

# 와드 환경 감지
function Test-WardEnvironment {
    return (Test-Path "$WardRoot\.ward\guard.sh")
}

# 와드 루트 찾기
function Find-WardRoot {
    $currentDir = Get-Location
    while ($currentDir -ne "") {
        if (Test-Path "$currentDir\.ward\guard.sh") {
            return $currentDir
        }
        $currentDir = Split-Path -Parent $currentDir
    }
    return $null
}

# 와드 환경 보장
function Ensure-WardEnvironment {
    if (Test-WardEnvironment) {
        return $true
    }

    $wardRoot = Find-WardRoot
    if ($wardRoot) {
        $env:WARD_ROOT = $wardRoot
        $env:BASH_ENV = "$wardRoot\.ward\guard.sh"
        Write-WardSuccess "Ward environment detected: $wardRoot"
        return $true
    }

    return $false
}

# PowerShell 프로필 통합
function Install-PowerShellIntegration {
    $profilePath = $PROFILE.CurrentUserAllHosts

    if (-not (Test-Path $profilePath)) {
        New-Item -Path $profilePath -ItemType File -Force | Out-Null
        Write-WardInfo "Created PowerShell profile: $profilePath"
    }

    $integrationCode = @"

# === WARD AUTO INTEGRATION ===
if (Test-Path "$ScriptDir\auto-ward.ps1") {
    . "$ScriptDir\auto-ward.ps1" -Action auto
}
# === END WARD AUTO INTEGRATION ===
"@

    $profileContent = Get-Content $profilePath -Raw
    if ($profileContent -like "*auto-ward.ps1*") {
        Write-WardInfo "Ward integration already exists in PowerShell profile"
        return $true
    }

    Add-Content -Path $profilePath -Value $integrationCode
    Write-WardSuccess "Ward integration added to PowerShell profile"
    return $true
}

# 와드 쉘 활성화
function Invoke-WardShell {
    if (-not (Ensure-WardEnvironment)) {
        Write-WardWarning "No ward environment found"
        return $false
    }

    $wardShell = "$WardRoot\ward-shell"
    if (Test-Path $wardShell) {
        Write-WardInfo "Activating ward environment..."

        # Windows에서 bash 실행
        if (Get-Command bash -ErrorAction SilentlyContinue) {
            bash $wardShell
        } else {
            Write-WardError "bash not found. Please install Git Bash or WSL."
            return $false
        }
    } else {
        Write-WardError "ward-shell not found"
        return $false
    }
}

# Windows Terminal 설정
function Set-WindowsTerminalIntegration {
    $settingsPath = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"

    if (-not (Test-Path $settingsPath)) {
        Write-WardWarning "Windows Terminal settings not found"
        return $false
    }

    try {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        $wardProfile = @{
            name = "Ward Shell"
            commandline = "bash.exe -c `"$WardRoot\ward-shell`""
            startingDirectory = $WardRoot
            icon = "⚡"
        }

        if ($settings.profiles.list -isnot [array]) {
            $settings.profiles.list = @($settings.profiles.list)
        }

        $settings.profiles.list += $wardProfile
        $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath

        Write-WardSuccess "Windows Terminal integration added"
        return $true
    } catch {
        Write-WardError "Failed to update Windows Terminal settings: $($_.Exception.Message)"
        return $false
    }
}

# 환경 변수 설정
function Set-WardEnvironmentVariables {
    [Environment]::SetEnvironmentVariable("WARD_AUTO_MODE", "detect", "User")
    [Environment]::SetEnvironmentVariable("WARD_ROOT", $WardRoot, "User")

    Write-WardSuccess "Environment variables set for current user"
    return $true
}

# VS Code PowerShell 통합
function Set-VSCodePowerShellIntegration {
    $vscodeDir = "$WardRoot\.vscode"
    $settingsFile = "$vscodeDir\settings.json"

    if (-not (Test-Path $vscodeDir)) {
        New-Item -Path $vscodeDir -ItemType Directory -Force | Out-Null
    }

    $settings = @{
        "powershell.integratedConsole.focusOnExit" = $true
        "powershell.integratedProfiles" = @(
            @{
                "name" = "Ward PowerShell"
                "scriptPath" = "$ScriptDir\auto-ward.ps1"
            }
        )
        "terminal.integrated.defaultProfile.windows" = "Ward PowerShell"
    }

    if (Test-Path $settingsFile) {
        $existingSettings = Get-Content $settingsFile -Raw | ConvertFrom-Json
        $settings = $existingSettings + $settings
    }

    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsFile
    Write-WardSuccess "VS Code PowerShell integration configured"
}

# 전체 설치
function Install-WardAutoIntegration {
    Write-WardInfo "Installing automatic ward integration for PowerShell..."

    # 1. PowerShell 프로필 통합
    $result1 = Install-PowerShellIntegration

    # 2. Windows Terminal 통합
    $result2 = Set-WindowsTerminalIntegration

    # 3. 환경 변수 설정
    $result3 = Set-WardEnvironmentVariables

    # 4. VS Code 통합
    $result4 = Set-VSCodePowerShellIntegration

    if ($result1 -or $result2 -or $result3 -or $result4) {
        Write-WardSuccess "PowerShell ward integration installed!"
        Write-WardInfo "Restart PowerShell or run: . `$PROFILE"
    } else {
        Write-WardError "Installation failed"
        return $false
    }

    return $true
}

# 와드 상태 확인
function Get-WardStatus {
    Write-WardInfo "Ward Status for PowerShell"
    Write-Host "Ward Root: $WardRoot" -ForegroundColor $Colors.White
    Write-Host "PowerShell Version: $($PSVersionTable.PSVersion)" -ForegroundColor $Colors.White
    Write-Host "OS: $($env:OS)" -ForegroundColor $Colors.White

    if (Test-WardEnvironment) {
        Write-WardSuccess "Ward environment detected"
    } else {
        Write-WardWarning "Ward environment not detected"
    }

    if (Get-Command bash -ErrorAction SilentlyContinue) {
        Write-WardSuccess "bash available"
    } else {
        Write-WardWarning "bash not available"
    }

    Write-Host "Environment Variables:" -ForegroundColor $Colors.White
    Write-Host "  WARD_ROOT: $($env:WARD_ROOT)" -ForegroundColor $Colors.White
    Write-Host "  WARD_AUTO_MODE: $($env:WARD_AUTO_MODE)" -ForegroundColor $Colors.White
}

# 메인 실행 로직
switch ($Action.ToLower()) {
    "install" {
        Install-WardAutoIntegration
    }
    "activate" {
        Invoke-WardShell
    }
    "status" {
        Get-WardStatus
    }
    "auto" {
        # 자동 모드: 환경 감지
        Ensure-WardEnvironment | Out-Null
    }
    "help" {
        Write-Host "Auto-Ward PowerShell Integration" -ForegroundColor $Colors.Blue
        Write-Host ""
        Write-Host "Usage: .\auto-ward.ps1 [-Action <action>] [-WardRoot <path>]"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  install    Install automatic ward integration"
        Write-Host "  activate   Force activate ward environment"
        Write-Host "  status     Show ward status"
        Write-Host "  auto       Auto-detect and setup (default)"
        Write-Host "  help       Show this help"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\auto-ward.ps1 -Action install"
        Write-Host "  .\auto-ward.ps1 -Action activate"
        Write-Host "  .\auto-ward.ps1 -Action status"
    }
    default {
        Write-WardError "Unknown action: $Action"
        exit 1
    }
}