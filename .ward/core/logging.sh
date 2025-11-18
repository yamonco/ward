#!/usr/bin/env bash
# core/logging.sh - Ward Advanced Logging System
# Structured logging with multiple outputs and log rotation

set -euo pipefail

# Logging namespace
declare -gr WARD_LOG_NAMESPACE="WARD_LOGGING"

# Log levels (numeric for comparison)
declare -gr WARD_LOG_TRACE=0
declare -gr WARD_LOG_DEBUG=1
declare -gr WARD_LOG_INFO=2
declare -gr WARD_LOG_WARN=3
declare -gr WARD_LOG_ERROR=4
declare -gr WARD_LOG_FATAL=5

# Current log level (configurable)
declare -g WARD_CURRENT_LOG_LEVEL="${WARD_LOG_LEVEL:-$WARD_LOG_INFO}"

# Log format types
declare -gr WARD_LOG_FORMAT_SIMPLE="simple"
declare -gr WARD_LOG_FORMAT_STRUCTURED="structured"
declare -gr WARD_LOG_FORMAT_JSON="json"

# Log output configuration
declare -g WARD_LOG_FORMAT="${WARD_LOG_FORMAT:-$WARD_LOG_FORMAT_STRUCTURED}"
declare -g WARD_LOG_TO_FILE="${WARD_LOG_TO_FILE:-false}"
declare -g WARD_LOG_TO_SYSLOG="${WARD_LOG_TO_SYSLOG:-false}"
declare -g WARD_LOG_FILE="${WARD_LOG_FILE:-.ward/logs/ward.log}"
declare -g WARD_LOG_MAX_SIZE="${WARD_LOG_MAX_SIZE:-10MB}"
declare -g WARD_LOG_MAX_FILES="${WARD_LOG_MAX_FILES:-5}"

# Color codes for console output
declare -Ar WARD_LOG_COLORS=(
    [$WARD_LOG_TRACE]="\033[0;37m"  # Gray
    [$WARD_LOG_DEBUG]="\033[0;36m"  # Cyan
    [$WARD_LOG_INFO]="\033[0;32m"   # Green
    [$WARD_LOG_WARN]="\033[1;33m"  # Yellow
    [$WARD_LOG_ERROR]="\033[0;31m" # Red
    [$WARD_LOG_FATAL]="\033[1;31m" # Bold Red
)

declare -gr WARD_LOG_RESET="\033[0m"

# Log buffer for batch operations
declare -a WARD_LOG_BUFFER
declare -g WARD_LOG_BUFFER_SIZE=1000
declare -g WARD_LOG_BUFFER_ENABLED=false

# Performance metrics
declare -A WARD_LOG_METRICS
declare -g WARD_LOG_METRICS_ENABLED=false

# Initialize logging system
ward::logging::init() {
    local config_file="${WARD_CONFIG_FILE:-.ward/ward.conf}"

    # Load logging configuration
    ward::logging::load_config "$config_file"

    # Initialize log files
    if [[ "$WARD_LOG_TO_FILE" == "true" ]]; then
        ward::logging::init_log_file
    fi

    # Initialize syslog if enabled
    if [[ "$WARD_LOG_TO_SYSLOG" == "true" ]]; then
        ward::logging::init_syslog
    fi

    # Setup signal handlers for graceful shutdown
    trap 'ward::logging::shutdown' EXIT TERM INT

    ward::debug "Logging system initialized (level: $WARD_CURRENT_LOG_LEVEL, format: $WARD_LOG_FORMAT)"
}

