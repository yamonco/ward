#!/usr/bin/env bash
# core/engine.sh - Ward Security Engine v2.0
# Advanced file system protection with enterprise-grade architecture

set -euo pipefail

readonly WARD_ENGINE_VERSION="2.0.0"
readonly WARD_ENGINE_AUTHOR="Ward Security Team"

# Core namespace and constants
declare -gr WARD_NAMESPACE="WARD_SECURITY"
declare -gr WARD_LOG_LEVEL="${WARD_LOG_LEVEL:-INFO}"
declare -gr WARD_CONFIG_FILE="${WARD_CONFIG_FILE:-.ward/ward.conf}"

# Error codes
declare -gr WARD_ERR_SUCCESS=0
declare -gr WARD_ERR_PERMISSION_DENIED=1
declare -gr WARD_ERR_INVALID_POLICY=2
declare -gr WARD_ERR_AUTHENTICATION_FAILED=3
declare -gr WARD_ERR_CONFIGURATION_ERROR=4
declare -gr WARD_ERR_SYSTEM_ERROR=5

# Core utility functions
ward::log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "DEBUG")   echo -e "\033[0;36m[$timestamp] [DEBUG] $message\033[0m" ;;
        "INFO")    echo -e "\033[0;32m[$timestamp] [INFO] $message\033[0m" ;;
        "WARN")    echo -e "\033[1;33m[$timestamp] [WARN] $message\033[0m" ;;
        "ERROR")   echo -e "\033[0;31m[$timestamp] [ERROR] $message\033[0m" >&2 ;;
        "FATAL")   echo -e "\033[1;31m[$timestamp] [FATAL] $message\033[0m" >&2 ;;
        *)         echo "[$timestamp] [$level] $message" ;;
    esac
}

ward::debug() { [[ "$WARD_LOG_LEVEL" == "DEBUG" ]] && ward::log "DEBUG" "$@"; }
ward::info() { ward::log "INFO" "$@"; }
ward::warn() { ward::log "WARN" "$@"; }
ward::error() { ward::log "ERROR" "$@"; }
ward::fatal() { ward::log "FATAL" "$@"; exit 1; }

# Advanced path resolution with security validation
ward::resolve_path() {
    local input_path="$1"
    local resolved_path

    # Security: prevent path traversal attacks
    if [[ "$input_path" =~ \.\. ]]; then
        ward::error "Path traversal detected: $input_path"
        return "$WARD_ERR_PERMISSION_DENIED"
    fi

    # Resolve to absolute path
    if command -v realpath >/dev/null 2>&1; then
        resolved_path=$(realpath -m "$input_path" 2>/dev/null)
    else
        # Fallback for older systems
        resolved_path=$(cd "$(dirname "$input_path")" && pwd)/$(basename "$input_path")
    fi

    # Validate resolved path
    if [[ ! -d "$(dirname "$resolved_path")" ]]; then
        ward::error "Invalid path resolution: $resolved_path"
        return "$WARD_ERR_SYSTEM_ERROR"
    fi

    echo "$resolved_path"
    return "$WARD_ERR_SUCCESS"
}

