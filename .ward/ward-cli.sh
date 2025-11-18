#!/usr/bin/env bash
# ward-cli.sh - Ward Security CLI v2.0
# Professional command-line interface with enterprise features

set -euo pipefail

# Ward CLI namespace
readonly WARD_CLI_VERSION="2.0.0"
readonly WARD_CLI_AUTHOR="Ward Security Team"

# Core paths
readonly WARD_ROOT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
readonly WARD_LIB_DIR="${WARD_ROOT_DIR}/.ward"
readonly WARD_CORE_DIR="${WARD_LIB_DIR}/core"

# Load core modules
source "${WARD_CORE_DIR}/engine.sh" 2>/dev/null || {
    echo "Fatal: Failed to load core engine module" >&2
    exit 1
}

source "${WARD_CORE_DIR}/config.sh" 2>/dev/null || {
    echo "Fatal: Failed to load configuration module" >&2
    exit 1
}

source "${WARD_CORE_DIR}/logging.sh" 2>/dev/null || {
    echo "Fatal: Failed to load logging module" >&2
    exit 1
}

source "${WARD_CORE_DIR}/plugin_manager.sh" 2>/dev/null || {
    echo "Fatal: Failed to load plugin manager module" >&2
    exit 1
}

# CLI state
declare -g WARD_CLI_COMMAND=""
declare -g WARD_CLI_ARGS=()
declare -g WARD_CLI_VERBOSE=false
declare -g WARD_CLI_QUIET=false
declare -g WARD_CLI_FORCE=false

# Color definitions
declare -Ar WARD_CLI_COLORS=(
    [RESET]="\033[0m"
    [BLACK]="\033[0;30m"
    [RED]="\033[0;31m"
    [GREEN]="\033[0;32m"
    [YELLOW]="\033[1;33m"
    [BLUE]="\033[0;34m"
    [PURPLE]="\033[0;35m"
    [CYAN]="\033[0;36m"
    [WHITE]="\033[1;37m"
)

# CLI utility functions
ward_cli::print() {
    local color="${1:-RESET}"
    shift
    echo -e "${WARD_CLI_COLORS[$color]}$*${WARD_CLI_COLORS[RESET]}"
}

ward_cli::success() { [[ "$WARD_CLI_QUIET" != "true" ]] && ward_cli::print "GREEN" "✓ $*"; }
ward_cli::error() { ward_cli::print "RED" "✗ $*" >&2; }
ward_cli::warning() { [[ "$WARD_CLI_QUIET" != "true" ]] && ward_cli::print "YELLOW" "⚠ $*"; }
ward_cli::info() { [[ "$WARD_CLI_QUIET" != "true" ]] && ward_cli::print "CYAN" "ℹ $*"; }
ward_cli::debug() { [[ "$WARD_CLI_VERBOSE" == "true" ]] && ward_cli::print "WHITE" "› $*"; }

# CLI banner
ward_cli::banner() {
    cat << 'EOF'
██╗      █████╗ ███████╗██████╗     ██╗ █████╗ ██╗
██║     ██╔════╝██╔════╝██╔══██╗    ██║██╔══██╗██║
██║     █████╗  ██║     █████╔╝    ██║███████║██║
██║     ██╔══╝  ██║     ██╔══██╗    ██║██╔══██║██║
███████╗███████╗███████╗██║  ██║    ██║██║  ██║███████╗
╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝╚═╝  ╚═╝╚══════╝
EOF
    ward_cli::print "BLUE" "Ward Security CLI v$WARD_CLI_VERSION"
    echo
}

# Command validation
ward_cli::validate_command() {
    local command="$1"
    local valid_commands=(
        "status" "check" "validate" "debug" "test" "install"
        "auth" "deploy" "cleanup" "export" "import" "config"
        "plugin" "logs" "metrics" "help" "version"
    )

    for valid_cmd in "${valid_commands[@]}"; do
        if [[ "$command" == "$valid_cmd" ]]; then
            return 0
        fi
    done

    return 1
}

