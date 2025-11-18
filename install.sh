#!/usr/bin/env bash
# Ward Security System - One-Click Installer
# Easy installation with MCP support for Claude Desktop

set -euo pipefail

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
header() { print_msg "$PURPLE" "🛡️  $*"; }

# Check dependencies
check_dependencies() {
    local missing_deps=()

    # Check for Python
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi

    # Check for pip
    if ! command -v pip3 >/dev/null 2>&1 && ! command -v pip >/dev/null 2>&1; then
        missing_deps+=("pip")
    fi

    # Check for UVX (optional but recommended)
    if ! command -v uvx >/dev/null 2>&1; then
        warning "UVX not found - will use pip instead"
        info "Install UVX for easier management: pip install uv"
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing dependencies: ${missing_deps[*]}"
        echo
        info "Please install missing dependencies and try again:"
        for dep in "${missing_deps[@]}"; do
            case "$dep" in
                "python3")
                    echo "  • Ubuntu/Debian: sudo apt install python3"
                    echo "  • macOS: brew install python"
                    echo "  • Windows: Download from python.org"
                    ;;
                "pip")
                    echo "  • Ubuntu/Debian: sudo apt install python3-pip"
                    echo "  • macOS: python3 -m ensurepip --upgrade"
                    echo "  • Windows: Use python installer with pip option"
                    ;;
            esac
        done
        return 1
    fi

    return 0
}

# Install Ward with MCP support
install_ward() {
    header "Installing Ward Security System"

    local install_cmd

    # Prefer UVX if available
    if command -v uvx >/dev/null 2>&1; then
        info "Using UVX for installation..."
        install_cmd="uv tool install git+https://github.com/yamonco/ward.git"
        success "UVX will automatically install Ward with MCP support"
    else
        info "Using pip for installation..."
        install_cmd="pip3 install git+https://github.com/yamonco/ward.git"
    fi

    echo
    info "Running: $install_cmd"
    echo

    if eval "$install_cmd"; then
        success "Ward Security System installed successfully!"
        return 0
    else
        error "Installation failed"
        return 1
    fi
}

# Configure Claude Desktop MCP integration
configure_claude_mcp() {
    header "Configuring Claude Desktop MCP Integration"

    # Try to use ward-mcp CLI if available
    if command -v ward-mcp >/dev/null 2>&1; then
        info "Using ward-mcp CLI for configuration..."
        if ward-mcp add; then
            success "Claude Desktop MCP integration configured!"
            return 0
        else
            warning "ward-mcp CLI configuration failed, trying manual setup..."
        fi
    fi

    # Manual configuration as fallback
    manual_claude_config
}

# Manual Claude Desktop configuration
manual_claude_config() {
    info "Setting up manual Claude Desktop configuration..."

    # Determine config directory
    local config_dir
    case "$(uname -s)" in
        Darwin*)
            config_dir="$HOME/Library/Application Support/Claude"
            ;;
        Linux*)
            config_dir="$HOME/.config/Claude"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            config_dir="$HOME/AppData/Roaming/Claude"
            ;;
        *)
            error "Unsupported operating system"
            return 1
            ;;
    esac

    local config_file="$config_dir/claude_desktop_config.json"

    # Create config directory if needed
    mkdir -p "$config_dir"

    # Backup existing config
    if [ -f "$config_file" ]; then
        local backup_file="$config_file.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$config_file" "$backup_file"
        success "Backed up existing config to $backup_file"
    fi

    # Create or update config
    local temp_config=$(mktemp)

    if [ -f "$config_file" ]; then
        # Update existing config
        python3 -c "
import json
import sys

