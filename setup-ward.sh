#!/bin/bash
set -e

# Ward Security System - Setup Script
# This script installs Ward Security System

WARD_VERSION="2.0.0"
INSTALL_DIR="$HOME/.ward"
BACKUP_DIR="$HOME/.ward_backup_$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Ward Security System Setup${NC}"
echo -e "${BLUE}===================================${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root. Ward should be installed as a regular user."
    exit 1
fi

# Backup existing installation if it exists
if [ -d "$INSTALL_DIR" ]; then
    print_warning "Existing Ward installation found in $INSTALL_DIR"
    echo "Creating backup in $BACKUP_DIR..."
    mv "$INSTALL_DIR" "$BACKUP_DIR"
    print_status "Backup created successfully"
fi

# Create installation directory
print_status "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy Ward files
print_status "Installing Ward Security System..."
cp -r "$SCRIPT_DIR/.ward"/* "$INSTALL_DIR/"

# Create symlinks for main commands
print_status "Creating command symlinks..."
if [ ! -L "$INSTALL_DIR/ward" ]; then
    ln -sf "$INSTALL_DIR/ward.sh" "$INSTALL_DIR/ward"
fi

if [ ! -L "$INSTALL_DIR/ward-init" ]; then
    ln -sf "$INSTALL_DIR/ward-cli.sh" "$INSTALL_DIR/ward-init"
fi

# Make scripts executable
print_status "Setting permissions..."
chmod +x "$INSTALL_DIR"/*.sh
chmod +x "$INSTALL_DIR"/core/*.sh
chmod +x "$INSTALL_DIR"/ward
chmod +x "$INSTALL_DIR"/ward-init

# Install MCP server
install_mcp_server() {
    print_status "Installing Ward MCP Server..."

    # Create MCP directory
    mkdir -p "$INSTALL_DIR/mcp"

    # Deploy MCP server
    if [ -f "$SCRIPT_DIR/src/ward_security/mcp_server.py" ]; then
        cp "$SCRIPT_DIR/src/ward_security/mcp_server.py" "$INSTALL_DIR/mcp/"
        chmod +x "$INSTALL_DIR/mcp/mcp_server.py"
        print_status "MCP Server installed successfully"

        # Create MCP configuration
        cat > "$INSTALL_DIR/mcp/ward.fastmcp.json" << 'EOF'
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "entrypoint": "mcp_server.py",
  "environment": {
    "dependencies": ["mcp>=0.1.0", "click>=8.0.0", "pyyaml>=6.0"]
  },
  "tool_definitions": {
    "ward_check": {
      "description": "Check Ward policies for a path",
      "category": "security"
    },
    "ward_status": {
      "description": "Get Ward system status",
      "category": "security"
    },
    "ward_allow_operation": {
      "description": "Allow AI operation in scope",
      "category": "authorization"
    }
  }
}
EOF
        print_status "MCP configuration created"
    else
        print_warning "MCP server source not found. MCP features will be limited."
    fi
}

# Install MCP dependencies
install_mcp_dependencies() {
    if command -v pip3 >/dev/null 2>&1; then
        print_status "Installing MCP dependencies..."

        # Try to install MCP dependencies
        if pip3 install --user mcp fastmcp 2>/dev/null; then
            print_status "MCP dependencies installed successfully"
        else
            print_warning "MCP dependencies installation failed. Install manually:"
            print_warning "  pip install --user mcp fastmcp"
        fi
    else
        print_warning "pip3 not found. Install Python and pip for MCP support."
    fi
}

# Install MCP components
print_status "Setting up MCP integration..."
install_mcp_dependencies
install_mcp_server

# Ward is intentionally local-only - no global PATH modification
print_warning "Ward is installed locally only - no global PATH changes made"
print_status "This prevents accidental global access and maintains security boundaries"

# Create local wrapper script for user convenience
create_local_wrapper() {
    local wrapper_dir="$HOME/.local/bin"
    if [ ! -d "$wrapper_dir" ]; then
        mkdir -p "$wrapper_dir"
    fi

    # Create local ward wrapper that points to installation
    cat > "$wrapper_dir/ward" << EOF
#!/bin/bash
# Ward Security System - Local Wrapper
# This wrapper ensures Ward runs from its local installation

WARD_HOME="$INSTALL_DIR"

if [ ! -d "\$WARD_HOME" ]; then
    echo "❌ Ward installation not found at \$WARD_HOME"
    echo "Please run ./setup-ward.sh from the Ward source directory"
    exit 1
fi

# Execute ward from local installation
exec "\$WARD_HOME/ward" "\$@"
EOF

    chmod +x "$wrapper_dir/ward"
    print_status "Local wrapper created at $wrapper_dir/ward"
}

# Create local wrapper for user convenience
create_local_wrapper

# Create a sample .ward file in user's home directory (optional)
SAMPLE_WARD="$HOME/.ward_example"
if [ ! -f "$SAMPLE_WARD" ]; then
    print_status "Creating example .ward file..."
    cat > "$SAMPLE_WARD" << 'EOF'
# Ward Security Configuration Example
@description: Example secure project
@whitelist: ls cat pwd echo grep sed awk git nano vim code
@blacklist: rm -rf /* dd format fdisk sudo su
@allow_comments: true
@max_comments: 5
@comment_prompt: "Explain changes from a security perspective"
EOF
    print_status "Example configuration created at $SAMPLE_WARD"
fi

# Function to add UV tools PATH to shell configuration
add_uv_tools_path() {
    local uv_tools_path="$HOME/.local/share/uv/tools/ward-security/bin"
    local shell_rc=""

    # Detect shell and appropriate config file
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
        shell_rc="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
        shell_rc="$HOME/.bashrc"
    fi

    if [ -n "$shell_rc" ] && [ -f "$shell_rc" ]; then
        # Check if UV tools path is already in the config
        if ! grep -q "$uv_tools_path" "$shell_rc" 2>/dev/null; then
            echo "" >> "$shell_rc"
            echo "# UV tools path for Ward Security System" >> "$shell_rc"
            echo "export PATH=\"$uv_tools_path:\$PATH\"" >> "$shell_rc"
            print_status "UV tools path added to $shell_rc"
        else
            print_status "UV tools path already configured in $shell_rc"
        fi
    fi
}

# Function to install Ward with UV (preferred method)
install_with_uv() {
    if command -v uv >/dev/null 2>&1; then
        print_status "Installing Ward with UV (recommended)..."

        # Install Ward with MCP support
        if uv tool install "git+https://github.com/yamonco/ward.git[mcp]" 2>/dev/null; then
            print_status "Ward installed successfully with UV!"

            # Add UV tools path to shell configuration
            add_uv_tools_path

            # Configure Claude MCP automatically
            if command -v uvx >/dev/null 2>&1; then
                print_status "Configuring Claude MCP integration..."
                if uvx --help >/dev/null 2>&1; then
                    # Use uvx to run ward-mcp
                    if uvx "git+https://github.com/yamonco/ward.git" ward-mcp add --target claude-code 2>/dev/null; then
                        print_status "Claude MCP integration configured!"
                    else
                        print_warning "Claude MCP configuration failed. Run manually: uvx git+https://github.com/yamonco/ward.git ward-mcp add"
                    fi
                fi
            else
                print_warning "UVX not found. Install UVX for automatic MCP integration: pip install uvx"
            fi

            return 0
        else
            print_warning "UV installation failed, falling back to local installation"
            return 1
        fi
    else
        print_warning "UV not found. Install UV for better experience: https://docs.astral.sh/uv/"
        return 1
    fi
}

# Try UV installation first, fallback to local
if install_with_uv; then
    # Apply PATH to current session immediately
    UV_TOOLS_PATH="$HOME/.local/share/uv/tools/ward-security/bin"
    export PATH="$UV_TOOLS_PATH:$PATH"

    echo ""
    echo -e "${GREEN}🎉 Ward Security System installed with UV!${NC}"
    echo ""
    echo -e "${BLUE}🔧 PATH configured for current session${NC}"
    echo -e "   ${YELLOW}export PATH=\"$UV_TOOLS_PATH:\$PATH\"${NC}"
    echo ""
    echo -e "${BLUE}✅ Testing installation immediately...${NC}"

    # Test Ward command immediately
    if command -v ward >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Ward command is now available${NC}"
        echo -e "   📱 Version: $(ward --version 2>/dev/null || echo 'Unknown')${NC}"
    else
        echo -e "${YELLOW}   ⚠️ Ward command found but may need shell reload${NC}"
    fi

    echo ""
    echo -e "${BLUE}🔄 Next steps:${NC}"
    echo "1. For future sessions, shell will automatically load PATH"
    echo "2. For current session, Ward is ready to use!"
    echo ""
    echo "3. Verify installation:"
    echo -e "   ${YELLOW}ward --version${NC}"
    echo -e "   ${YELLOW}uv tool list | grep ward${NC}"
    echo ""
    echo "4. Initialize your first project:"
    echo -e "   ${YELLOW}mkdir my-secure-project && cd my-secure-project${NC}"
    echo -e "   ${YELLOW}ward init${NC}"
    echo ""
    echo "5. 🤖 AI Assistant Integration (MCP):"
    echo -e "   ${YELLOW}# Already configured! Restart Claude Code to use Ward tools${NC}"
    echo ""
    echo -e "${BLUE}Management commands:${NC}"
    echo -e "   ${YELLOW}uv tool install --force git+https://github.com/yamonco/ward.git  # Update${NC}"
    echo -e "   ${YELLOW}uv tool uninstall ward-security  # Remove${NC}"
else
    # Fallback to local installation (existing code)
    echo ""
    echo -e "${GREEN}🎉 Ward Security System installed locally!${NC}"
    echo ""
    echo -e "${BLUE}🔒 Security Notice:${NC}"
    echo "Ward is installed locally only - no global system changes made"
    echo "This prevents accidental global access and maintains security boundaries"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Add local bin to PATH (optional, for convenience only):"
    echo -e "   ${YELLOW}echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> \$HOME/.bashrc${NC}"
    echo -e "   ${YELLOW}source \$HOME/.bashrc${NC}"
    echo ""
    echo "2. Or use Ward directly from its installation:"
    echo -e "   ${YELLOW}$INSTALL_DIR/ward --version${NC}"
    echo ""
    echo "3. Check system status:"
    echo -e "   ${YELLOW}$INSTALL_DIR/ward status${NC}"
    echo ""
    echo "4. Initialize your first project:"
    echo -e "   ${YELLOW}mkdir my-secure-project && cd my-secure-project${NC}"
    echo -e "   ${YELLOW}$INSTALL_DIR/ward init${NC}"
    echo ""
    echo "5. For more help:"
    echo -e "   ${YELLOW}$INSTALL_DIR/ward help${NC}"
    echo ""
    echo "6. 🤖 AI Assistant Integration (MCP):"
    echo -e "   ${YELLOW}# Test MCP server${NC}"
    echo -e "   ${YELLOW}python3 $INSTALL_DIR/mcp/mcp_server.py${NC}"
    echo ""
    echo -e "   ${YELLOW}# Configure Claude Desktop (macOS)${NC}"
    echo -e "   ${YELLOW}./configure-claude-desktop.sh${NC}"
fi

echo ""
echo -e "${BLUE}Documentation:${NC} https://github.com/yamonco/ward#readme"
echo -e "${BLUE}Issues:${NC} https://github.com/yamonco/ward/issues"
echo -e "${BLUE}MCP Guide:${NC} https://github.com/yamonco/ward/wiki/MCP-Integration"

# If UV installation succeeded, create quick PATH setup
if command -v uv >/dev/null 2>&1 && uv tool list | grep -q "ward-security"; then
    print_status "Creating quick PATH setup for current session..."

    # Create ward-now script
    cat > "$HOME/.ward-now" << 'EOF'
#!/bin/bash
# Quick Ward PATH setup
UV_TOOLS_PATH="$HOME/.local/share/uv/tools/ward-security/bin"
export PATH="$UV_TOOLS_PATH:$PATH"
echo "✅ Ward PATH configured for this session"
echo "Available commands: ward, ward-mcp, ward-mcp-server"
EOF

    chmod +x "$HOME/.ward-now"
    print_status "Created quick setup: ~/.ward-now"
    print_info "Run: source ~/.ward-now"
    print_info "Or: bash ~/.ward-now"
fi
echo ""

# Test installation
if [ -x "$INSTALL_DIR/ward" ]; then
    print_status "Installation verified successfully!"
    echo ""
    echo -e "${BLUE}Ward version:${NC} $("$INSTALL_DIR/ward" --version 2>/dev/null || echo "Unknown")"
else
    print_error "Installation verification failed. Please check the logs above."
    exit 1
fi