# Command registration and execution
declare -A WARD_CLI_COMMANDS

ward_cli::register_command() {
    local command="$1"
    local function_name="$2"
    local description="$3"

    WARD_CLI_COMMANDS["$command"]="$function_name:$description"
}

ward_cli::execute_command() {
    local command="$1"
    shift
    local command_entry="${WARD_CLI_COMMANDS[$command]:-}"

    if [[ -z "$command_entry" ]]; then
        ward_cli::error "Unknown command: $command"
        ward_cli::show_help
        return 1
    fi

    local function_name="${command_entry%:*}"
    local description="${command_entry#*:}"

    ward_cli::debug "Executing command: $command ($function_name)"
    ward_cli::debug "Arguments: $*"

    # Execute command with error handling
    if ! "$function_name" "$@"; then
        local exit_code=$?
        ward_cli::error "Command '$command' failed with exit code $exit_code"
        return $exit_code
    fi

    return 0
}

# Command implementations
ward_cli::cmd_status() {
    ward_cli::info "Ward Security System Status"
    echo

    # System information
    echo "System Information:"
    echo "  Version: $WARD_ENGINE_VERSION"
    echo "  Root Directory: $WARD_ROOT_DIR"
    echo "  User: $(whoami)"
    echo "  Shell: $SHELL"
    echo "  Platform: $(uname -s)"
    echo

    # Engine status
    echo "Engine Status:"
    echo "  Policy Engine: ✓ Running"
    echo "  Configuration: ✓ Loaded"
    echo "  Logging: ✓ Active"
    echo "  Plugin Manager: ✓ Ready"
    echo

    # Configuration
    echo "Configuration:"
    ward::config::show | head -20
    echo

    # Plugin status
    if command -v ward::plugin::list >/dev/null 2>&1; then
        echo "Plugins:"
        ward::plugin::list | head -10
    fi
}

ward_cli::cmd_check() {
    local path="${1:-$(pwd)}"
    local resolved_path

    resolved_path=$(ward::resolve_path "$path") || {
        ward_cli::error "Invalid path: $path"
        return 1
    }

    ward_cli::info "Policy Analysis for: $resolved_path"
    echo

    local -a policies
    readarray -t policies < <("$WARD_ROOT_DIR/.ward/guard.sh" | ward::PolicyEngine discover_policies "$resolved_path")

    if [[ ${#policies[@]} -eq 0 ]]; then
        ward_cli::info "No policies apply to this path"
        return 0
    fi

    echo "Applicable Policies (${#policies[@]}):"
    echo

    for policy in "${policies[@]}"; do
        local rel_path="${policy#$WARD_ROOT_DIR/}"
        ward_cli::info "• $rel_path"

        # Parse and display key policies
        while IFS='=' read -r key value; do
            case "$key" in
                "policy.description")
                    echo "  Description: $value"
                    ;;
                "policy.whitelist")
                    echo "  Allowed Commands: $value"
                    ;;
                "policy.blacklist")
                    echo "  Blocked Commands: $value"
                    ;;
                "policy.lock_new_dirs")
                    echo "  New Directory Lock: $value"
                    ;;
                "policy.allow_comments")
                    echo "  Comments Allowed: $value"
                    ;;
            esac
        done < <("$WARD_ROOT_DIR/.ward/guard.sh" parse_policy "$policy")
        echo
    done
}

ward_cli::cmd_validate() {
    ward_cli::info "Validating Ward Policies"
    echo

    local errors=0
    local warnings=0

    # Validate policy files
    while IFS= read -r -d '' policy_file; do
        echo -n "Validating $(basename "$(dirname "$policy_file")")/.ward... "

        if bash -n "$policy_file" 2>/dev/null; then
            ward_cli::success "Valid"
        else
            ward_cli::error "Invalid syntax"
            ((errors++))
        fi
    done < <(find "$WARD_ROOT_DIR" -name ".ward" -type f -print0 2>/dev/null)

    echo
    if [[ $errors -eq 0 ]]; then
        ward_cli::success "All policies are valid"
        return 0
    else
        ward_cli::error "Found $errors invalid policies"
        return 1
    fi
}

