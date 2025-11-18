# Contributing to Ward Security System

Thank you for your interest in contributing to Ward! This guide explains how to contribute to the project.

## 🤝 How to Contribute

### Reporting Issues

Please use [GitHub Issues](https://github.com/yamonco/ward/issues) to report bugs or request features.

#### Bug Reports
- **Title**: Clear and concise bug description
- **Environment**: Operating system, Python version, Ward version
- **Steps to Reproduce**: Exact steps to reproduce the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots**: Include if applicable
- **Logs**: Include relevant log files

#### Feature Requests
- **Title**: Concise description of the requested feature
- **Problem**: Description of the problem to solve
- **Proposed Solution**: Description of the desired solution
- **Alternatives**: Other solutions considered
- **Additional Context**: Other relevant information

### Code Contributions

#### Development Environment Setup

1. Fork and clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ward.git
cd ward
```

2. Set up development environment
```bash
# Use UV (recommended)
uv sync
source .venv/bin/activate

# Or use pip
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

3. Set up pre-commit hooks
```bash
pre-commit install
```

#### Branch Strategy

- `main`: Stable release branch
- `develop`: Development branch
- `feature/*`: New feature development branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Emergency fix branches

#### Code Style

The project uses the following tools to maintain code style:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

```bash
# Check code style
black src tests
isort src tests
flake8 src tests
mypy src
```

#### Testing

All code changes should include tests:

```bash
# Run tests
pytest tests/

# Check coverage
pytest tests/ --cov=src --cov-report=html

# Run specific tests
pytest tests/test_cli.py
```

#### Pull Request Process

1. **Create a branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Write code and tests**
```bash
# Write code
# Write tests
# Ensure all tests pass
pytest tests/
```

3. **Commit**
```bash
git add .
git commit -m "feat: add new feature description"
```

4. **Push and create PR**
```bash
git push origin feature/your-feature-name
```

5. **Fill in the PR template**
   - Summary of changes
   - How to test
   - Related issues
   - Screenshots (if applicable)

#### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (no logic changes)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Build process, auxiliary tool changes

**Examples:**
```
feat(cli): add verbose logging option

Added --verbose flag to enable detailed logging output
for debugging and troubleshooting.

Closes #123
```

## 🔧 Development Guide

### Project Structure

```
ward/
├── src/ward_security/          # Python source code
│   ├── __init__.py
│   ├── cli.py                  # CLI interface
│   ├── shell.py                # Secure shell
│   ├── installer.py            # Installation manager
│   └── deployer.py             # Deployment manager
├── .ward/                      # Bash scripts and configuration
│   ├── core/                   # Core functionality
│   ├── ward-cli.sh            # CLI script
│   └── ward.sh                # Main script
├── tests/                      # Test code
├── docs/                       # Documentation
└── .github/                    # GitHub configuration
```

### Coding Standards

1. **Type Hints**: Use type hints for all functions
```python
def process_command(command: str, args: List[str]) -> int:
    """Process a command with arguments."""
    pass
```

2. **Docstrings**: Include docstrings for all modules, classes, and functions
```python
class WardCLI:
    """Ward Security Command Line Interface.

    Provides a Python wrapper around the Ward CLI bash script
    for better integration with Python-based workflows.
    """
```

3. **Error Handling**: Use specific exception handling
```python
try:
    result = subprocess.run(command, check=True)
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {e}")
    raise WardError(f"Command execution failed: {e}") from e
```

4. **Logging**: Use structured logging
```python
import logging

logger = logging.getLogger(__name__)

def execute_command(command: str) -> int:
    logger.info(f"Executing command: {command}")
    try:
        result = run_command(command)
        logger.debug(f"Command result: {result}")
        return result
    except Exception as e:
        logger.error(f"Command failed: {e}")
        raise
```

### Testing Guidelines

#### Unit Tests
```python
import pytest
from ward_security.cli import WardCLI

class TestWardCLI:
    def test_init_success(self):
        cli = WardCLI()
        assert cli.ward_root is not None

    def test_run_command_invalid_cli(self, tmp_path):
        cli = WardCLI()
        cli.ward_cli_path = tmp_path / "nonexistent.sh"
        result = cli.run_ward_command(["status"])
        assert result == 1
```

#### Integration Tests
```python
def test_full_workflow(tmp_path):
    # Create test .ward file
    ward_file = tmp_path / ".ward"
    ward_file.write_text("@description: Test project\n@whitelist: ls cat pwd\n")

    # Run CLI
    result = run_cli(["check", str(tmp_path)])
    assert result.returncode == 0
```

## 📝 Documentation Contributions

### Documentation Types

- **API Documentation**: Included in code docstrings
- **User Guides**: `docs/` directory
- **Developer Guides**: `CONTRIBUTING.md`
- **Release Notes**: GitHub Releases

### Documentation Writing Guidelines

1. **Use Markdown format**
2. **Include code examples**
3. **Attach screenshots** (when applicable)
4. **Verify all links** (ensure all links are valid)

## 🚀 Release Process

### Version Management

Follow [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: Incompatible API changes
- `MINOR`: New functionality (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Code review complete
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number updated
- [ ] Tag created
- [ ] GitHub Release created
- [ ] Docker image built and pushed
- [ ] Deployed to PyPI

## 🏅 Contributor Recognition

All contributors are recognized in the following ways:

- **README.md**: Contributor list
- **Release Notes**: People who contributed to specific releases
- **GitHub Contributors**: Automatically tracked

## 📞 Getting Help

If you need help with contributing:

- **GitHub Discussions**: Questions and discussions
- **Issues**: Bug reports and feature requests
- **Email**: dev@yamonco.com

## 📄 License

All contributed code is distributed under the project's [MIT License](LICENSE). By contributing, you agree to license your contributions under the same terms.

---

Thank you again for contributing! 🙏