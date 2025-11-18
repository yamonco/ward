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

# Add to PATH in various shell configs
update_shell_config() {
    local config_file="$1"
    local shell_name="$2"

    if [ -f "$config_file" ] && ! grep -q "$INSTALL_DIR" "$config_file"; then
        echo "" >> "$config_file"
        echo "# Ward Security System" >> "$config_file"
        echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$config_file"
        print_status "Added to $shell_name configuration"
    fi
}

print_status "Updating shell configurations..."
update_shell_config "$HOME/.bashrc" "Bash"
update_shell_config "$HOME/.zshrc" "Zsh"
update_shell_config "$HOME/.profile" "Profile"

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

# Installation complete
echo ""
echo -e "${GREEN}🎉 Ward Security System installed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Restart your terminal or run:"
echo -e "   ${YELLOW}export PATH=\"$INSTALL_DIR:\$PATH\"${NC}"
echo ""
echo "2. Verify installation:"
echo -e "   ${YELLOW}ward --version${NC}"
echo ""
echo "3. Check system status:"
echo -e "   ${YELLOW}ward-cli status${NC}"
echo ""
echo "4. Initialize your first project:"
echo -e "   ${YELLOW}mkdir my-secure-project && cd my-secure-project${NC}"
echo -e "   ${YELLOW}ward-init --here${NC}"
echo ""
echo "5. For more help:"
echo -e "   ${YELLOW}ward-cli help${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC} https://github.com/yamonco/ward#readme"
echo -e "${BLUE}Issues:${NC} https://github.com/yamonco/ward/issues"
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