#!/usr/bin/env bash
# .ward/ward-auth.sh - 와드 패스워드 기반 인증 시스템
# - 와드 폴더 내에 저장된 패스워드로 검증
# - 배포/클린업 권한 관리

WARD_ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
WARD_DIR="$(dirname "${BASH_SOURCE[0]}")"
WARD_AUTH_FILE="$WARD_DIR/.ward_auth"
WARD_SESSION_FILE="$WARD_DIR/.ward_session"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

_print_auth() {
    echo -e "${BLUE}[WARD AUTH]${NC} $1"
}

_print_success() {
    echo -e "${GREEN}[WARD AUTH]${NC} ✓ $1"
}

_print_error() {
    echo -e "${RED}[WARD AUTH]${NC} ✗ $1"
}

_print_warning() {
    echo -e "${YELLOW}[WARD AUTH]${NC} ⚠ $1"
}

# 간단한 해시 함수 (단방향)
_hash_password() {
    local password="$1"
    local salt="${2:-ward_default_salt}"
    echo -n "$password$salt" | sha256sum | cut -d' ' -f1
}

# 패스워드 설정
set_ward_password() {
    local password="$1"
    local confirm="$2"

    if [[ -z "$password" ]]; then
        read -s -p "Enter new ward password: " password
        echo
        read -s -p "Confirm password: " confirm
        echo
    fi

    if [[ "$password" != "$confirm" ]]; then
        _print_error "Passwords do not match"
        return 1
    fi

    if [[ ${#password} -lt 8 ]]; then
        _print_error "Password must be at least 8 characters"
        return 1
    fi

    local hashed_password
    hashed_password=$(_hash_password "$password")

    echo "$hashed_password" > "$WARD_AUTH_FILE"
    chmod 600 "$WARD_AUTH_FILE"

    _print_success "Ward password set successfully"
    return 0
}

# 패스워드 검증
verify_ward_password() {
    local password="$1"
    local hashed_password

    if [[ ! -f "$WARD_AUTH_FILE" ]]; then
        _print_warning "No ward password set. Creating default..."
        set_ward_password "ward123" "ward123"
        return $?
    fi

    hashed_password=$(cat "$WARD_AUTH_FILE")
    local computed_hash
    computed_hash=$(_hash_password "$password")

    [[ "$hashed_password" == "$computed_hash" ]]
}

# 세션 생성
create_ward_session() {
    local session_token
    session_token=$(date +%s | sha256sum | cut -d' ' -f1)
    local expiry_time
    expiry_time=$(($(date +%s) + 3600))  # 1시간 유효

    echo "$session_token:$expiry_time" > "$WARD_SESSION_FILE"
    chmod 600 "$WARD_SESSION_FILE"

    _print_success "Session created (valid for 1 hour)"
    echo "Session token: $session_token"
}

# 세션 검증
verify_ward_session() {
    local token="$1"

    if [[ ! -f "$WARD_SESSION_FILE" ]]; then
        return 1
    fi

    local session_data
    session_data=$(cat "$WARD_SESSION_FILE")
    local stored_token
    stored_token=$(echo "$session_data" | cut -d':' -f1)
    local expiry_time
    expiry_time=$(echo "$session_data" | cut -d':' -f2)
    local current_time
    current_time=$(date +%s)

    # 토큰 일치 및 만료 확인
    if [[ "$token" == "$stored_token" && "$current_time" -lt "$expiry_time" ]]; then
        return 0
    else
        # 만료된 세션 정리
        rm -f "$WARD_SESSION_FILE"
        return 1
    fi
}

# 인증 프롬프트
prompt_ward_auth() {
    local operation="$1"
    local password session_token

    _print_auth "Authentication required for: $operation"

    # 세션 토큰 확인
    read -p "Enter session token (or press Enter for password): " session_token

    if [[ -n "$session_token" ]]; then
        if verify_ward_session "$session_token"; then
            _print_success "Session authenticated"
            return 0
        else
            _print_error "Invalid or expired session token"
        fi
    fi

    # 패스워드 인증
    read -s -p "Enter ward password: " password
    echo

    if verify_ward_password "$password"; then
        _print_success "Authenticated successfully"

        # 새 세션 제공
        create_ward_session
        return 0
    else
        _print_error "Authentication failed"
        return 1
    fi
}

# 권한 확인
check_ward_permission() {
    local operation="$1"
    local auto_auth="${2:-false}"

    # 관리자 작업 목록
    local admin_operations=("deploy" "cleanup" "package" "export" "import")

    # 관리자 작업이 아니면 통과
    if [[ ! " ${admin_operations[@]} " =~ " ${operation} " ]]; then
        return 0
    fi

    # 자동 인증 모드이면 환경 변수 확인
    if [[ "$auto_auth" == "true" && -n "$WARD_AUTO_AUTH" ]]; then
        if verify_ward_password "$WARD_AUTO_AUTH"; then
            return 0
        fi
    fi

    # 인증 프롬프트
    prompt_ward_auth "$operation"
}

# 와드 환경 배포 (인증 필요)
deploy_ward_environment() {
    local target_dir="$1"
    local password="$2"

    if check_ward_permission "deploy"; then
        _print_auth "Deploying ward environment to: $target_dir"

        # 배포 전 유효성 검사
        if ! bash -n "$WARD_DIR/guard.sh"; then
            _print_error "Guard script has syntax errors"
            return 1
        fi

        # 대상 디렉터리 생성
        mkdir -p "$target_dir"

        # 필수 파일 복사
        cp -r "$WARD_DIR" "$target_dir/"
        cp "$WARD_ROOT/ward-shell" "$target_dir/"
        cp "$WARD_ROOT/ward" "$target_dir/" 2>/dev/null || true

        # 권한 설정
        chmod +x "$target_dir/ward-shell"
        chmod +x "$target_dir/ward.sh"
        chmod +x "$target_dir/auto-ward.sh"

        # 인증 파일 복사 (선택적)
        if [[ "$WARD_INCLUDE_AUTH" == "true" ]]; then
            cp "$WARD_AUTH_FILE" "$target_dir/.ward/" 2>/dev/null || true
            cp "$WARD_SESSION_FILE" "$target_dir/.ward/" 2>/dev/null || true
        fi

        _print_success "Ward environment deployed to $target_dir"
        return 0
    else
        return 1
    fi
}

# 와드 환경 클린업 (인증 필요)
cleanup_ward_environment() {
    local clean_level="${1:-standard}"  # standard|deep|secure

    if check_ward_permission "cleanup"; then
        _print_auth "Cleaning ward environment (level: $clean_level)"

        case "$clean_level" in
            "standard")
                # 기본 클린업
                rm -f "$WARD_SESSION_FILE"
                history -c 2>/dev/null
                unset WARD_ROOT 2>/dev/null
                ;;
            "deep")
                # 깊은 클린업
                rm -f "$WARD_SESSION_FILE"
                rm -f "$WARD_AUTH_FILE"
                history -c 2>/dev/null
                unset WARD_ROOT WARD_AUTO_AUTH 2>/dev/null
                find "$WARD_DIR" -name "*.tmp" -delete 2>/dev/null
                ;;
            "secure")
                # 보안 클린업 (모든 민감 정보)
                rm -f "$WARD_SESSION_FILE"
                shred -u "$WARD_AUTH_FILE" 2>/dev/null || rm -f "$WARD_AUTH_FILE"
                history -c 2>/dev/null
                unset WARD_ROOT WARD_AUTO_AUTH 2>/dev/null
                find "$WARD_DIR" -name "*.tmp" -delete 2>/dev/null
                find "$WARD_DIR" -name "*ward*" -type f -exec shred -u {} \; 2>/dev/null
                ;;
        esac

        _print_success "Ward environment cleaned (level: $clean_level)"
        return 0
    else
        return 1
    fi
}