# Policy evaluation engine
ward::PolicyEngine() {
    declare -A policy_cache
    declare -A policy_metadata

    # Initialize policy engine
    __init() {
        ward::debug "Initializing Ward Policy Engine v$WARD_ENGINE_VERSION"
        _load_configuration
        _validate_system_requirements
    }

    # Load configuration from file or defaults
    _load_configuration() {
        if [[ -f "$WARD_CONFIG_FILE" ]]; then
            ward::debug "Loading configuration from: $WARD_CONFIG_FILE"
            source "$WARD_CONFIG_FILE"
        else
            ward::debug "Using default configuration"
            _set_default_configuration
        fi
    }

    # Set default configuration values
    _set_default_configuration() {
        WARD_ROOT="${WARD_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
        WARD_CACHE_ENABLED="${WARD_CACHE_ENABLED:-true}"
        WARD_STRICT_MODE="${WARD_STRICT_MODE:-true}"
        WARD_AUDIT_ENABLED="${WARD_AUDIT_ENABLED:-false}"
    }

    # Validate system requirements
    _validate_system_requirements() {
        local required_commands=("find" "grep" "sed" "wc")

        for cmd in "${required_commands[@]}"; do
            if ! command -v "$cmd" >/dev/null 2>&1; then
                ward::fatal "Required command not found: $cmd"
            fi
        done

        ward::debug "System requirements validation passed"
    }

    # Discover ward policies for a given path
    discover_policies() {
        local target_path="$1"
        local -a policy_chain=()
        local current_dir

        target_path=$(ward::resolve_path "$target_path") || return $?

        if [[ -d "$target_path" ]]; then
            current_dir="$target_path"
        else
            current_dir=$(dirname "$target_path")
        fi

        ward::debug "Discovering policies for path: $target_path"

        # Traverse up the directory tree
        while [[ "$current_dir" != "/" ]] && [[ "$current_dir" != "$WARD_ROOT" ]]; do
            local policy_file="$current_dir/.ward"

            if [[ -f "$policy_file" ]]; then
                policy_cache["$policy_file"]="$(_get_policy_hash "$policy_file")"
                policy_chain+=("$policy_file")
                ward::debug "Found policy: $policy_file"
            fi

            current_dir=$(dirname "$current_dir")
        done

        # Check root ward
        local root_policy="$WARD_ROOT/.ward/.ward"
        if [[ -f "$root_policy" ]]; then
            policy_cache["$root_policy"]="$(_get_policy_hash "$root_policy")"
            policy_chain+=("$root_policy")
        fi

        # Output in parent-to-child order (reverse of discovery)
        for (( i=${#policy_chain[@]}-1; i>=0; i-- )); do
            echo "${policy_chain[$i]}"
        done
    }

    # Get policy file hash for cache validation
    _get_policy_hash() {
        local policy_file="$1"
        if command -v sha256sum >/dev/null 2>&1; then
            sha256sum "$policy_file" | cut -d' ' -f1
        else
            # Fallback: use modification time
            stat -c %Y "$policy_file" 2>/dev/null || stat -f %m "$policy_file" 2>/dev/null
        fi
    }

    # Parse policy file with advanced syntax support
    parse_policy() {
        local policy_file="$1"
        local cache_key="${policy_cache[$policy_file]:-$(date +%s)}"

        # Check cache if enabled
        if [[ "$WARD_CACHE_ENABLED" == "true" ]]; then
            local cache_entry="/tmp/ward_cache_$(echo "$policy_file" | tr '/' '_')"
            if [[ -f "$cache_entry" ]]; then
                local cached_hash
                cached_hash=$(head -1 "$cache_entry")
                if [[ "$cached_hash" == "$cache_key" ]]; then
                    ward::debug "Using cached policy for: $policy_file"
                    tail -n +2 "$cache_entry"
                    return "$WARD_ERR_SUCCESS"
                fi
            fi
        fi

        # Parse policy file
        local -A policy_data
        local line_num=0
        local section="metadata"

        while IFS= read -r line; do
            ((line_num++))

            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

            # Section headers
            if [[ "$line" =~ ^\[(.+)\]$ ]]; then
                section="${BASH_REMATCH[1],,}"
                continue
            fi

            # Key-value pairs
            if [[ "$line" =~ ^[[:space:]]*([a-zA-Z_][a-zA-Z0-9_]*)[[:space:]]*=[[:space:]]*(.+)$ ]]; then
                local key="${BASH_REMATCH[1]}"
                local value="${BASH_REMATCH[2]}"
                value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                policy_data["${section}.${key}"]="$value"
                continue
            fi

            # Legacy @directive syntax (for backward compatibility)
            if [[ "$line" =~ ^@([a-zA-Z_][a-zA-Z0-9_]*)[[:space:]]*:[[:space:]]*(.+)$ ]]; then
                local directive="${BASH_REMATCH[1]}"
                local value="${BASH_REMATCH[2]}"
                value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                policy_data["policy.$directive"]="$value"
                continue
            fi

            # Free-form description
            if [[ "$line" =~ ^[[:space:]]*[^@#\[] ]]; then
                if [[ -n "${policy_data[metadata.description]:-}" ]]; then
                    policy_data["metadata.description"]+=$'\n'"$line"
                else
                    policy_data["metadata.description"]="$line"
                fi
            fi
        done < "$policy_file"

        # Output parsed policy (cache format)
        if [[ "$WARD_CACHE_ENABLED" == "true" ]]; then
            echo "$cache_key" > "$cache_entry"
        fi

        # Output policy data
        for key in "${!policy_data[@]}"; do
            echo "$key=${policy_data[$key]}"
            if [[ "$WARD_CACHE_ENABLED" == "true" ]]; then
                echo "$key=${policy_data[$key]}" >> "$cache_entry"
            fi
        done

        ward::debug "Parsed policy: $policy_file (${#policy_data[@]} directives)"
    }

    # Execute the initializer
    __init
}

# Global policy engine instance
declare -g WARD_POLICY_ENGINE
WARD_POLICY_ENGINE=$(ward::PolicyEngine)