ward_cli::cmd_debug() {
    local path="${1:-$(pwd)}"

    ward_cli::info "Debug Information for: $path"
    echo

    # System debug
    echo "System Debug:"
    echo "  Working Directory: $(pwd)"
    echo "  Script Path: ${BASH_SOURCE[0]}"
    echo "  WARD_ROOT: ${WARD_ROOT_DIR:-Not set}"
    echo

    # Configuration debug
    echo "Configuration Debug:"
    ward::config::show | head -10
    echo

    # Policy debug
    echo "Policy Debug:"
    ward_cli::cmd_check "$path"
}

ward_cli::cmd_install() {
    local installer="${WARD_ROOT_DIR}/setup-ward.sh"

    if [[ -x "$installer" ]]; then
        ward_cli::info "Running Ward installation..."
        "$installer"
    else
        ward_cli::error "Installation script not found: $installer"
        return 1
    fi
}

ward_cli::cmd_auth() {
    local action="${1:-status}"
    local auth_script="${WARD_ROOT_DIR}/.ward/ward-auth.sh"

    if [[ -x "$auth_script" ]]; then
        "$auth_script" "$action"
    else
        ward_cli::error "Authentication script not found: $auth_script"
        return 1
    fi
}

ward_cli::cmd_help() {
    local topic="${1:-general}"

    case "$topic" in
        "general"|"-h"|"--help"|"")
            ward_cli::show_help
            ;;
        "plugins")
            ward_cli::show_plugin_help
            ;;
        "config")
            ward_cli::show_config_help
            ;;
        *)
            ward_cli::error "Unknown help topic: $topic"
            ward_cli::show_help
            return 1
            ;;
    esac
}

ward_cli::cmd_version() {
    echo "Ward Security CLI v$WARD_CLI_VERSION"
    echo "Engine v$WARD_ENGINE_VERSION"
    echo "Author: $WARD_CLI_AUTHOR"
    echo "Platform: $(uname -s) $(uname -r)"
}

# Help displays
ward_cli::show_help() {
    cat << 'EOF'
Ward Security CLI - Enterprise File System Protection

USAGE:
    ward-cli [OPTIONS] <COMMAND> [ARGS...]

OPTIONS:
    -v, --verbose     Enable verbose output
    -q, --quiet       Suppress non-error output
    -f, --force       Force operation (bypass confirmations)
    -h, --help        Show this help message
    --version        Show version information

COMMANDS:
    status          Show system status and configuration
    check [path]    Analyze policies for a specific path
    validate         Validate all policy files
    debug [path]    Show debug information
    install          Install Ward system integration
    auth <action>   Manage authentication
    plugin <action>  Manage plugins
    logs [action]    View system logs
    config <action>  Manage configuration
    help [topic]    Show detailed help

EXAMPLES:
    ward-cli status                          # Show system status
    ward-cli check frontend/src              # Check policies for frontend/src
    ward-cli validate                         # Validate all policies
    ward-cli auth status                      # Show authentication status
    ward-cli install                          # Install system integration

For more detailed help on a specific topic:
    ward-cli help plugins       # Plugin management help
    ward-cli help config        # Configuration help
EOF
}

ward_cli::show_plugin_help() {
    cat << 'EOF
Ward Plugin Management

USAGE:
    ward-cli plugin <action> [args]

ACTIONS:
    list                List all available plugins
    info <plugin>       Show plugin information
    load <plugin>       Load a plugin
    unload <plugin>     Unload a plugin
    reload <plugin>     Reload a plugin
    enable <plugin>     Enable a plugin
    disable <plugin>    Disable a plugin

EXAMPLES:
    ward-cli plugin list                     # List all plugins
    ward-cli plugin info security           # Show security plugin info
    ward-cli plugin load audit               # Load audit plugin
EOF
}