# Load logging configuration
ward::logging::load_config() {
    local config_file="$1"

    if [[ -f "$config_file" ]]; then
        # Parse logging configuration
        while IFS='=' read -r key value; do
            case "$key" in
                "logging.level")
                    case "${value^^}" in
                        "TRACE") WARD_CURRENT_LOG_LEVEL="$WARD_LOG_TRACE" ;;
                        "DEBUG") WARD_CURRENT_LOG_LEVEL="$WARD_LOG_DEBUG" ;;
                        "INFO")  WARD_CURRENT_LOG_LEVEL="$WARD_LOG_INFO" ;;
                        "WARN")  WARD_CURRENT_LOG_LEVEL="$WARD_LOG_WARN" ;;
                        "ERROR") WARD_CURRENT_LOG_LEVEL="$WARD_LOG_ERROR" ;;
                        "FATAL") WARD_CURRENT_LOG_LEVEL="$WARD_LOG_FATAL" ;;
                    esac
                    ;;
                "logging.format")
                    case "${value,,}" in
                        "simple") WARD_LOG_FORMAT="$WARD_LOG_FORMAT_SIMPLE" ;;
                        "structured") WARD_LOG_FORMAT="$WARD_LOG_FORMAT_STRUCTURED" ;;
                        "json") WARD_LOG_FORMAT="$WARD_LOG_FORMAT_JSON" ;;
                    esac
                    ;;
                "logging.file_enabled")
                    WARD_LOG_TO_FILE="$value"
                    ;;
                "logging.file_path")
                    WARD_LOG_FILE="$value"
                    ;;
                "logging.max_file_size")
                    WARD_LOG_MAX_SIZE="$value"
                    ;;
                "logging.max_files")
                    WARD_LOG_MAX_FILES="$value"
                    ;;
                "logging.metrics_enabled")
                    WARD_LOG_METRICS_ENABLED="$value"
                    ;;
            esac
        done < <(grep "^logging\." "$config_file" 2>/dev/null)
    fi
}

# Initialize log file
ward::logging::init_log_file() {
    local log_dir
    log_dir=$(dirname "$WARD_LOG_FILE")

    if [[ ! -d "$log_dir" ]]; then
        mkdir -p "$log_dir"
    fi

    # Check if log rotation is needed
    ward::logging::rotate_if_needed

    # Create or append to log file
    touch "$WARD_LOG_FILE"
}

# Initialize syslog
ward::logging::init_syslog() {
    if command -v logger >/dev/null 2>&1; then
        ward::debug "Syslog initialized"
    else
        ward::warn "Syslog not available, disabling syslog logging"
        WARD_LOG_TO_SYSLOG="false"
    fi
}

# Check if log rotation is needed
ward::logging::rotate_if_needed() {
    [[ ! -f "$WARD_LOG_FILE" ]] && return 0

    local current_size
    current_size=$(stat -f%z "$WARD_LOG_FILE" 2>/dev/null || stat -c%s "$WARD_LOG_FILE" 2>/dev/null)
    local max_size_bytes
    max_size_bytes=$(ward::logging::parse_size "$WARD_LOG_MAX_SIZE")

    if [[ $current_size -gt $max_size_bytes ]]; then
        ward::logging::rotate_logs
    fi
}

# Parse size string to bytes
ward::logging::parse_size() {
    local size_str="$1"
    local number
    local unit

    if [[ "$size_str" =~ ^([0-9]+)([KMGT]?B?)?$ ]]; then
        number="${BASH_REMATCH[1]}"
        unit="${BASH_REMATCH[2]}"
    else
        echo 10485760  # Default 10MB
        return
    fi

    case "${unit,,}" in
        "b"|"") echo "$number" ;;
        "kb") echo $((number * 1024)) ;;
        "mb") echo $((number * 1024 * 1024)) ;;
        "gb") echo $((number * 1024 * 1024 * 1024)) ;;
        "tb") echo $((number * 1024 * 1024 * 1024 * 1024)) ;;
        *) echo "$number" ;;
    esac
}

# Rotate log files
ward::logging::rotate_logs() {
    local max_files="${WARD_LOG_MAX_FILES:-5}"

    ward::debug "Rotating log files (max: $max_files)"

    # Remove oldest log if it exists
    local oldest_log="$WARD_LOG_FILE.$max_files"
    if [[ -f "$oldest_log" ]]; then
        rm "$oldest_log"
    fi

    # Shift existing logs
    for ((i=max_files-1; i>=1; i--)); do
        local current_log="$WARD_LOG_FILE.$i"
        local next_log="$WARD_LOG_FILE.$((i+1))"
        if [[ -f "$current_log" ]]; then
            mv "$current_log" "$next_log"
        fi
    done

    # Move current log to .1
    if [[ -f "$WARD_LOG_FILE" ]]; then
        mv "$WARD_LOG_FILE" "$WARD_LOG_FILE.1"
    fi

    # Create new log file
    touch "$WARD_LOG_FILE"
}

# Get current timestamp in ISO format
ward::logging::timestamp() {
    date '+%Y-%m-%dT%H:%M:%S.%3NZ'
}

