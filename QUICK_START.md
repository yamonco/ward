# Ward Security System - Quick Start Guide

## 🚀 Installation Options

### Option 1: Using UV (Recommended)
```bash
# Install as a tool
uv tool install --from git+https://github.com/yamonco/ward.git ward-security

# Or run directly without installation
uvx --from git+https://github.com/yamonco/ward.git ward-cli status

# Initialize a new project
ward-init my-project
cd my-project
```

### Option 2: Using Docker
```bash
# Pull and run
docker pull yamonco/ward:latest
docker run -it -v $(pwd):/workspace yamonco/ward:latest

# Or mount specific directory
docker run -it -v /path/to/your/project:/workspace yamonco/ward:latest
```

### Option 3: Direct Download
```bash
# Download the latest release
wget https://github.com/yamonco/ward/releases/latest/download/ward-bash.tar.gz

# Extract and install
tar -xzf ward-bash.tar.gz
cd ward-bash
./setup-ward.sh
```

## 🏁 Quick Start

### Initialize a New Project
```bash
# Method 1: With UV (if installed)
ward-init my-project
cd my-project

# Method 2: Manual initialization
mkdir my-project
cd my-project
curl -fsSL https://raw.githubusercontent.com/yamonco/ward/main/setup-ward.sh | bash

# Method 3: With Docker
docker run --rm -v $(pwd):/workspace yamonco/ward:latest ward-init --here
```

### Basic Usage
```bash
# Check system status
ward-cli status

# Analyze current directory policies
ward-cli check .

# Validate all policies
ward-cli validate

# Run in protected shell
ward-shell

# Show help
ward-cli help
```

### Create Your First Policy
```bash
# Create a .ward file in your project directory
echo "@description: My secure project
@whitelist: ls cat pwd echo grep sed awk git
@allow_comments: true
@max_comments: 5
@comment_prompt: \"Explain changes from a security perspective\"" > .ward

# Validate the policy
ward-cli check .
```

### AI Collaboration Features
```bash
# Enable AI collaboration (handle commands)
ward-cli handle add "Refactor authentication module" --comment "Improve security and add rate limiting"

# Show all handles
ward-cli handle list

# Remove a handle
ward-cli handle remove 1

# Add comments with AI prompts
ward-cli comment "This change improves performance by 20%" --context "backend optimization"
```

## 📋 Common Workflows

### Frontend Development
```bash
# Initialize with frontend policy
echo "@description: Frontend application
@whitelist: ls cat pwd echo grep sed awk npm yarn node git code vim nano
@blacklist: rm mv cp chmod chown sudo
@allow_comments: true
@max_comments: 10
@comment_prompt: \"Explain changes from a frontend architecture perspective\"" > .ward

# Work in protected environment
ward-shell

# Your AI copilot can now use handle commands:
# ward-cli handle add "Update React component" --comment "Add new props and improve accessibility"
```

### Backend Development
```bash
# Initialize with backend policy
echo "@description: Backend API server
@whitelist: ls cat pwd echo grep sed awk python pip poetry docker git
@blacklist: rm -rf / rm mv cp sudo su
@allow_comments: true
@max_comments: 8
@comment_prompt: \"Explain changes from a backend security perspective\"" > .ward

# Test configuration
ward-cli validate

# Start development
ward-shell
```

### System Administration
```bash
# Initialize with admin policy
echo "@description: System administration tasks
@whitelist: ls cat pwd echo grep sed awk systemctl journalctl docker kubectl git vim nano
@blacklist: rm -rf /* dd format fdisk
@allow_comments: true
@max_comments: 3
@comment_prompt: \"Explain changes from a system administration perspective\"" > .ward

# Enable audit logging
ward-cli config set engine.audit_enabled true

# Run with enhanced monitoring
ward-cli -v check /etc
```

## 🐳 Docker Usage

### Basic Docker Commands
```bash
# Run Ward in current directory
docker run -it --rm -v $(pwd):/workspace ghcr.io/ward-security/ward-security:latest

# Run with custom policy
docker run -it --rm -v $(pwd):/workspace \
  -e WARD_POLICY_WHITELIST="ls cat pwd echo git" \
  ghcr.io/ward-security/ward-security:latest

# Run in background with specific command
docker run -d --name ward-security \
  -v /path/to/project:/workspace \
  ghcr.io/ward-security/ward-security:latest \
  ward-cli check /workspace
```

### Docker Compose Example
```yaml
# docker-compose.yml
version: '3.8'
services:
  ward-security:
    image: ghcr.io/ward-security/ward-security:latest
    volumes:
      - .:/workspace
    working_dir: /workspace
    environment:
      - WARD_LOG_LEVEL=INFO
      - WARD_POLICY_ALLOW_COMMENTS=true
    command: ward-shell
```

## 🔧 Configuration

### Environment Variables
```bash
export WARD_LOG_LEVEL=DEBUG
export WARD_STRICT_MODE=true
export WARD_PLUGIN_DIR=/custom/plugins
export WARD_AUTH_SESSION_TIMEOUT=7200
```

### Configuration Management
```bash
# Show current configuration
ward-cli config show

# Set configuration values
ward-cli config set engine.debug true
ward-cli config set logging.level DEBUG

# Reload configuration
ward-cli config reload
```

## 🚨 Security Best Practices

### Production Setup
```bash
# Enable authentication
ward-cli auth set-password

# Enable audit logging
ward-cli config set engine.audit_enabled true
ward-cli config set logging.file_enabled true

# Set strict mode
ward-cli config set engine.strict_mode true

# Use environment variables for secrets
export WARD_AUTH_PASSWORD_HASH=$(echo -n "your-password" | sha256sum)
```

### Policy Recommendations
```bash
# Restrict dangerous commands
echo "@blacklist: rm -rf / dd format fdisk sudo su" >> .ward

# Limit directory operations
echo "@lock_new_dirs: true" >> .ward

# Enable AI collaboration with limits
echo "@allow_comments: true
@max_comments: 5" >> .ward
```

## 🆘 Troubleshooting

### Common Issues
```bash
# Check system status
ward-cli status

# Debug mode
ward-cli -v debug .

# Validate policies
ward-cli validate

# Check logs
tail -f .ward/logs/ward.log

# Reset system
ward-cli cleanup --force
```

### Get Help
```bash
# General help
ward-cli help

# Specific topic help
ward-cli help plugins
ward-cli help config

# Show version
ward-cli --version
```

## 📚 Next Steps

- [Read complete documentation](.ward/README.md)
- [Explore plugin development](.ward/README.md#-plugins)
- [Check API reference](.ward/README.md#-api-reference)
- [Join community discussions](https://github.com/yamonco/ward/discussions)
- [Report issues](https://github.com/yamonco/ward/issues)

---

**🚀 Ward Security System - Protecting your code, empowering your team**