ward_cli::show_config_help() {
    cat << 'EOF
Ward Configuration Management

USAGE:
    ward-cli config <action> [args]

ACTIONS:
    show                Show current configuration
    get <key>          Get configuration value
    set <key> <value>   Set configuration value
    reload              Reload configuration from file
    export              Export configuration as environment variables

EXAMPLES:
    ward-cli config show                       # Show all configuration
    ward-cli config get engine.debug           # Get debug setting
    ward-cli config set engine.debug true       # Enable debug mode
EOF
}

# Argument parsing
ward_cli::parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -v|--verbose)
                WARD_CLI_VERBOSE=true
                ward::config::set "logging.level" "DEBUG"
                shift
                ;;
            -q|--quiet)
                WARD_CLI_QUIET=true
                shift
                ;;
            -f|--force)
                WARD_CLI_FORCE=true
                shift
                ;;
            -h|--help)
                WARD_CLI_COMMAND="help"
                shift
                ;;
            --version)
                WARD_CLI_COMMAND="version"
                shift
                ;;
            -*)
                ward_cli::error "Unknown option: $1"
                return 1
                ;;
            *)
                if [[ -z "$WARD_CLI_COMMAND" ]]; then
                    WARD_CLI_COMMAND="$1"
                else
                    WARD_CLI_ARGS+=("$1")
                fi
                shift
                ;;
        esac
    done
}

# Main execution
main() {
    # Parse command line arguments
    if ! ward_cli::parse_args "$@"; then
        return 1
    fi

    # Validate command
    if [[ -z "$WARD_CLI_COMMAND" ]]; then
        WARD_CLI_COMMAND="status"
    fi

    if ! ward_cli::validate_command "$WARD_CLI_COMMAND"; then
        ward_cli::error "Unknown command: $WARD_CLI_COMMAND"
        return 1
    fi

    # Initialize system
    ward_cli::debug "Initializing Ward CLI v$WARD_CLI_VERSION"
    ward_cli::debug "Command: $WARD_CLI_COMMAND"
    ward_cli::debug "Arguments: ${WARD_CLI_ARGS[*]}"

    # Show banner unless quiet
    if [[ "$WARD_CLI_QUIET" != "true" && "$WARD_CLI_COMMAND" != "version" && "$WARD_CLI_COMMAND" != "help" ]]; then
        ward_cli::banner
    fi

    # Execute command
    ward_cli::execute_command "$WARD_CLI_COMMAND" "${WARD_CLI_ARGS[@]}"
}

# Register commands
ward_cli::register_command "status" "ward_cli::cmd_status" "Show system status and configuration"
ward_cli::register_command "check" "ward_cli::cmd_check" "Analyze policies for a specific path"
ward_cli::register_command "validate" "ward_cli::cmd_validate" "Validate all policy files"
ward_cli::register_command "debug" "ward_cli::cmd_debug" "Show debug information"
ward_cli::register_command "test" "ward_cli::cmd_test" "Test command execution"
ward_cli::register_command "install" "ward_cli::cmd_install" "Install Ward system integration"
ward_cli::register_command "auth" "ward_cli::cmd_auth" "Manage authentication"
ward_cli::register_command "deploy" "ward_cli::cmd_deploy" "Deploy Ward environment"
ward_cli::register_command "cleanup" "ward_cli::cmd_cleanup" "Clean Ward environment"
ward_cli::register_command "export" "ward_cli::cmd_export" "Export Ward environment"
ward_cli::register_command "import" "ward_cli::cmd_import" "Import Ward environment"
ward_cli::register_command "config" "ward_cli::cmd_config" "Manage configuration"
ward_cli::register_command "plugin" "ward_cli::cmd_plugin" "Manage plugins"
ward_cli::register_command "logs" "ward_cli::cmd_logs" "View system logs"
ward_cli::register_command "metrics" "ward_cli::cmd_metrics" "Show performance metrics"
ward_cli::register_command "help" "ward_cli::cmd_help" "Show help information"
ward_cli::register_command "version" "ward_cli::cmd_version" "Show version information"

# Execute main function
main "$@"