#!/bin/bash
# Configure Claude Desktop for Ward MCP Integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo -e "${BLUE}🤖 Claude Desktop Ward Integration Setup${NC}"
echo -e "${BLUE}======================================${NC}"

# Detect operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/.config/claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
else
    print_error "Unsupported operating system: $OSTYPE"
    print_info "Ward MCP integration currently supports macOS and Linux"
    exit 1
fi

WARD_MCP_SERVER="$HOME/.ward/mcp/mcp_server.py"

# Check if Ward MCP server exists
if [ ! -f "$WARD_MCP_SERVER" ]; then
    print_error "Ward MCP server not found at $WARD_MCP_SERVER"
    print_info "Please run Ward setup first:"
    print_info "  ./setup-ward.sh"
    exit 1
fi

# Check if python3 is available
if ! command -v python3 >/dev/null 2>&1; then
    print_error "Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if MCP dependencies are installed
if ! python3 -c "import mcp" 2>/dev/null; then
    print_warning "MCP dependencies not found. Installing..."
    pip3 install --user mcp fastmcp
    print_status "MCP dependencies installed"
fi

# Create config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Backup existing config
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    BACKUP_FILE="$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    print_warning "Backing up existing Claude config to $BACKUP_FILE"
    cp "$CLAUDE_CONFIG_FILE" "$BACKUP_FILE"
fi

# Function to create or update Claude config
update_claude_config() {
    local config_file="$1"
    local mcp_server_path="$2"

    # Read existing config or create new
    if [ -f "$config_file" ]; then
        # Use Python to properly merge JSON
        python3 << EOF
import json
import os

config_file = "$config_file"
mcp_server = "$mcp_server_path"

# Create MCP server configuration
ward_config = {
    "mcpServers": {
        "ward-security": {
            "command": "python3",
            "args": [mcp_server],
            "description": "Ward Security System - AI Assistant Protection",
            "category": "security",
            "enabled": True
        }
    }
}

try:
    with open(config_file, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}
except json.JSONDecodeError as e:
    print(f"Warning: Invalid JSON in config file: {e}")
    config = {}

# Merge configurations
if "mcpServers" not in config:
    config["mcpServers"] = {}

config["mcpServers"]["ward-security"] = ward_config["mcpServers"]["ward-security"]

# Write updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ Claude Desktop configured successfully")
print(f"📁 Config file: {config_file}")
EOF
    else
        # Create new config
        cat > "$config_file" << EOF
{
  "mcpServers": {
    "ward-security": {
      "command": "python3",
      "args": ["$mcp_server_path"],
      "description": "Ward Security System - AI Assistant Protection",
      "category": "security",
      "enabled": true
    }
  }
}
EOF
    fi
}

# Update Claude configuration
print_status "Configuring Claude Desktop for Ward integration..."
update_claude_config "$CLAUDE_CONFIG_FILE" "$WARD_MCP_SERVER"

# Test MCP server
print_status "Testing Ward MCP server..."
if timeout 5 python3 "$WARD_MCP_SERVER" --test 2>/dev/null || python3 -c "
import sys
sys.path.insert(0, '$(dirname $WARD_MCP_SERVER)')
from mcp_server import app
print('✅ MCP server validation successful')
" 2>/dev/null; then
    print_status "MCP server test passed"
else
    print_warning "MCP server test failed. The configuration may still work, but please verify:"
    print_warning "  1. Restart Claude Desktop"
    print_warning "  2. Check Claude Desktop logs for MCP errors"
    print_warning "  3. Test with: python3 $WARD_MCP_SERVER"
fi

# Create validation script
cat > "$CLAUDE_CONFIG_DIR/validate_ward_mcp.sh" << 'EOF'
#!/bin/bash
# Validate Ward MCP integration

WARD_MCP_SERVER="$HOME/.ward/mcp/mcp_server.py"

echo "🔍 Validating Ward MCP integration..."

# Check if MCP server exists
if [ ! -f "$WARD_MCP_SERVER" ]; then
    echo "❌ Ward MCP server not found"
    exit 1
fi

# Test MCP server functionality
if timeout 10 python3 "$WARD_MCP_SERVER" 2>/dev/null; then
    echo "✅ MCP server is running correctly"
else
    echo "❌ MCP server test failed"
    exit 1
fi

# Check Claude config
CLAUDE_CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    if grep -q "ward-security" "$CLAUDE_CONFIG_FILE"; then
        echo "✅ Claude Desktop is configured for Ward"
    else
        echo "❌ Claude Desktop not configured for Ward"
        exit 1
    fi
else
    echo "❌ Claude Desktop config not found"
    exit 1
fi

echo "🎉 Ward MCP integration is working correctly!"
EOF

chmod +x "$CLAUDE_CONFIG_DIR/validate_ward_mcp.sh"

# Create Claude Desktop usage examples
cat > "$CLAUDE_CONFIG_DIR/ward_mcp_examples.md" << 'EOF'
# Ward MCP Integration Examples

## Claude Desktop + Ward Security

With Ward MCP integration, Claude can:

### 🛡️ Security Operations
```claude
# Check security policies for current directory
ward_check

# Get system security status
ward_status

# Validate all policies
ward_validate
```

### 📋 Permission Management
```claude
# Allow file modification in specific scope
ward_allow_operation --operation file_modification --scope ./src --justification "Bug fixes for authentication module"

# Allow temporary system access
ward_allow_operation --operation system_access --justification "Checking system configuration for deployment"
```

### 🔍 AI Assistance
```claude
# Get recent AI activity
ward_ai_log --timeframe 1h

# Create AI-safe policy
ward_create_policy --description "Backend API development" --ai_mode enabled --whitelist "ls cat grep python pip git"
```

## Setup Verification

1. Open Claude Desktop
2. Look for "Ward Security" in the tools list
3. Try the examples above
4. Run validation script: `validate_ward_mcp.sh`

## Troubleshooting

If Ward tools don't appear in Claude Desktop:
1. Restart Claude Desktop
2. Check Claude Desktop logs
3. Run validation script
4. Verify MCP server: `python3 ~/.ward/mcp/mcp_server.py`
EOF

echo ""
echo -e "${GREEN}🎉 Claude Desktop Ward integration completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. 🔄 Restart Claude Desktop"
echo "2. 🧪 Test integration:"
echo -e "   ${YELLOW}validate_ward_mcp.sh${NC}"
echo "3. 📚 Check examples:"
echo -e "   ${YELLOW}$CLAUDE_CONFIG_DIR/ward_mcp_examples.md${NC}"
echo ""
echo -e "${BLUE}Claude Desktop should now show Ward Security tools!${NC}"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "- Restart Claude Desktop to activate changes"
echo "- Look for 'Ward Security' in Claude's tool list"
echo "- Check Claude Desktop logs if tools don't appear"
echo "- Run validation script to verify integration"