with open('$config_file', 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add Ward MCP server
config['mcpServers']['ward-security'] = {
    'command': 'uvx' if command -v uvx >/dev/null 2>&1 else 'ward-mcp-server',
    'args': ['git+https://github.com/yamonco/ward.git', 'python', '-m', 'ward_security.mcp_server'] if command -v uvx >/dev/null 2>&1 else [],
    'description': 'Ward Security System - AI-powered terminal protection'
}

with open('$temp_config', 'w') as f:
    json.dump(config, f, indent=2)
"
    else
        # Create new config
        cat > "$temp_config" << 'EOF'
{
  "mcpServers": {
    "ward-security": {
      "command": "uvx",
      "args": ["git+https://github.com/yamonco/ward.git", "python", "-m", "ward_security.mcp_server"],
      "description": "Ward Security System - AI-powered terminal protection"
    }
  }
}
EOF
    fi

    # Install the configuration
    mv "$temp_config" "$config_file"
    success "Claude Desktop configuration updated!"

    info "Configuration file: $config_file"
    return 0
}

# Test installation
test_installation() {
    header "Testing Installation"

    # Test Ward CLI
    if command -v ward >/dev/null 2>&1 || python3 -c "import ward_security" 2>/dev/null; then
        success "Ward CLI is available"
    else
        error "Ward CLI not found"
        return 1
    fi

    # Test MCP installer
    if command -v ward-mcp >/dev/null 2>&1 || python3 -c "import ward_security.mcp_installer" 2>/dev/null; then
        success "Ward MCP installer is available"
    else
        warning "Ward MCP installer not found"
    fi

    # Test MCP server
    if python3 -c "import ward_security.mcp_server" 2>/dev/null; then
        success "Ward MCP server is available"
    else
        warning "Ward MCP server not found - check MCP dependencies"
    fi

    return 0
}

# Show next steps
show_next_steps() {
    header "Installation Complete!"

    echo
    success "🎉 Ward Security System has been installed successfully!"
    echo

    info "📚 Quick Start:"
    echo "1. Restart Claude Desktop to activate MCP integration"
    echo "2. In Claude, try: 'ward_check .' to check current directory"
    echo "3. Try: 'ward_plant my-project' to create protection"
    echo

    info "🔧 Available Commands:"
    echo "• ward - Main Ward CLI"
    echo "• ward-mcp - MCP installation and configuration"
    echo "• ward-mcp-server - Direct MCP server (for advanced use)"
    echo

    info "🤖 Claude Integration:"
    echo "• Ward tools are now available in Claude conversations"
    echo "• Use 'ward_' commands to interact with Ward from Claude"
    echo "• Ask Claude: 'What Ward tools are available?'"
    echo

    info "📖 Documentation:"
    echo "• Project: https://github.com/yamonco/ward"
    echo "• Help: ward-mcp info"
    echo "• Status: ward-mcp status"
    echo

    if command -v uvx >/dev/null 2>&1; then
        info "🔍 Management with UVX:"
        echo "• Update: uv tool install --force git+https://github.com/yamonco/ward.git"
        echo "• Remove: uv tool uninstall ward"
    else
        info "🔍 Management with pip:"
        echo "• Update: pip install --upgrade git+https://github.com/yamonco/ward.git"
        echo "• Remove: pip uninstall ward-security"
    fi
}

# Main installation flow
main() {
    echo
    header "Ward Security System - One-Click Installer"
    echo "🤖 AI-Powered Terminal Protection with Claude Desktop Integration"
    echo

    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi

    echo
    # Install Ward
    if ! install_ward; then
        exit 1
    fi

    echo
    # Configure Claude Desktop
    if ! configure_claude_mcp; then
        warning "Claude Desktop configuration failed"
        info "You can configure it later with: ward-mcp add"
    fi

    echo
    # Test installation
    test_installation

    echo
    # Show next steps
    show_next_steps
}

# Handle command line arguments
case "${1:-install}" in
    "install"|"")
        main
        ;;
    "check")
        check_dependencies && success "All dependencies satisfied" || error "Missing dependencies"
        ;;
    "ward-only")
        check_dependencies && install_ward
        ;;
    "mcp-only")
        configure_claude_mcp
        ;;
    "help"|"-h"|"--help")
        echo "Ward Security System Installer"
        echo
        echo "USAGE: $0 [COMMAND]"
        echo
        echo "COMMANDS:"
        echo "  install     Install Ward and configure Claude MCP (default)"
        echo "  check       Check dependencies"
        echo "  ward-only   Install Ward without MCP configuration"
        echo "  mcp-only    Configure MCP integration only"
        echo "  help        Show this help"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac