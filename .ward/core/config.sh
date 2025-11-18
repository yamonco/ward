#!/usr/bin/env bash
# core/config.sh - Ward Configuration Management System
# Professional configuration with validation and hot-reload support

set -euo pipefail

# Configuration namespace
declare -gr WARD_CONFIG_NAMESPACE="WARD_CONFIG"

# Default configuration values
declare -Ar WARD_DEFAULTS=(
    ["engine.version"]="2.0.0"
    ["engine.debug"]="false"
    ["engine.cache_enabled"]="true"
    ["engine.strict_mode"]="true"
    ["engine.audit_enabled"]="false"

    ["security.authentication.enabled"]="true"
    ["security.authentication.session_timeout"]="3600"
    ["security.encryption.algorithm"]="SHA256"
    ["security.max_login_attempts"]="3"

    ["policy.default_whitelist"]="ls cat pwd"
    ["policy.default_blacklist"]=""
    ["policy.default_lock_new_dirs"]="false"
    ["policy.default_allow_comments"]="true"
    ["policy.default_max_comments"]="5"

    ["logging.level"]="INFO"
    ["logging.format"]="structured"
    ["logging.file_enabled"]="false"
    ["logging.file_path"]=".ward/logs/ward.log"
    ["logging.max_file_size"]="10MB"
    ["logging.max_files"]="5"

    ["performance.parallel_policy_evaluation"]="true"
    ["performance.cache_ttl"]="300"
    ["performance.max_concurrent_operations"]="10"
)

# Runtime configuration storage
declare -A WARD_CONFIG
declare -A WARD_CONFIG_METADATA

# Initialize configuration system
ward::config::init() {
    local config_file="${WARD_CONFIG_FILE:-.ward/ward.conf}"

    ward::config::load_defaults
    if [[ -f "$config_file" ]]; then
        ward::config::load_file "$config_file"
    fi
    ward::config::load_environment
    ward::config::validate_all

    ward::debug "Configuration system initialized"
}

# Load default configuration values
ward::config::load_defaults() {
    for key in "${!WARD_DEFAULTS[@]}"; do
        WARD_CONFIG["$key"]="${WARD_DEFAULTS[$key]}"
        WARD_CONFIG_METADATA["$key"]="source=default"
    done
}

# Load configuration from file with validation
ward::config::load_file() {
    local config_file="$1"

    ward::debug "Loading configuration from: $config_file"

    if [[ ! -r "$config_file" ]]; then
        ward::error "Configuration file not readable: $config_file"
        return 1
    fi

    local line_num=0
    while IFS= read -r line; do
        ((line_num++))

        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

        # Parse key-value pairs
        if [[ "$line" =~ ^[[:space:]]*([a-zA-Z_][a-zA-Z0-9_.]*)[[:space:]]*=[[:space:]]*(.+)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"

            # Remove surrounding whitespace and quotes
            value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            value=$(echo "$value" | sed 's/^"//;s/"$//')
            value=$(echo "$value" | sed "s/^'//;s/'$//")

            # Validate key
            if ward::config::validate_key "$key"; then
                # Type validation and conversion
                if ward::config::validate_value "$key" "$value"; then
                    WARD_CONFIG["$key"]="$value"
                    WARD_CONFIG_METADATA["$key"]="source=file:$config_file:$line_num"
                    ward::debug "Set config: $key=$value"
                else
                    ward::error "Invalid value for $key: $value (line $line_num)"
                fi
            else
                ward::error "Invalid configuration key: $key (line $line_num)"
            fi
        else
            ward::warn "Invalid configuration syntax (line $line_num): $line"
        fi
    done < "$config_file"
}

# Load configuration from environment variables
ward::config::load_environment() {
    local prefix="WARD_"

    while IFS='=' read -r key value; do
        if [[ "$key" =~ ^${prefix}(.+)$ ]]; then
            local config_key="${BASH_REMATCH[1]}"
            config_key=$(echo "$config_key" | tr '[:upper:]' '[:lower:]')
            config_key=$(echo "$config_key" | tr '_' '.')

            if [[ -n "${WARD_CONFIG[$config_key]:-}" ]]; then
                WARD_CONFIG["$config_key"]="$value"
                WARD_CONFIG_METADATA["$config_key"]="source=environment"
                ward::debug "Override config from environment: $config_key=$value"
            fi
        fi
    done < <(env | grep "^${prefix}")
}

# Validate configuration key
ward::config::validate_key() {
    local key="$1"

    # Check key format
    if [[ ! "$key" =~ ^[a-z][a-z0-9_.]*$ ]]; then
        return 1
    fi

    # Check against known configuration keys
    for known_key in "${!WARD_DEFAULTS[@]}"; do
        if [[ "$key" == "$known_key" ]]; then
            return 0
        fi
    done

    ward::warn "Unknown configuration key: $key"
    return "$WARD_STRICT_MODE"  # Strict mode rejects unknown keys
}

# Validate configuration value
ward::config::validate_value() {
    local key="$1"
    local value="$2"

    case "$key" in
        "engine.debug"|"engine.cache_enabled"|"engine.strict_mode"|"engine.audit_enabled")
            if [[ "$value" =~ ^(true|false)$ ]]; then
                return 0
            fi
            ;;
        "security.authentication.session_timeout")
            if [[ "$value" =~ ^[0-9]+$ ]] && [[ "$value" -gt 0 ]]; then
                return 0
            fi
            ;;
        "logging.level")
            if [[ "$value" =~ ^(DEBUG|INFO|WARN|ERROR|FATAL)$ ]]; then
                return 0
            fi
            ;;
        "logging.max_file_size")
            if [[ "$value" =~ ^[0-9]+[KMGT]?B$ ]]; then
                return 0
            fi
            ;;
        "policy.max_comments")
            if [[ "$value" =~ ^[0-9]+$ ]] && [[ "$value" -gt 0 ]]; then
                return 0
            fi
            ;;
        *)
            # For unknown keys, accept in non-strict mode
                return $((! WARD_STRICT_MODE))
            ;;
    esac

    return 1
}

