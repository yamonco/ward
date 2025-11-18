#!/usr/bin/env bash
# ward.sh - Simplified Ward Security CLI v2.0
# Clean, intuitive interface inspired by spekit

set -euo pipefail

# Ward configuration
readonly WARD_VERSION="2.0.0"
readonly WARD_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Utility functions
print_msg() {
    local color="${1:-NC}"
    shift
    echo -e "${color}$*${NC}"
}

success() { print_msg "$GREEN" "✅ $*"; }
error() { print_msg "$RED" "❌ $*" >&2; }
warning() { print_msg "$YELLOW" "⚠️ $*"; }
info() { print_msg "$BLUE" "ℹ️ $*"; }

# Legacy compatibility
_print_header() { print_msg "$BLUE" "=== $1 ==="; }
_print_success() { success "$*"; }
_print_warning() { warning "$*"; }
_print_error() { error "$*" >&2; }
_print_info() { info "$*"; }

# 와드 파일 찾기
find_ward_files() {
    find "$WARD_DIR" -name ".ward" -type f 2>/dev/null | sort
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

    while [ "$dir" != "$WARD_DIR" ] && [ "$dir" != "/" ]; do
        if [ -f "$dir/.ward" ]; then
            echo "$dir/.ward"
        fi
        dir=$(dirname "$dir")
    done

    # 루트 와드 확인
    if [ -f "$WARD_DIR/.ward" ]; then
        echo "$WARD_DIR/.ward"
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

    echo -e "${CYAN}Root Directory:${NC} $WARD_DIR"
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
        local rel_path="${file#$WARD_DIR/}"
        echo -e "  ${CYAN}•${NC} $rel_path"
    done
    echo

    _print_header "POLICY SUMMARY"
    echo "$wards" | while read -r file; do
        if [ -n "$file" ]; then
            local rel_path="${file#$WARD_DIR/}"
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
            local rel_path="${file#$WARD_DIR/}"
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
            local rel_path="${file#$WARD_DIR/}"
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
    local guard_script="$WARD_DIR/.ward/guard.sh"
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
    local ward_shell="$WARD_DIR/ward-shell"
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
    echo "WARD_DIR=${WARD_DIR:-<unset>}"
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
    if [ -x "$WARD_DIR/ward-shell" ]; then
        local full_cmd="cd '$WARD_DIR' && $cmd"
        echo -e "${CYAN}Executing: $WARD_DIR/ward-shell -c \"$full_cmd\"${NC}"
        if "$WARD_DIR/ward-shell" -c "$full_cmd" 2>&1; then
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
                    local rel_path="${file#$WARD_DIR/}"
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
                    local rel_path="${file#$WARD_DIR/}"
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

# Check dependencies
check_ward_installation() {
    if [[ ! -d "$WARD_DIR" ]]; then
        error "Ward installation not found at $WARD_DIR"
        info "Please run ./setup-ward.sh first"
        exit 1
    fi
}

# Command functions
cmd_status() {
    info "Ward Security System v$WARD_VERSION"
    echo
    info "🔍 System Status:"

    # Check installation
    if [[ -d "$HOME/.ward" ]]; then
        success "Ward installed locally at ~/.ward"
    else
        warning "Ward not installed in home directory"
    fi

    # Check MCP server
    if [[ -f "$HOME/.ward/mcp/mcp_server.py" ]]; then
        success "MCP server available"
    else
        warning "MCP server not found"
    fi

    echo
    info "📍 Installation directory: $WARD_DIR"
    info "🏠 Home directory: $HOME"

    # Show ward status using legacy function for compatibility
    echo
    ward_status
}

cmd_init() {
    local target_dir="${1:-$(pwd)}"

    info "🚀 Initializing Ward in: $target_dir"

    # Create directory if it doesn't exist
    mkdir -p "$target_dir"

    # Create basic .ward file
    cat > "$target_dir/.ward" << 'EOF'
# Ward Security Configuration
@description: AI-Assisted Development Project
@whitelist: ls cat pwd echo grep sed awk git python npm node code vim
@blacklist: rm -rf / sudo su chmod chown docker kubectl
@allow_comments: true
@max_comments: 5
@comment_prompt: "Explain changes from a security perspective"
EOF

    success "Ward initialized in $target_dir"
    info "Edit $target_dir/.ward to customize policies"
}

cmd_check() {
    local target="${1:-$(pwd)}"

    info "🔍 Checking Ward policies for: $target"
    echo

    if [[ -f "$target/.ward" ]]; then
        success "✓ Ward policy found"
        echo
        info "📋 Policy Summary:"
        while IFS= read -r line; do
            if [[ "$line" =~ ^@description: ]]; then
                echo "  📝 $line"
            elif [[ "$line" =~ ^@whitelist: ]]; then
                echo "  ✅ Allowed: $line"
            elif [[ "$line" =~ ^@blacklist: ]]; then
                echo "  ❌ Blocked: $line"
            fi
        done < "$target/.ward"
    else
        warning "⚠ No .ward policy found in $target"
        info "Use 'ward init' to create a policy"
    fi

    # Use legacy check function for detailed analysis
    echo
    ward_check "$target"
}

cmd_mcp_status() {
    info "🤖 MCP Server Status"
    echo

    if [[ -f "$HOME/.ward/mcp/mcp_server.py" ]]; then
        success "✅ MCP server installed"

        # Test if Python can import it
        if python3 -c "import sys; sys.path.append('$HOME/.ward/mcp'); import mcp_server" 2>/dev/null; then
            success "✅ MCP server functional"
        else
            warning "⚠ MCP server import test failed"
        fi
    else
        error "❌ MCP server not found"
        info "Run ./setup-ward.sh to install MCP components"
    fi
}

cmd_mcp_test() {
    info "🧪 Testing MCP Server"

    if [[ -f "$HOME/.ward/mcp/mcp_server.py" ]]; then
        echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | python3 "$HOME/.ward/mcp/mcp_server.py" --stdio 2>/dev/null && \
            success "✅ MCP server responding correctly" || \
            error "❌ MCP server test failed"
    else
        error "❌ MCP server not found"
    fi
}

cmd_configure_claude() {
    local script="$WARD_DIR/configure-claude-desktop.sh"

    if [[ -x "$script" ]]; then
        info "🔧 Configuring Claude Desktop..."
        "$script"
    else
        error "❌ Claude Desktop configuration script not found"
        return 1
    fi
}

cmd_help() {
    cat << 'EOF'
🛡️  Ward Security System - AI-Powered Terminal Protection

USAGE:
    ward [COMMAND] [OPTIONS]

CORE COMMANDS:
    status              Show Ward system status
    init [path]         Initialize Ward in directory (default: current)
    check [path]        Check security policies for path
    validate            Validate security policies
    help                Show this help message
    version             Show version information

MCP INTEGRATION:
    mcp-status          Check MCP server status
    mcp-test            Test MCP server functionality
    configure-claude    Configure Claude Desktop integration

ADVANCED COMMANDS:
    favorites           Manage favorite directories
    plant <path>        Plant Ward protection
    info <path>         Get Ward information
    search <query>      Search indexed folders
    bookmark            Manage bookmarks
    recent              Show recent access
    debug [path]        Show debug information
    comments [path] [action]  Manage comments

EXAMPLES:
    ward                           # Show status
    ward init                      # Initialize in current directory
    ward check frontend/src        # Check policies for frontend/src
    ward mcp-status                # Check MCP server
    ward search "config"           # Search for configuration files

For detailed help on specific commands:
    ward favorites --help
    ward bookmark --help
    ward search --help

🤖 AI Integration:
    Ward works seamlessly with Claude, Copilot, and ChatGPT through MCP.
    Use 'configure-claude' to set up AI assistant integration.
EOF
}

cmd_version() {
    echo "Ward Security System v$WARD_VERSION"
    echo "AI-Powered Terminal Protection"
}

# Advanced commands (Python CLI integration)
cmd_advanced() {
    local python_cli="$WARD_DIR/src/ward_security/cli.py"

    if [[ -f "$python_cli" && -x "$python_cli" ]]; then
        python3 "$python_cli" "$@"
    else
        error "Advanced CLI not available"
        return 1
    fi
}

# Main execution
main() {
    check_ward_installation

    # Simple command parsing
    case "${1:-status}" in
        "status"|"")
            cmd_status
            ;;
        "init")
            cmd_init "${2:-}"
            ;;
        "check")
            cmd_check "${2:-}"
            ;;
        "validate")
            ward_validate
            ;;
        "mcp-status")
            cmd_mcp_status
            ;;
        "mcp-test")
            cmd_mcp_test
            ;;
        "configure-claude")
            cmd_configure_claude
            ;;
        "favorites"|"plant"|"info"|"search"|"bookmark"|"recent")
            # Forward to Python CLI for advanced commands
            cmd_advanced "$@"
            ;;
        "debug")
            ward_debug "${2:-}"
            ;;
        "comments")
            ward_comments "${2:-}" "${3:-}"
            ;;
        "help"|"-h"|"--help")
            cmd_help
            ;;
        "version"|"-v"|"--version")
            cmd_version
            ;;
        "install")
            if [ -x "$WARD_DIR/.ward/auto-ward.sh" ]; then
                "$WARD_DIR/.ward/auto-ward.sh" install
            else
                error "auto-ward.sh not found"
            fi
            ;;
        "auth")
            if [ -x "$WARD_DIR/.ward/ward-auth.sh" ]; then
                "$WARD_DIR/.ward/ward-auth.sh" "${2:-status}"
            else
                error "ward-auth.sh not found"
            fi
            ;;
        "deploy")
            if [ -x "$WARD_DIR/.ward/ward-auth.sh" ]; then
                "$WARD_DIR/.ward/ward-auth.sh" deploy "$2" "$3"
            else
                error "ward-auth.sh not found"
            fi
            ;;
        "cleanup")
            if [ -x "$WARD_DIR/.ward/ward-auth.sh" ]; then
                "$WARD_DIR/.ward/ward-auth.sh" cleanup "$2"
            else
                error "ward-auth.sh not found"
            fi
            ;;
        "export")
            if [ -x "$WARD_DIR/.ward/ward-auth.sh" ]; then
                "$WARD_DIR/.ward/ward-auth.sh" export "$2" "$3"
            else
                error "ward-auth.sh not found"
            fi
            ;;
        *)
            error "Unknown command: $1"
            echo
            cmd_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"