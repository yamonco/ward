#!/usr/bin/env bash
# .ward/ward.sh - 와드 시스템 유틸리티

WARD_ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

_print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

_print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

_print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

_print_error() {
    echo -e "${RED}✗ $1${NC}"
}

_print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# 와드 파일 찾기
find_ward_files() {
    find "$WARD_ROOT" -name ".ward" -type f 2>/dev/null | sort
}

# 경로에 적용되는 와드 정책 찾기
get_policy_for_path() {
    local path="$1"
    local dir

    if [ -d "$path" ]; then
        dir="$path"
    else
        dir=$(dirname "$path")
    fi

    # 절대 경로로 변환
    dir=$(cd "$dir" && pwd)

    while [ "$dir" != "$WARD_ROOT" ] && [ "$dir" != "/" ]; do
        if [ -f "$dir/.ward" ]; then
            echo "$dir/.ward"
        fi
        dir=$(dirname "$dir")
    done

    # 루트 와드 확인
    if [ -f "$WARD_ROOT/.ward/.ward" ]; then
        echo "$WARD_ROOT/.ward/.ward"
    fi
}

# 와드 파일 파싱
parse_ward() {
    local file="$1"
    local section="$2"

    if [ ! -f "$file" ]; then
        return 1
    fi

    case "$section" in
        "whitelist")
            grep "^@whitelist:" "$file" 2>/dev/null | sed 's/^@whitelist: //'
            ;;
        "blacklist")
            grep "^@blacklist:" "$file" 2>/dev/null | sed 's/^@blacklist: //'
            ;;
        "lock_new_dirs")
            grep "^@lock_new_dirs:" "$file" 2>/dev/null | sed 's/^@lock_new_dirs: //'
            ;;
        "description")
            grep "^@description:" "$file" 2>/dev/null | sed 's/^@description: //'
            ;;
        "prompt")
            grep "^@prompt:" "$file" 2>/dev/null | sed 's/^@prompt: //'
            ;;
        "allow_comments")
            grep "^@allow_comments:" "$file" 2>/dev/null | sed 's/^@allow_comments: //'
            ;;
        "max_comments")
            grep "^@max_comments:" "$file" 2>/dev/null | sed 's/^@max_comments: //'
            ;;
        "comment_prompt")
            grep "^@comment_prompt:" "$file" 2>/dev/null | sed 's/^@comment_prompt: //'
            ;;
    esac
}

# 상태 확인
ward_status() {
    _print_header "WARD SYSTEM STATUS"

    echo -e "${CYAN}Root Directory:${NC} $WARD_ROOT"
    echo

    local wards
    wards=$(find_ward_files)

    if [ -z "$wards" ]; then
        _print_warning "No .ward files found"
        return 1
    fi

    local count
    count=$(echo "$wards" | wc -l)
    _print_info "Found $count .ward file(s):"
    echo "$wards" | while read -r file; do
        local rel_path="${file#$WARD_ROOT/}"
        echo -e "  ${CYAN}•${NC} $rel_path"
    done
    echo

    _print_header "POLICY SUMMARY"
    echo "$wards" | while read -r file; do
        if [ -n "$file" ]; then
            local rel_path="${file#$WARD_ROOT/}"
            echo -e "${YELLOW}$rel_path${NC}"

            local whitelist
            whitelist=$(parse_ward "$file" "whitelist")
            local blacklist
            blacklist=$(parse_ward "$file" "blacklist")
            local lock_new
            lock_new=$(parse_ward "$file" "lock_new_dirs")
            local allow_comments
            allow_comments=$(parse_ward "$file" "allow_comments")
            local max_comments
            max_comments=$(parse_ward "$file" "max_comments")

            echo -e "  Whitelist: ${whitelist:-<none>}"
            echo -e "  Blacklist: ${blacklist:-<none>}"
            echo -e "  Lock New Dirs: ${lock_new:-<unset>}"
            echo -e "  Allow Comments: ${allow_comments:-<unset>}"
            echo -e "  Max Comments: ${max_comments:-<unset>}"
            echo
        fi
    done
}

# 경로 확인
ward_check() {
    local path="${1:-$(pwd)}"

    _print_header "POLICY FOR PATH: $path"

    local policies
    policies=$(get_policy_for_path "$path")

    if [ -z "$policies" ]; then
        _print_info "No ward policies apply to this path"
        return 0
    fi

    _print_info "Applicable ward policies (parent → child):"
    echo "$policies" | while read -r file; do
        if [ -n "$file" ]; then
            local rel_path="${file#$WARD_ROOT/}"
            echo -e "  ${CYAN}•${NC} $rel_path"

            local description
            description=$(parse_ward "$file" "description")
            local prompt
            prompt=$(parse_ward "$file" "prompt")
            local whitelist
            whitelist=$(parse_ward "$file" "whitelist")
            local allow_comments
            allow_comments=$(parse_ward "$file" "allow_comments")
            local comment_prompt
            comment_prompt=$(parse_ward "$file" "comment_prompt")

            [ -n "$description" ] && echo -e "    Description: $description"
            [ -n "$prompt" ] && echo -e "    Prompt: $prompt"
            [ -n "$whitelist" ] && echo -e "    Whitelist: $whitelist"
            [ -n "$allow_comments" ] && echo -e "    Allow Comments: $allow_comments"
            [ -n "$comment_prompt" ] && echo -e "    Comment Prompt: $comment_prompt"
            echo
        fi
    done
}

# 유효성 검사
ward_validate() {
    _print_header "VALIDATING WARD POLICIES"

    local has_errors=0
    local wards
    wards=$(find_ward_files)

    echo "$wards" | while read -r file; do
        if [ -n "$file" ]; then
            local rel_path="${file#$WARD_ROOT/}"
            echo -n "Validating $rel_path... "

            # 기본 형식 검사
            if grep -q "^@[a-zA-Z_][a-zA-Z0-9_]*:" "$file"; then
                _print_success "OK"
            else
                _print_error "Invalid format"
                has_errors=1
            fi
        fi
    done

    if [ $has_errors -eq 0 ]; then
        _print_success "All ward files are valid!"
        return 0
    else
        _print_error "Found validation errors"
        return 1
    fi
}

# 디버그 정보
ward_debug() {
    local path="${1:-$(pwd)}"

    _print_header "WARD DEBUG INFO"
    echo -e "${CYAN}Target Path:${NC} $path"
    echo -e "${CYAN}Current User:${NC} $(whoami)"
    echo -e "${CYAN}Current Shell:${NC} $0"
    echo

    # 가드 스크립트 상태
    local guard_script="$WARD_ROOT/.ward/guard.sh"
    if [ -f "$guard_script" ]; then
        _print_success "Guard script exists: $guard_script"
        if bash -n "$guard_script" 2>/dev/null; then
            _print_success "Guard script syntax is valid"
        else
            _print_error "Guard script has syntax errors!"
            bash -n "$guard_script"
        fi
    else
        _print_error "Guard script missing: $guard_script"
    fi
    echo

    # ward-shell 상태
    local ward_shell="$WARD_ROOT/ward-shell"
    if [ -f "$ward_shell" ]; then
        _print_success "Ward shell exists: $ward_shell"
        if [ -x "$ward_shell" ]; then
            _print_success "Ward shell is executable"
        else
            _print_warning "Ward shell is not executable"
        fi
    else
        _print_error "Ward shell missing: $ward_shell"
    fi
    echo

    # 환경 변수
    echo -e "${CYAN}Environment Variables:${NC}"
    echo "WARD_ROOT=${WARD_ROOT:-<unset>}"
    echo "BASH_ENV=${BASH_ENV:-<unset>}"
    echo

    # 적용되는 정책
    ward_check "$path"
}

# 테스트
ward_test() {
    local cmd="$1"
    local path="$2"

    _print_header "TESTING COMMAND: $cmd on $path"

    if [ -z "$cmd" ]; then
        _print_error "Command required"
        echo "Usage: $0 test <command> <path>"
        return 1
    fi

    echo -e "${CYAN}Testing with ward environment...${NC}"

    # ward-shell로 테스트
    if [ -x "$WARD_ROOT/ward-shell" ]; then
        local full_cmd="cd '$WARD_ROOT' && $cmd"
        echo -e "${CYAN}Executing: $WARD_ROOT/ward-shell -c \"$full_cmd\"${NC}"
        if "$WARD_ROOT/ward-shell" -c "$full_cmd" 2>&1; then
            _print_success "Command allowed"
        else
            _print_error "Command blocked or failed"
        fi
    else
        _print_error "ward-shell not found"
        return 1
    fi
}

# 댓글 관리 유틸리티
ward_comments() {
    local path="${1:-$(pwd)}"
    local action="$2"

    case "$action" in
        "count"|"")
            _print_header "COMMENT STATUS FOR: $path"

            local policies
            policies=$(get_policy_for_path "$path")

            if [ -z "$policies" ]; then
                _print_info "No ward policies apply to this path"
                return 0
            fi

            echo "$policies" | while read -r file; do
                if [ -n "$file" ]; then
                    local rel_path="${file#$WARD_ROOT/}"
                    echo -e "${YELLOW}$rel_path${NC}"

                    local allow_comments
                    allow_comments=$(parse_ward "$file" "allow_comments")
                    local max_comments
                    max_comments=$(parse_ward "$file" "max_comments")

                    # 현재 댓글 개수 계산
                    local current_comments
                    current_comments=$(grep "^#" "$file" 2>/dev/null | grep -v "^# @" | wc -l)

                    echo -e "  Allow Comments: ${allow_comments:-<unset>}"
                    echo -e "  Max Comments: ${max_comments:-<unlimited>}"
                    echo -e "  Current Comments: $current_comments"

                    if [ -n "$max_comments" ] && [ "$allow_comments" = "true" ]; then
                        local remaining=$((max_comments - current_comments))
                        if [ $remaining -gt 0 ]; then
                            echo -e "  ${GREEN}Comments available: $remaining${NC}"
                        else
                            echo -e "  ${RED}Comment limit reached${NC}"
                        fi
                    fi
                    echo
                fi
            done
            ;;
        "show")
            _print_header "COMMENTS FOR: $path"

            local policies
            policies=$(get_policy_for_path "$path")

            echo "$policies" | while read -r file; do
                if [ -n "$file" ]; then
                    local rel_path="${file#$WARD_ROOT/}"
                    echo -e "${YELLOW}$rel_path${NC}"

                    grep "^#" "$file" 2>/dev/null | grep -v "^# @" | while read -r comment; do
                        echo -e "  ${CYAN}•${NC} $comment"
                    done
                    echo
                fi
            done
            ;;
        *)
            _print_error "Unknown comment action: $action"
            echo "Usage: $0 comments [path] [count|show]"
            return 1
            ;;
    esac
}

# 도움말
ward_help() {
    _print_header "WARD UTILITY HELP"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  status              Show ward system status and all policies"
    echo "  check [path]        Show policies applied to specific path"
    echo "  validate            Validate all ward file formats"
    echo "  debug [path]        Show debug information for path"
    echo "  test <cmd> <path>   Test if command is allowed on path"
    echo "  comments [path] [action]  Manage comments (count, show)"
    echo "  install             Install automatic shell integration"
    echo "  auth [action]       Manage authentication (status, set-password)"
    echo "  deploy <target>     Deploy ward environment (auth required)"
    echo "  cleanup [level]     Clean ward environment (auth required)"
    echo "  export <file>       Export ward environment (auth required)"
    echo "  help                Show this help"
    echo
    echo "Examples:"
    echo "  $0 status                    # Show all ward policies"
    echo "  $0 check frontend/src        # Check policies for frontend/src"
    echo "  $0 test mkdir frontend/test  # Test mkdir command"
    echo "  $0 validate                  # Validate all ward files"
    echo "  $0 comments frontend count   # Show comment status"
    echo "  $0 comments frontend show    # Show all comments"
    echo "  $0 install                   # Install automatic integration"
    echo "  $0 auth status               # Check authentication status"
    echo "  $0 auth set-password         # Set new password"
    echo "  $0 deploy /tmp/ward-copy     # Deploy to another location"
    echo "  $0 cleanup standard          # Clean environment"
    echo "  $0 export ward-backup.tar.gz # Export for backup"
    echo
    echo "Ward Shell Commands (inside ward-shell):"
    echo "  handle <cmd> [path]          Handle operations with AI prompts"
    echo "  comment <text>               Add comment to .ward file"
}

# 메인 처리
case "${1:-help}" in
    "status")
        ward_status
        ;;
    "check")
        ward_check "$2"
        ;;
    "validate")
        ward_validate
        ;;
    "debug")
        ward_debug "$2"
        ;;
    "test")
        ward_test "$2" "$3"
        ;;
    "comments")
        ward_comments "$2" "$3"
        ;;
    "install")
        if [ -x "$WARD_ROOT/.ward/auto-ward.sh" ]; then
            "$WARD_ROOT/.ward/auto-ward.sh" install
        else
            _print_error "auto-ward.sh not found"
        fi
        ;;
    "auth")
        if [ -x "$WARD_ROOT/.ward/ward-auth.sh" ]; then
            "$WARD_ROOT/.ward/ward-auth.sh" "${2:-status}"
        else
            _print_error "ward-auth.sh not found"
        fi
        ;;
    "deploy")
        if [ -x "$WARD_ROOT/.ward/ward-auth.sh" ]; then
            "$WARD_ROOT/.ward/ward-auth.sh" deploy "$2" "$3"
        else
            _print_error "ward-auth.sh not found"
        fi
        ;;
    "cleanup")
        if [ -x "$WARD_ROOT/.ward/ward-auth.sh" ]; then
            "$WARD_ROOT/.ward/ward-auth.sh" cleanup "$2"
        else
            _print_error "ward-auth.sh not found"
        fi
        ;;
    "export")
        if [ -x "$WARD_ROOT/.ward/ward-auth.sh" ]; then
            "$WARD_ROOT/.ward/ward-auth.sh" export "$2" "$3"
        else
            _print_error "ward-auth.sh not found"
        fi
        ;;
    "help"|"-h"|"--help")
        ward_help
        ;;
    *)
        _print_error "Unknown command: $1"
        echo
        ward_help
        exit 1
        ;;
esac