# Get hostname for structured logging
ward::logging::hostname() {
    hostname 2>/dev/null || echo "unknown"
}

# Get process ID
ward::logging::pid() {
    echo $$
}

# Simple format logging
ward::logging::log_simple() {
    local level="$1"
    shift
    local message="$*"
    local level_num="$1"
    shift

    if [[ $level_num -lt $WARD_CURRENT_LOG_LEVEL ]]; then
        return 0
    fi

    local timestamp
    timestamp=$(ward::logging::timestamp)
    local color="${WARD_LOG_COLORS[$level_num]}"
    local level_name="${WARD_LOG_LEVEL_NAMES[$level_num]}"

    echo -e "${color}[$timestamp] [$level_name] $message${WARD_LOG_RESET}"
}

# Structured format logging
ward::logging::log_structured() {
    local level="$1"
    shift
    local message="$*"
    local level_num="$1"
    shift

    if [[ $level_num -lt $WARD_CURRENT_LOG_LEVEL ]]; then
        return 0
    fi

    local timestamp
    timestamp=$(ward::logging::timestamp)
    local hostname
    hostname=$(ward::logging::hostname)
    local pid
    pid=$(ward::logging::pid)
    local level_name="${WARD_LOG_LEVEL_NAMES[$level_num]}"

    echo "time=\"$timestamp\" level=\"$level_name\" host=\"$hostname\" pid=\"$pid\" message=\"$message\""
}

# JSON format logging
ward::logging::log_json() {
    local level="$1"
    shift
    local message="$*"
    local level_num="$1"
    shift

    if [[ $level_num -lt $WARD_CURRENT_LOG_LEVEL ]]; then
        return 0
    fi

    local timestamp
    timestamp=$(ward::logging::timestamp)
    local hostname
    hostname=$(ward::logging::hostname)
    local pid
    pid=$(ward::logging::pid)
    local level_name="${WARD_LOG_LEVEL_NAMES[$level_num]}"

    # Create JSON object
    local json="{"
    json+="\"timestamp\":\"$timestamp\","
    json+="\"level\":\"$level_name\","
    json+="\"host\":\"$hostname\","
    json+="\"pid\":$pid,"
    json+="\"message\":\"$(echo "$message" | sed 's/"/\\"/g')\""

    # Add metrics if enabled
    if [[ "$WARD_LOG_METRICS_ENABLED" == "true" ]]; then
        json+=",\"metrics\":{"
        local first=true
        for metric in "${!WARD_LOG_METRICS[@]}"; do
            if [[ "$first" == "true" ]]; then
                first=false
            else
                json+=","
            fi
            json+="\"$metric\":\"${WARD_LOG_METRICS[$metric]}\""
        done
        json+="}"
    fi

    json+="}"

    echo "$json"
}

# Main logging function
ward::logging::log() {
    local level="$1"
    shift
    local message="$*"

    # Convert level name to number
    local level_num
    case "${level^^}" in
        "TRACE") level_num="$WARD_LOG_TRACE" ;;
        "DEBUG") level_num="$WARD_LOG_DEBUG" ;;
        "INFO")  level_num="$WARD_LOG_INFO" ;;
        "WARN")  level_num="$WARD_LOG_WARN" ;;
        "ERROR") level_num="$WARD_LOG_ERROR" ;;
        "FATAL") level_num="$WARD_LOG_FATAL" ;;
        *) level_num="$WARD_LOG_INFO" ;;  # Default to INFO
    esac

    # Set level name for formatting
    case "$level_num" in
        $WARD_LOG_TRACE) level_name="TRACE" ;;
        $WARD_LOG_DEBUG) level_name="DEBUG" ;;
        $WARD_LOG_INFO)  level_name="INFO" ;;
        $WARD_LOG_WARN)  level_name="WARN" ;;
        $WARD_LOG_ERROR) level_name="ERROR" ;;
        $WARD_LOG_FATAL) level_name="FATAL" ;;
        *) level_name="INFO" ;;
    esac

    # Add to buffer if enabled
    if [[ "$WARD_LOG_BUFFER_ENABLED" == "true" ]]; then
        WARD_LOG_BUFFER+=("$level_name: $message")
        if [[ ${#WARD_LOG_BUFFER[@]} -ge $WARD_LOG_BUFFER_SIZE ]]; then
            ward::logging::flush_buffer
        fi
    fi

    # Format and output based on configuration
    local formatted_output
    case "$WARD_LOG_FORMAT" in
        "$WARD_LOG_FORMAT_SIMPLE")
            formatted_output=$(ward::logging::log_simple "$level_name" "$message" $level_num)
            ;;
        "$WARD_LOG_FORMAT_STRUCTURED")
            formatted_output=$(ward::logging::log_structured "$level_name" "$message" $level_num)
            ;;
        "$WARD_LOG_FORMAT_JSON")
            formatted_output=$(ward::logging::log_json "$level_name" "$message" $level_num)
            ;;
        *)
            formatted_output=$(ward::logging::log_simple "$level_name" "$message" $level_num)
            ;;
    esac

    # Output to console
    echo "$formatted_output"

    # Output to file if enabled
    if [[ "$WARD_LOG_TO_FILE" == "true" ]]; then
        ward::logging::rotate_if_needed
        echo "$formatted_output" >> "$WARD_LOG_FILE"
    fi

    # Output to syslog if enabled
    if [[ "$WARD_LOG_TO_SYSLOG" == "true" ]]; then
        logger -t "ward" -p "${level_name,,}" "$message"
    fi

    # Update metrics
    if [[ "$WARD_LOG_METRICS_ENABLED" == "true" ]]; then
        local metric_key="log_count_${level_name,,}"
        WARD_LOG_METRICS["$metric_key"]=$((${WARD_LOG_METRICS["$metric_key"]:-0} + 1))
    fi
}

