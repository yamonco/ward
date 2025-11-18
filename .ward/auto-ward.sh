#!/usr/bin/env bash
# .ward/auto-ward.sh - 자동 와드 쉘 통합 시스템
# - 모든 새 쉘 세션을 자동으로 와드 환경으로 통합
# - 코파일럿/사용자 구분 없이 재현성 보장

WARD_ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
WARD_DIR="$(dirname "${BASH_SOURCE[0]}")"

# 자동 감지 설정
WARD_AUTO_MODE="${WARD_AUTO_MODE:-detect}"
WARD_SHELL_TYPE="${WARD_SHELL_TYPE:-$(basename "$SHELL")}"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

_print_info() {
    echo -e "${CYAN}[WARD AUTO]${NC} $1"
}

_print_success() {
    echo -e "${GREEN}[WARD AUTO]${NC} ✓ $1"
}

_print_warning() {
    echo -e "${YELLOW}[WARD AUTO]${NC} ⚠ $1"
}

_print_error() {
    echo -e "${RED}[WARD AUTO]${NC} ✗ $1"
}

# 와드 환경 감지
_is_ward_environment() {
    [[ -n "$WARD_ROOT" && -f "$WARD_ROOT/.ward/guard.sh" ]]
}

# 와드 환경인지 확인하고 없으면 자동으로 설정
_ensure_ward_environment() {
    if _is_ward_environment; then
        return 0
    fi

    # 현재 디렉터리에서부터 와드 루트 찾기
    local current_dir="$(pwd)"
    while [[ "$current_dir" != "/" ]]; do
        if [[ -f "$current_dir/.ward/guard.sh" ]]; then
            export WARD_ROOT="$current_dir"
            export BASH_ENV="$WARD_ROOT/.ward/guard.sh"
            _print_success "Ward environment detected: $WARD_ROOT"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done

    return 1
}

# 쉘 프로필에 와드 통합 추가
_install_shell_integration() {
    local shell_type="$1"
    local profile_file=""

    case "$shell_type" in
        "bash")
            profile_file="$HOME/.bashrc"
            ;;
        "zsh")
            profile_file="$HOME/.zshrc"
            ;;
        "fish")
            profile_file="$HOME/.config/fish/config.fish"
            ;;
        *)
            _print_error "Unsupported shell: $shell_type"
            return 1
            ;;
    esac

    if [[ ! -f "$profile_file" ]]; then
        _print_warning "Profile file not found: $profile_file"
        return 1
    fi

    # 이미 통합되어 있는지 확인
    if grep -q "auto-ward.sh" "$profile_file" 2>/dev/null; then
        _print_info "Ward integration already exists in $profile_file"
        return 0
    fi

    # 통합 코드 추가
    local integration_code="
