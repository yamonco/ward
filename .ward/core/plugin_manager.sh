#!/usr/bin/env bash
# core/plugin_manager.sh - Ward Plugin Management System
# Extensible architecture for custom security modules

set -euo pipefail

# Plugin namespace
declare -gr WARD_PLUGIN_NAMESPACE="WARD_PLUGIN"

# Plugin registry
declare -A WARD_PLUGINS
declare -A WARD_PLUGIN_METADATA
declare -A WARD_PLUGIN_HOOKS

# Plugin lifecycle states
declare -gr PLUGIN_STATE_UNLOADED="unloaded"
declare -gr PLUGIN_STATE_LOADING="loading"
declare -gr PLUGIN_STATE_LOADED="loaded"
declare -gr PLUGIN_STATE_ERROR="error"

# Available hooks
declare -ra WARD_PLUGIN_HOOKS=(
    "pre_policy_evaluation"
    "post_policy_evaluation"
    "pre_command_execution"
    "post_command_execution"
    "authentication_success"
    "authentication_failure"
    "policy_violation"
    "system_startup"
    "system_shutdown"
)

# Initialize plugin manager
ward::plugin::init() {
    local plugin_dir="${WARD_PLUGIN_DIR:-.ward/plugins}"

    ward::debug "Initializing plugin manager"
    ward::plugin::discover_plugins "$plugin_dir"
    ward::plugin::load_core_plugins
    ward::plugin::register_builtin_hooks

    ward::info "Plugin manager initialized (${#WARD_PLUGINS[@]} plugins)"
}

# Discover available plugins
ward::plugin::discover_plugins() {
    local plugin_dir="$1"

    if [[ ! -d "$plugin_dir" ]]; then
        ward::debug "Plugin directory not found: $plugin_dir"
        return 0
    fi

    while IFS= read -r -d '' plugin_file; do
        local plugin_name
        plugin_name=$(basename "$plugin_file" .sh)

        if ward::plugin::validate_plugin "$plugin_file"; then
            WARD_PLUGINS["$plugin_name"]="$plugin_file"
            WARD_PLUGIN_METADATA["$plugin_name"]="state=$PLUGIN_STATE_UNLOADED"
            ward::debug "Discovered plugin: $plugin_name"
        fi
    done < <(find "$plugin_dir" -name "*.sh" -print0 2>/dev/null)
}

# Validate plugin file
ward::plugin::validate_plugin() {
    local plugin_file="$1"

    # Check file exists and is readable
    [[ -r "$plugin_file" ]] || return 1

    # Check for required plugin metadata
    local required_functions=("plugin_init" "plugin_info")
    for func in "${required_functions[@]}"; do
        if ! grep -q "^[[:space:]]*function[[:space:]]*$func[[:space:]]*(" "$plugin_file" && \
           ! grep -q "^[[:space:]]*$func[[:space:]]*(" "$plugin_file"; then
            ward::debug "Plugin missing required function: $func in $plugin_file"
            return 1
        fi
    done

    # Check for security issues
    if grep -q "rm[[:space:]]+-rf[[:space:]]+/" "$plugin_file" 2>/dev/null; then
        ward::error "Plugin contains potentially dangerous commands: $plugin_file"
        return 1
    fi

    return 0
}

# Load core plugins
ward::plugin::load_core_plugins() {
    local core_plugins_dir="${WARD_CORE_DIR:-.ward/core}/plugins"

    if [[ -d "$core_plugins_dir" ]]; then
        while IFS= read -r -d '' plugin_file; do
            local plugin_name
            plugin_name=$(basename "$plugin_file" .sh)
            WARD_PLUGINS["core.$plugin_name"]="$plugin_file"
            WARD_PLUGIN_METADATA["core.$plugin_name"]="state=$PLUGIN_STATE_UNLOADED"
        done < <(find "$core_plugins_dir" -name "*.sh" -print0 2>/dev/null)
    fi
}

# Register built-in hooks
ward::plugin::register_builtin_hooks() {
    for hook in "${WARD_PLUGIN_HOOKS[@]}"; do
        WARD_PLUGIN_HOOKS["$hook"]=""
    done
}