# Flush log buffer
ward::logging::flush_buffer() {
    if [[ ${#WARD_LOG_BUFFER[@]} -gt 0 ]]; then
        for entry in "${WARD_LOG_BUFFER[@]}"; do
            echo "$entry" >> "$WARD_LOG_FILE"
        done
        WARD_LOG_BUFFER=()
    fi
}

# Logging convenience functions
ward::trace() { ward::logging::log "TRACE" "$@"; }
ward::debug() { ward::logging::log "DEBUG" "$@"; }
ward::info() { ward::logging::log "INFO" "$@"; }
ward::warn() { ward::logging::log "WARN" "$@"; }
ward::error() { ward::logging::log "ERROR" "$@"; }
ward::fatal() { ward::logging::log "FATAL" "$@"; exit 1; }

# Performance logging
ward::logging::perf() {
    local operation="$1"
    local duration="$2"
    local unit="${3:-ms}"

    if [[ "$WARD_LOG_METRICS_ENABLED" == "true" ]]; then
        WARD_LOG_METRICS["perf_${operation}"]="$duration$unit"
        ward::debug "Performance: $operation took $duration$unit"
    fi
}

# Context-aware logging with correlation ID
ward::logging::context() {
    local correlation_id="${WARD_CORRELATION_ID:-$(date +%s%N)}"
    local level="$1"
    shift

    ward::logging::log "$level" "[cid:$correlation_id] $@"
}

# Structured event logging
ward::logging::event() {
    local event_type="$1"
    shift
    local event_data="$*"

    local timestamp
    timestamp=$(ward::logging::timestamp)

    if [[ "$WARD_LOG_FORMAT" == "$WARD_LOG_FORMAT_JSON" ]]; then
        echo "{\"timestamp\":\"$timestamp\",\"event\":\"$event_type\",\"data\":\"$(echo "$event_data" | sed 's/"/\\"/g')\"}"
    else
        ward::info "Event: $event_type - $event_data"
    fi
}

# Audit logging for security events
ward::logging::audit() {
    local action="$1"
    local user="${WARD_USER:-$(whoami)}"
    local resource="$2"
    local result="$3"

    local timestamp
    timestamp=$(ward::logging::timestamp)

    if [[ "$WARD_LOG_FORMAT" == "$WARD_LOG_FORMAT_JSON" ]]; then
        echo "{\"timestamp\":\"$timestamp\",\"audit\":true,\"action\":\"$action\",\"user\":\"$user\",\"resource\":\"$resource\",\"result\":\"$result\"}"
    else
        ward::info "AUDIT: $action by $user on $resource ($result)"
    fi
}

# Cleanup function
ward::logging::shutdown() {
    ward::debug "Shutting down logging system"
    ward::logging::flush_buffer
}

# Initialize logging system
ward::logging::init