# === WARD AUTO INTEGRATION ===
if [[ -f \"$WARD_DIR/auto-ward.sh\" ]]; then
    source \"$WARD_DIR/auto-ward.sh\"
fi
# === END WARD AUTO INTEGRATION ===
"

    echo "$integration_code" >> "$profile_file"
    _print_success "Ward integration added to $profile_file"
}

# 자동 와드 쉘 활성화
_activate_ward_shell() {
    if ! _ensure_ward_environment; then
        _print_warning "No ward environment found"
        return 1
    fi

    # 이미 와드 환경이면 추가 설정 없음
    if [[ "$BASH_ENV" == "$WARD_ROOT/.ward/guard.sh" ]]; then
        _print_info "Already in ward environment"
        return 0
    fi

    # 와드 환경으로 전환
    if [[ -x "$WARD_ROOT/ward-shell" ]]; then
        _print_info "Activating ward environment..."
        exec "$WARD_ROOT/ward-shell"
    else
        _print_error "ward-shell not found"
        return 1
    fi
}

# PowerShell 통합 스크립트 생성
_create_powershell_integration() {
    local ps_script="$WARD_DIR/auto-ward.ps1"

    cat > "$ps_script" << 'EOF'
# auto-ward.ps1 - PowerShell 와드 자동 통합
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wardRoot = Split-Path -Parent $scriptDir

function Test-WardEnvironment {
    return (Test-Path "$wardRoot\.ward\guard.sh")
}

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

function Enter-WardEnvironment {
    $wardRoot = Find-WardRoot
    if ($wardRoot) {
        Write-Host "[WARD AUTO] Entering ward environment: $wardRoot" -ForegroundColor Cyan
        $env:WARD_ROOT = $wardRoot
        & "$wardRoot\ward-shell"
    } else {
        Write-Host "[WARD AUTO] No ward environment found" -ForegroundColor Yellow
    }
}

# 자동 와드 환경 감지 및 전환
if (-not $env:WARD_ROOT -or -not (Test-WardEnvironment)) {
    Enter-WardEnvironment
}
EOF

    _print_success "PowerShell integration created: $ps_script"
}

# Git 훅 설정 (자동으로 모든 터미널을 와드 환경으로)
_setup_git_hooks() {
    local hooks_dir="$WARD_ROOT/.git/hooks"

    if [[ ! -d "$hooks_dir" ]]; then
        _print_warning "Not a git repository"
        return 1
    fi

    # post-checkout 훅
    cat > "$hooks_dir/post-checkout" << EOF
#!/bin/bash
# Git post-checkout hook - 자동 와드 환경 설정
if [[ -f ".ward/auto-ward.sh" ]]; then
    source ".ward/auto-ward.sh"
    _ensure_ward_environment
fi
EOF

    chmod +x "$hooks_dir/post-checkout"
    _print_success "Git post-checkout hook installed"
}

# VS Code 통합 설정
_setup_vscode_integration() {
    local vscode_dir="$WARD_ROOT/.vscode"

    mkdir -p "$vscode_dir"

    # VS Code 터미널 설정
    cat > "$vscode_dir/settings.json" << EOF
{
    "terminal.integrated.profiles.linux": {
        "bash": {
            "path": "bash",
            "args": ["--rcfile", ".ward/ward-shell"]
        }
    },
    "terminal.integrated.defaultProfile.linux": "bash"
}
EOF

    _print_success "VS Code integration configured"
}

# 전체 자동 설정 설치
install_auto_ward() {
    _print_info "Installing automatic ward integration..."

    # 1. 쉘 통합 설치
    _install_shell_integration "$WARD_SHELL_TYPE"

    # 2. PowerShell 통합 생성
    _create_powershell_integration

    # 3. Git 훅 설정
    _setup_git_hooks

    # 4. VS Code 통합
    _setup_vscode_integration

    _print_success "Auto-ward installation completed!"
    _print_info "Restart your shell or run: source ~/.bashrc"
}

# 와드 환경 클린업 (배포용)
cleanup_ward_environment() {
    _print_info "Cleaning ward environment for deployment..."

    # 1. 감민 정보 제거
    unset WARD_ROOT 2>/dev/null
    unset BASH_ENV 2>/dev/null

    # 2. 쉘 히스토리에서 와드 관련 제거
    history -c 2>/dev/null

    # 3. 임시 파일 정리
    rm -f /tmp/ward_* 2>/dev/null

    _print_success "Ward environment cleaned"
}

# 와드 환경 배포 (압축)
package_ward_environment() {
    local output_file="${1:-ward-environment.tar.gz}"

    _print_info "Packaging ward environment..."

    # 클린업 먼저 수행
    cleanup_ward_environment

    # 와드 관련 파일들 압축
    tar -czf "$output_file" \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='dist' \
        --exclude='build' \
        .ward/ \
        ward-shell \
        ward 2>/dev/null

    _print_success "Ward environment packaged: $output_file"
}

# 메인 실행 로직
case "${1:-auto}" in
    "install")
        install_auto_ward
        ;;
    "activate")
        _activate_ward_shell
        ;;
    "cleanup")
        cleanup_ward_environment
        ;;
    "package")
        package_ward_environment "$2"
        ;;
    "auto")
        # 자동 모드: 환경 감지 및 활성화
        if [[ "$WARD_AUTO_MODE" == "detect" ]]; then
            _ensure_ward_environment
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Auto-Ward Integration System"
        echo
        echo "Usage: $0 [command] [options]"
        echo
        echo "Commands:"
        echo "  install           Install automatic ward integration"
        echo "  activate          Force activate ward environment"
        echo "  cleanup          Clean ward environment for deployment"
        echo "  package [file]   Package ward environment"
        echo "  auto             Auto-detect and setup (default)"
        echo "  help             Show this help"
        echo
        echo "Environment Variables:"
        echo "  WARD_AUTO_MODE   auto|detect|manual (default: detect)"
        echo "  WARD_SHELL_TYPE  bash|zsh|fish|powershell"
        ;;
    *)
        _print_error "Unknown command: $1"
        exit 1
        ;;
esac