# Load plugin
ward::plugin::load() {
    local plugin_name="$1"
    local plugin_file="${WARD_PLUGINS[$plugin_name]:-}"

    if [[ -z "$plugin_file" ]]; then
        ward::error "Plugin not found: $plugin_name"
        return 1
    fi

    local current_state="${WARD_PLUGIN_METADATA[$plugin_name]#*=}"
    if [[ "$current_state" == "$PLUGIN_STATE_LOADED" ]]; then
        ward::debug "Plugin already loaded: $plugin_name"
        return 0
    fi

    ward::debug "Loading plugin: $plugin_name"
    WARD_PLUGIN_METADATA["$plugin_name"]="state=$PLUGIN_STATE_LOADING"

    # Source plugin file in subshell to test for errors
    if ! (source "$plugin_file" >/dev/null 2>&1); then
        WARD_PLUGIN_METADATA["$plugin_name"]="state=$PLUGIN_STATE_ERROR"
        ward::error "Failed to load plugin: $plugin_name"
        return 1
    fi

    # Load plugin in current shell
    source "$plugin_file"

    # Initialize plugin
    if command -v "plugin_init" >/dev/null 2>&1; then
        if plugin_init; then
            WARD_PLUGIN_METADATA["$plugin_name"]="state=$PLUGIN_STATE_LOADED"
            ward::info "Plugin loaded successfully: $plugin_name"

            # Call plugin info to get metadata
            if command -v "plugin_info" >/dev/null 2>&1; then
                local plugin_info
                plugin_info=$(plugin_info)
                WARD_PLUGIN_METADATA["$plugin_name"]+=";info=$plugin_info"
            fi

            return 0
        else
            WARD_PLUGIN_METADATA["$plugin_name"]="state=$PLUGIN_STATE_ERROR"
            ward::error "Plugin initialization failed: $plugin_name"
            return 1
        fi
    else
        WARD_PLUGIN_METADATA["$plugin_name"]="state=$PLUGIN_STATE_ERROR"
        ward::error "Plugin missing plugin_init function: $plugin_name"
        return 1
    fi
}

# Unload plugin
ward::plugin::unload() {
    local plugin_name="$1"
    local current_state="${WARD_PLUGIN_METADATA[$plugin_name]#*=}"

    if [[ "$current_state" != "$PLUGIN_STATE_LOADED" ]]; then
        ward::warn "Plugin not loaded: $plugin_name"
        return 1
    fi

    # Call plugin cleanup if available
    if command -v "plugin_cleanup" >/dev/null 2>&1; then
        plugin_cleanup
    fi

    # Unregister hooks
    for hook in "${!WARD_PLUGIN_HOOKS[@]}"; do
        WARD_PLUGIN_HOOKS["$hook"]=$(echo "${WARD_PLUGIN_HOOKS[$hook]}" | sed "s|$plugin_name||g")
    done

    WARD_PLUGIN_METADATA["$plugin_name"]="state=$PLUGIN_STATE_UNLOADED"
    ward::info "Plugin unloaded: $plugin_name"
    return 0
}

# Register plugin hook
ward::plugin::register_hook() {
    local plugin_name="$1"
    local hook_name="$2"
    local hook_function="$3"

    if [[ -z "${WARD_PLUGIN_HOOKS[$hook_name]:-}" ]]; then
        WARD_PLUGIN_HOOKS["$hook_name"]="$plugin_name:$hook_function"
    else
        WARD_PLUGIN_HOOKS["$hook_name"]+="|$plugin_name:$hook_function"
    fi

    ward::debug "Registered hook: $hook_name -> $plugin_name:$hook_function"
}

# Execute plugin hooks
ward::plugin::execute_hooks() {
    local hook_name="$1"
    shift
    local hook_data=("$@")

    local hook_chain="${WARD_PLUGIN_HOOKS[$hook_name]:-}"

    if [[ -z "$hook_chain" ]]; then
        return 0
    fi

    ward::debug "Executing hooks for: $hook_name"

    IFS='|' read -ra hooks <<< "$hook_chain"
    for hook in "${hooks[@]}"; do
        local plugin_name="${hook%:*}"
        local hook_function="${hook#*:}"

        local plugin_state="${WARD_PLUGIN_METADATA[$plugin_name]#*=}"
        if [[ "$plugin_state" != "$PLUGIN_STATE_LOADED" ]]; then
            ward::debug "Skipping hook from unloaded plugin: $plugin_name"
            continue
        fi

        if command -v "$hook_function" >/dev/null 2>&1; then
            ward::debug "Executing hook: $hook_function (${hook_data[*]})"
            if ! "$hook_function" "${hook_data[@]}"; then
                ward::warn "Hook execution failed: $hook_function"
            fi
        else
            ward::error "Hook function not found: $hook_function"
        fi
    done
}