# 와드 환경 내보내기 (인증 필요)
export_ward_environment() {
    local export_file="$1"
    local include_password="${2:-false}"

    if check_ward_permission "export"; then
        _print_auth "Exporting ward environment to: $export_file"

        local temp_dir="/tmp/ward_export_$$"
        mkdir -p "$temp_dir"

        # 파일 복사
        cp -r "$WARD_DIR" "$temp_dir/"
        cp "$WARD_ROOT/ward-shell" "$temp_dir/"
        cp "$WARD_ROOT/ward" "$temp_dir/" 2>/dev/null || true

        # 패스워드 포함 옵션
        if [[ "$include_password" == "true" ]]; then
            cp "$WARD_AUTH_FILE" "$temp_dir/.ward/" 2>/dev/null || true
        fi

        # 압축
        tar -czf "$export_file" -C "$temp_dir" .
        rm -rf "$temp_dir"

        _print_success "Ward environment exported to: $export_file"
        return 0
    else
        return 1
    fi
}

# 인증 상태 확인
ward_auth_status() {
    _print_auth "Ward Authentication Status"
    echo

    # 패스워드 설정 여부
    if [[ -f "$WARD_AUTH_FILE" ]]; then
        _print_success "Password is set"
    else
        _print_warning "No password set (using default)"
    fi

    # 세션 상태
    if [[ -f "$WARD_SESSION_FILE" ]]; then
        local session_data
        session_data=$(cat "$WARD_SESSION_FILE")
        local expiry_time
        expiry_time=$(echo "$session_data" | cut -d':' -f2)
        local current_time
        current_time=$(date +%s)
        local remaining
        remaining=$((expiry_time - current_time))

        if [[ $remaining -gt 0 ]]; then
            _print_success "Active session ($(($remaining / 60)) minutes remaining)"
        else
            _print_warning "Session expired"
        fi
    else
        _print_warning "No active session"
    fi

    echo
    echo "Environment variables:"
    echo "  WARD_AUTO_AUTH: ${WARD_AUTO_AUTH:-<not set>}"
    echo "  WARD_INCLUDE_AUTH: ${WARD_INCLUDE_AUTH:-<not set>}"
}

# 메인 실행
case "${1:-status}" in
    "set-password")
        set_ward_password "$2" "$3"
        ;;
    "verify")
        verify_ward_password "$2" && _print_success "Password valid" || _print_error "Password invalid"
        ;;
    "session")
        create_ward_session
        ;;
    "deploy")
        deploy_ward_environment "$2" "$3"
        ;;
    "cleanup")
        cleanup_ward_environment "$2"
        ;;
    "export")
        export_ward_environment "$2" "$3"
        ;;
    "status")
        ward_auth_status
        ;;
    "help"|"-h"|"--help")
        echo "Ward Authentication System"
        echo
        echo "Usage: $0 <command> [options]"
        echo
        echo "Commands:"
        echo "  set-password [pass] [confirm]  Set ward password"
        echo "  verify <password>              Verify password"
        echo "  session                        Create new session"
        echo "  deploy <target> [password]    Deploy ward environment"
        echo "  cleanup [level]               Clean ward environment"
        echo "  export <file> [include-pass]  Export ward environment"
        echo "  status                         Show authentication status"
        echo "  help                           Show this help"
        echo
        echo "Environment Variables:"
        echo "  WARD_AUTO_AUTH      Auto-authentication password"
        echo "  WARD_INCLUDE_AUTH   Include auth in exports"
        ;;
    *)
        _print_error "Unknown command: $1"
        exit 1
        ;;
esac