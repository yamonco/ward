# Ward Security System

<p align="center">
  <img src="assets/ward.png" alt="Ward Security System" width="200"/>
</p>

[![CI/CD](https://github.com/yamonco/ward/workflows/CI%2FCD/badge.svg)](https://github.com/yamonco/ward/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Pulls](https://img.shields.io/docker/pulls/yamonco/ward.svg)](https://hub.docker.com/r/yamonco/ward)

**Ward** is a simple security service that enforces restrictions on specific folders. It controls file system access and provides a secure development environment.

## 🚀 Key Features

- **Directory Access Control**: Set security policies for specific folders
- **Command Whitelist/Blacklist**: Manage allowed/blocked commands
- **AI Collaboration**: Secure work with AI copilots
- **Real-time Audit Logging**: Record all operation activities
- **Docker Support**: Easy deployment in container environments
- **Python CLI**: Python-based command line interface

## 📦 Installation

### Using UV (Recommended)
```bash
uv tool install --from git+https://github.com/yamonco/ward.git ward

# Or run directly without installation
uvx --from git+https://github.com/yamonco/ward.git ward-cli status
```

### Using Docker
```bash
docker pull yamonco/ward:latest
docker run -it -v $(pwd):/workspace yamonco/ward:latest
```

### Direct Download
```bash
wget https://github.com/yamonco/ward/releases/latest/download/ward-bash.tar.gz
tar -xzf ward-bash.tar.gz
cd ward-bash
./setup-ward.sh
```

## 🏁 Quick Start

### Project Initialization
```bash
# Create new project
ward-init my-project
cd my-project

# Check basic policies
ward-cli status
```

### Create First Policy
```bash
# Create .ward file
echo "@description: My secure project
@whitelist: ls cat pwd echo grep sed awk git
@allow_comments: true
@max_comments: 5
@comment_prompt: \"Explain changes from a security perspective\"" > .ward

# Validate policy
ward-cli check .
```

## 🔧 Usage

### Basic Commands
```bash
# Check system status
ward-cli status

# Analyze directory policies
ward-cli check .

# Validate all policies
ward-cli validate

# Run secure shell
ward-shell
```

### AI Collaboration
```bash
# Add AI task handle
ward-cli handle add "Refactor authentication module" --comment "Improve security and add rate limiting"

# List handles
ward-cli handle list

# Add comments
ward-cli comment "This change improves performance by 20%" --context "backend optimization"
```

## 🐳 Docker Usage

### Basic Docker Commands
```bash
# Run Ward in current directory
docker run -it --rm -v $(pwd):/workspace yamonco/ward:latest

# Run with custom policy
docker run -it --rm -v $(pwd):/workspace \
  -e WARD_POLICY_WHITELIST="ls cat pwd echo git" \
  yamonco/ward:latest
```

### Docker Compose Example
```yaml
# docker-compose.yml
version: '3.8'
services:
  ward:
    image: yamonco/ward:latest
    volumes:
      - .:/workspace
    working_dir: /workspace
    environment:
      - WARD_LOG_LEVEL=INFO
      - WARD_POLICY_ALLOW_COMMENTS=true
    command: ward-shell
```

## 📋 Policy Examples

### Frontend Development
```bash
echo "@description: Frontend application
@whitelist: ls cat pwd echo grep sed awk npm yarn node git code vim nano
@blacklist: rm mv cp chmod chown sudo
@allow_comments: true
@max_comments: 10
@comment_prompt: \"Explain changes from a frontend architecture perspective\"" > .ward
```

### Backend Development
```bash
echo "@description: Backend API server
@whitelist: ls cat pwd echo grep sed awk python pip poetry docker git
@blacklist: rm -rf / rm mv cp sudo su
@allow_comments: true
@max_comments: 8
@comment_prompt: \"Explain changes from a backend security perspective\"" > .ward
```

### System Administration
```bash
echo "@description: System administration tasks
@whitelist: ls cat pwd echo grep sed awk systemctl journalctl docker kubectl git vim nano
@blacklist: rm -rf /* dd format fdisk
@allow_comments: true
@max_comments: 3
@comment_prompt: \"Explain changes from a system administration perspective\"" > .ward
```

## 🔒 Security Best Practices

### Production Environment Setup
```bash
# Enable authentication
ward-cli auth set-password

# Enable audit logging
ward-cli config set engine.audit_enabled true
ward-cli config set logging.file_enabled true

# Set strict mode
ward-cli config set engine.strict_mode true
```

### Environment Variables
```bash
export WARD_LOG_LEVEL=DEBUG
export WARD_STRICT_MODE=true
export WARD_PLUGIN_DIR=/custom/plugins
export WARD_AUTH_SESSION_TIMEOUT=7200
```

## 🛠️ Development

### Local Development Setup
```bash
git clone https://github.com/yamonco/ward.git
cd ward
uv sync
source .venv/bin/activate

# Install in development mode
pip install -e .
```

### Run Tests
```bash
pytest tests/
```

## 📚 Documentation

- [Complete documentation](.ward/README.md)
- [Plugin development guide](.ward/README.md#-plugins)
- [API reference](.ward/README.md#-api-reference)

## 🤝 Contributing

Contributions are welcome! Please see our [CONTRIBUTING.md](CONTRIBUTING.md).

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🆘 Support

- [GitHub Discussions](https://github.com/yamonco/ward/discussions)
- [Issue reporting](https://github.com/yamonco/ward/issues)
- [Security vulnerability reports](security@yamonco.com)

## 🏢 yamonco

Ward is developed and maintained as an open source project by [yamonco](https://github.com/yamonco).

## ❤️ Sponsors

If you find this project helpful, please consider supporting us through GitHub Sponsors:

[![Sponsor yamonco](https://img.shields.io/github/sponsors/yamonco?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sponsors/yamonco)

Your support helps us with:
- 🐛 Bug fixes and maintenance
- ✨ New feature development
- 📚 Documentation improvements
- 🔧 Infrastructure costs
- 🌍 Community support

---

**🚀 Ward Security System - Protecting your code, empowering your team**