# List loaded plugins
ward::plugin::list() {
    local filter="${1:-}"

    echo "Ward Plugins"
    echo "============"
    printf "%-30s %-15s %s\n" "Plugin" "State" "Info"
    echo "------------------------------------------------------------"

    for plugin_name in "${!WARD_PLUGINS[@]}"; do
        if [[ -z "$filter" || "$plugin_name" =~ $filter ]]; then
            local state="${WARD_PLUGIN_METADATA[$plugin_name]#*=}"
            local info="${WARD_PLUGIN_METADATA[$plugin_name]#*info=}"
            printf "%-30s %-15s %s\n" "$plugin_name" "$state" "${info:-N/A}"
        fi
    done | sort
}

# Show plugin information
ward::plugin::info() {
    local plugin_name="$1"

    if [[ -z "${WARD_PLUGINS[$plugin_name]:-}" ]]; then
        ward::error "Plugin not found: $plugin_name"
        return 1
    fi

    echo "Plugin Information: $plugin_name"
    echo "========================="
    echo "File: ${WARD_PLUGINS[$plugin_name]}"
    echo "State: ${WARD_PLUGIN_METADATA[$plugin_name]#*=}"

    local info="${WARD_PLUGIN_METADATA[$plugin_name]#*info=}"
    if [[ -n "$info" ]]; then
        echo "Info: $info"
    fi

    # Show registered hooks
    local registered_hooks=()
    for hook in "${!WARD_PLUGIN_HOOKS[@]}"; do
        if [[ "$hook" =~ $plugin_name ]]; then
            registered_hooks+=("$hook")
        fi
    done

    if [[ ${#registered_hooks[@]} -gt 0 ]]; then
        echo "Hooks: ${registered_hooks[*]}"
    fi
}

# Reload plugin
ward::plugin::reload() {
    local plugin_name="$1"

    ward::plugin::unload "$plugin_name"
    sleep 1
    ward::plugin::load "$plugin_name"
}

# Enable/disable plugin
ward::plugin::enable() {
    local plugin_name="$1"
    local config_file="${WARD_CONFIG_FILE:-.ward/ward.conf}"

    echo "plugin.$plugin_name.enabled=true" >> "$config_file"
    ward::plugin::load "$plugin_name"
}

ward::plugin::disable() {
    local plugin_name="$1"
    local config_file="${WARD_CONFIG_FILE:-.ward/ward.conf}"

    echo "plugin.$plugin_name.enabled=false" >> "$config_file"
    ward::plugin::unload "$plugin_name"
}

# Plugin API helpers for plugin developers
ward::plugin::api_log() {
    local level="$1"
    shift
    local message="$*"
    local plugin_name="${WARD_CURRENT_PLUGIN:-unknown}"

    ward::log "$level" "[$plugin_name] $message"
}

ward::plugin::api_register_command() {
    local command_name="$1"
    local command_function="$2"

    # Create a wrapper function that validates the plugin is loaded
    eval "
    $command_name() {
        if [[ \"\${WARD_PLUGIN_METADATA[\$WARD_CURRENT_PLUGIN]#*=}\" != \"$PLUGIN_STATE_LOADED\" ]]; then
            ward::error \"Plugin not loaded: \$WARD_CURRENT_PLUGIN\"
            return 1
        fi
        $command_function \"\$@\"
    }
    "

    ward::debug "Registered command: $command_name from plugin"
}

ward::plugin::api_add_policy_directive() {
    local directive="$1"
    local default_value="$2"

    # This would extend the policy parser to support custom directives
    ward::debug "Plugin added policy directive: $directive (default: $default_value)"
}

# Initialize plugin manager
ward::plugin::init