# Validate all configuration values
ward::config::validate_all() {
    local errors=0

    for key in "${!WARD_CONFIG[@]}"; do
        if ! ward::config::validate_value "$key" "${WARD_CONFIG[$key]}"; then
            ward::error "Invalid configuration value: $key=${WARD_CONFIG[$key]}"
            ((errors++))
        fi
    done

    if [[ $errors -gt 0 ]]; then
        ward::fatal "Configuration validation failed with $errors errors"
    fi

    ward::debug "All configuration values validated successfully"
}

# Get configuration value with default
ward::config::get() {
    local key="$1"
    local default="${2:-}"

    echo "${WARD_CONFIG[$key]:-$default}"
}

# Set configuration value
ward::config::set() {
    local key="$1"
    local value="$2"
    local persist="${3:-false}"

    if ward::config::validate_key "$key" && ward::config::validate_value "$key" "$value"; then
        WARD_CONFIG["$key"]="$value"
        WARD_CONFIG_METADATA["$key"]="source=runtime"

        if [[ "$persist" == "true" ]]; then
            ward::config::persist "$key" "$value"
        fi

        ward::debug "Set configuration: $key=$value"
        return 0
    else
        ward::error "Failed to set configuration: $key=$value"
        return 1
    fi
}

# Persist configuration to file
ward::config::persist() {
    local key="$1"
    local value="$2"
    local config_file="${WARD_CONFIG_FILE:-.ward/ward.conf}"

    # Create backup
    if [[ -f "$config_file" ]]; then
        cp "$config_file" "$config_file.bak"
    fi

    # Update or add the configuration
    if grep -q "^$key=" "$config_file" 2>/dev/null; then
        sed -i "s|^$key=.*|$key=\"$value\"|" "$config_file"
    else
        echo "$key=\"$value\"" >> "$config_file"
    fi

    ward::debug "Persisted configuration: $key=$value"
}

# Reload configuration from file
ward::config::reload() {
    local config_file="${WARD_CONFIG_FILE:-.ward/ward.conf}"

    ward::info "Reloading configuration from: $config_file"
    ward::config::load_defaults
    if [[ -f "$config_file" ]]; then
        ward::config::load_file "$config_file"
    fi
    ward::config::load_environment
    ward::config::validate_all
}

# Export configuration as environment variables
ward::config::export() {
    for key in "${!WARD_CONFIG[@]}"; do
        local env_key="WARD_$(echo "$key" | tr '[:lower:].' '[:upper:]_')"
        export "$env_key"="${WARD_CONFIG[$key]}"
    done
}

# Show current configuration
ward::config::show() {
    local filter="${1:-}"

    echo "Ward Configuration v${WARD_CONFIG[engine.version]}"
    echo "========================================"

    for key in $(printf '%s\n' "${!WARD_CONFIG[@]}" | sort); do
        if [[ -z "$filter" || "$key" =~ $filter ]]; then
            local value="${WARD_CONFIG[$key]}"
            local source="${WARD_CONFIG_METADATA[$key]}"
            printf "%-40s = %-20s [%s]\n" "$key" "$value" "$source"
        fi
    done
}

# Configuration schema validation
ward::config::validate_schema() {
    local schema_file="${1:-.ward/ward.schema.json}"

    if [[ ! -f "$schema_file" ]]; then
        ward::warn "Schema file not found: $schema_file"
        return 0
    fi

    # This would integrate with a JSON schema validator
    # For now, just basic validation
    ward::info "Validating configuration against schema: $schema_file"
    # TODO: Implement JSON schema validation
}

# Initialize configuration system
ward::config::init