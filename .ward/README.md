# Ward Security System v2.0

Enterprise-grade file system protection with AI collaboration features

## Overview

Ward Security is an advanced file system protection system that provides granular policy-based access control, automated environment integration, and AI-powered collaboration tools. Built for enterprise environments with extensibility and professional-grade architecture in mind.

## 🚀 Key Features

### Core Capabilities
- **Policy-Based Security**: Granular, hierarchical policy enforcement
- **Automatic Integration**: Zero-configuration shell and IDE integration
- **AI Collaboration**: Intelligent prompting and comment management
- **Enterprise Authentication**: Password-based access control with session management
- **Cross-Platform**: Linux, macOS, and Windows (PowerShell) support
- **Plugin Architecture**: Extensible system with custom security modules
- **Structured Logging**: Comprehensive audit trail and performance metrics

### Architecture Highlights
- **Modular Design**: Clean separation of concerns with core, plugin, and CLI modules
- **Professional Error Handling**: Comprehensive error codes and recovery mechanisms
- **Configuration Management**: Hot-reload configuration with validation
- **Performance Optimization**: Caching and parallel evaluation
- **Security-First**: Built-in security validations and protections

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Policy Management](#policy-management)
- [Plugins](#plugins)
- [Enterprise Features](#enterprise-features)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Prerequisites

- Bash 4.0+ or compatible shell
- Core utilities: find, grep, sed, awk, wc
- Optional: Git, PowerShell (Windows)

### Installation

```bash
# Automated installation (recommended)
./setup-ward.sh

# Manual installation
./ward-cli install

# Verify installation
./ward-cli version
```

### Basic Usage

```bash
# Check system status
./ward-cli status

# Analyze policies for a directory
./ward-cli check ./frontend

# Execute in protected environment
./ward-shell
```

## 🔧 Installation

### Automated Installation

The `setup-ward.sh` script provides a complete, automated installation experience:

```bash
./setup-ward.sh
```

This script:
- Detects system requirements
- Configures shell integration
- Sets up plugins and extensions
- Validates the installation
- Provides platform-specific instructions

### Manual Installation

For custom installations:

1. **Core System**
   ```bash
   cp .ward/ward-cli.sh /usr/local/bin/ward
   chmod +x /usr/local/bin/ward
   ```

2. **Shell Integration**
   ```bash
   # Bash
   echo 'source "$(pwd)/.ward/auto-ward.sh"' >> ~/.bashrc

   # Zsh
   echo 'source "$(pwd)/.ward/auto-ward.sh"' >> ~/.zshrc

   # PowerShell
   . .ward/auto-ward.ps1 -Action install
   ```

3. **VS Code Integration**
   ```bash
   # Automatic setup included in installation
   ```

### Verification

```bash
./ward-cli version
./ward-cli status
```

## ⚙️ Configuration

### Configuration File Structure

Configuration is managed through `ward.conf` in the `.ward` directory:

```toml
# Example configuration
[engine]
version = "2.0.0"
debug = false
cache_enabled = true
strict_mode = true

[security]
authentication.enabled = true
session_timeout = 3600
encryption.algorithm = "SHA256"

[logging]
level = "INFO"
format = "structured"
file_enabled = true
file_path = ".ward/logs/ward.log"
```

### Configuration Management

```bash
# Show current configuration
./ward-cli config show

# Get specific configuration value
./ward-cli config get engine.debug

# Set configuration value
./ward-cli config set engine.debug true

# Reload configuration
./ward-cli config reload
```

### Environment Variables

Configuration can be overridden using environment variables:

```bash
export WARD_LOG_LEVEL=DEBUG
export WARD_STRICT_MODE=true
export WARD_PLUGIN_DIR=/custom/plugins
./ward-cli status
```

## 📖 Usage

### Core Commands

```bash
# System Status
./ward-cli status

# Policy Analysis
./ward-cli check <path>

# Validation
./ward-cli validate

# Debug Information
./ward-cli debug <path>

# Authentication
./ward-cli auth status
./ward-cli auth set-password

# Plugin Management
./ward-cli plugin list
./ward-cli plugin load <plugin-name>
```

### Command Line Options

```bash
# Verbose output
./ward-cli -v status

# Quiet mode
./ward-cli -q validate

# Force operations
./ward-cli -f deploy /target/path

# Help
./ward-cli help
./ward-cli help plugins
```

### Policy Examples

Create `.ward` files in directories to define security policies:

```yaml
# Simple policy file
@description: Frontend application directory
@whitelist: ls cat touch nano vim
@blacklist: rm mv cp
@lock_new_dirs: true
@allow_comments: true
@max_comments: 5
@comment_prompt: "Explain changes from a frontend architecture perspective"
```

## 🛡️ Policy Management

### Policy Structure

Policies are defined in `.ward` files using a structured format:

```yaml
# Metadata Section
[metadata]
description = "Critical infrastructure directory"
owner = "platform-team"
classification = "restricted"

# Policy Section
[policy]
whitelist = "ls cat pwd grep find"
blacklist = "rm mv cp chmod chown"
lock_new_dirs = true
allow_comments = true
max_comments = 3

# Behavior Section
[behavior]
explain_on_error = true
audit_enabled = true
notification_enabled = false
```

### Policy Inheritance

Policies inherit from parent directories in a hierarchical manner:

1. Parent policies are loaded first
2. Child policies override parent settings
3. The most specific policy takes precedence

### Policy Validation

```bash
# Validate all policies
./ward-cli validate

# Check specific policy syntax
./ward-cli check ./path/to/policy
```

## 🔌 Plugins

### Built-in Plugins

- **Security Audit**: Enhanced security logging and monitoring
- **Performance Monitor**: Resource usage and performance metrics
- **Integration Hooks**: Custom system integration points

### Plugin Development

Create custom plugins in `.ward/plugins/`:

```bash
#!/usr/bin/env bash
# Example: audit-plugin.sh

plugin_init() {
    WARD_CURRENT_PLUGIN="audit"
    ward::plugin::register_hook "post_command_execution" "audit_log_command"
    return 0
}

plugin_info() {
    echo "Audit Plugin v1.0 - Enhanced security logging"
    return 0
}

plugin_cleanup() {
    # Cleanup resources
    return 0
}

audit_log_command() {
    local command="$1"
    local exit_code="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] AUDIT: Command '$command' executed with exit code $exit_code" >> /var/log/ward/audit.log
}
```

### Plugin Management

```bash
# List available plugins
./ward-cli plugin list

# Plugin information
./ward-cli plugin info audit

# Load/unload plugins
./ward-cli plugin load audit
./ward-cli plugin unload audit

# Enable/disable plugins
./ward-cli plugin enable audit
./ward-cli plugin disable audit
```

## 🏢 Enterprise Features

### Authentication & Authorization

```bash
# Password-based authentication
./ward-cli auth set-password

# Session management
./ward-cli auth status

# Deploy with authentication
./ward-cli deploy /production --auth
```

### Audit & Compliance

```bash
# Enable audit logging
./ward-cli config set engine.audit_enabled true

# View audit logs
./ward-cli logs audit

# Generate compliance report
./ward-cli audit report --format json
```

### Performance Monitoring

```bash
# Enable performance metrics
./ward-cli config set logging.metrics_enabled true

# View performance metrics
./ward-cli metrics

# Export metrics to monitoring systems
./ward-cli metrics export --format prometheus
```

### Integration APIs

#### Shell Integration

```bash
# Automatic integration
source .ward/auto-ward.sh

# Manual integration
export WARD_ROOT=$(pwd)
export BASH_ENV="$WARD_ROOT/.ward/guard.sh"
```

#### CI/CD Integration

```yaml
# GitHub Actions example
- name: Ward Security Check
  run: |
    ./ward-cli validate
    ./ward-cli check ./
    ./ward-cli deploy ./artifacts --auth
```

## 📚 API Reference

### Core API Functions

#### Engine API

```bash
# Path resolution
resolved_path=$(ward::resolve_path "$path")

# Policy discovery
policies=($(ward::PolicyEngine discover_policies "$path"))

# Policy parsing
policy_data=$(ward::PolicyEngine parse_policy "$policy_file")
```

#### Configuration API

```bash
# Get configuration
debug_enabled=$(ward::config::get "engine.debug" "false")

# Set configuration
ward::config::set "engine.debug" "true"

# Validate configuration
ward::config::validate_all
```

#### Logging API

```bash
# Structured logging
ward::logging::info "System operation completed"

# Performance logging
ward::logging::perf "policy_evaluation" "150" "ms"

# Audit logging
ward::logging::audit "file_access" "/etc/passwd" "denied"
```

#### Plugin API

```bash
# Register hooks
ward::plugin::register_hook "pre_command_execution" "security_check"

# Execute hooks
ward::plugin::execute_hooks "pre_command_execution" "$cmd" "$args"
```

### CLI API

#### Command Registration

```bash
# Register custom command
ward_cli::register_command "mycmd" "my_command_function" "Description"

# Execute command
ward_cli::execute_command "mycmd" "$@"
```

#### CLI Utilities

```bash
# Output formatting
ward_cli::success "Operation completed"
ward_cli::error "Operation failed"
ward_cli::warning "Warning message"
ward_cli::info "Information message"
```

## 🔍 Troubleshooting

### Common Issues

#### Permission Denied Errors

```bash
# Check policy configuration
./ward-cli check <path>

# Verify policy syntax
./ward-cli validate

# Check authentication status
./ward-cli auth status
```

#### Plugin Issues

```bash
# Check plugin status
./ward-cli plugin list

# Reload plugins
./ward-cli plugin reload <plugin>

# Check plugin logs
./ward-cli logs plugin
```

#### Configuration Issues

```bash
# Validate configuration
./ward-cli config validate

# Show current configuration
./ward-cli config show

# Check configuration source
./ward-cli config show | grep source
```

### Debug Mode

Enable verbose debugging:

```bash
# Enable debug logging
./ward-cli config set logging.level DEBUG

# Run with verbose flag
./ward-cli -v status

# Check system state
./ward-cli debug
```

### Log Analysis

```bash
# View recent logs
tail -f .ward/logs/ward.log

# Search for errors
grep "ERROR" .ward/logs/ward.log

# Filter by component
grep "engine:" .ward/logs/ward.log
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Plugin Development

1. Create plugin in `.ward/plugins/`
2. Follow the plugin template
3. Register appropriate hooks
4. Test thoroughly
5. Document the plugin

### Code Standards

- Follow Bash 4.0+ best practices
- Use `ward::` namespace for all functions
- Implement proper error handling
- Include comprehensive documentation
- Add unit tests

## 📄 License

Ward Security System v2.0
Enterprise License - See LICENSE file for details

## 📞 Support

- **Documentation**: [Ward Security Wiki](https://ward-security.example.com/wiki)
- **Issues**: [GitHub Issues](https://github.com/ward-security/ward/issues)
- **Community**: [Discord Server](https://discord.gg/ward-security)
- **Enterprise**: [Enterprise Support](mailto:enterprise@ward-security.com)