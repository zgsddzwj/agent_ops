# Contributing to AgentOps

Thank you for your interest in contributing to AgentOps! This document provides guidelines and instructions for contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

By participating in this project, you agree to maintain a welcoming and inclusive environment for everyone. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/agent_ops.git
   cd agent_ops
   ```
3. **Set up upstream remote**:
   ```bash
   git remote add upstream https://github.com/zgsddzwj/agent_ops.git
   ```
4. **Keep your fork updated**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose

### Python Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e packages/agent-ops-sdk \
            -e packages/agent-ops-cli \
            -e backend \
            -e worker

# Install dev tools
pip install pytest pytest-asyncio ruff
```

### Node.js Environment

```bash
cd web
npm install
cd ..
```

### Database Setup

```bash
# Using Docker Compose (recommended)
cd infra
docker compose up -d postgres redis
cd ..

# Or setup manually
createdb agentops_dev
redis-server
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **Bug reports** - Report issues you encounter
2. **Feature requests** - Suggest new functionality
3. **Code contributions** - Implement features or fix bugs
4. **Documentation improvements** - Enhance docs and examples
5. **Test improvements** - Add tests and improve coverage
6. **Performance optimizations** - Make things faster and more efficient

### Finding Issues to Work On

1. Check the [Issues](https://github.com/zgsddzwj/agent_ops/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Ask in discussions if you're unsure where to start

## Pull Request Guidelines

### Before You Start

1. **Discuss major changes** - Open an issue to discuss significant changes
2. **Create a feature branch** - Don't work directly on `main`
3. **Check existing issues** - Make sure no one else is working on the same thing

### Creating a Pull Request

1. **Create a new branch**:
   ```bash
   git checkout -b feature/my-awesome-feature
   ```

2. **Make your changes** following our coding standards
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run tests** and ensure they pass
6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add awesome feature
   
   This adds the awesome feature that does X, Y, and Z.
   
   Closes #123"
   ```

### Pull Request Template

When creating a PR, please include:

- **Description** of what you've implemented
- **Motivation** and context
- **Testing done** and test results
- **Breaking changes** (if any)
- **Screenshots** (for UI changes)
- **Related issues**

### Review Process

1. **Automated checks** will run on your PR
2. **Maintainers will review** your code
3. **Address feedback** promptly
4. **Update your PR** as requested

## Code Style and Standards

### Python Code Style

We follow [PEP 8](https://pep8.org/) with these additional guidelines:

- Use **Ruff** for linting and formatting
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for public APIs
- Follow consistent naming conventions

```python
# Good example
def calculate_metrics(
    data: list[dict],
    threshold: float | None = None
) -> dict[str, float]:
    """Calculate performance metrics from trace data.
    
    Args:
        data: List of trace dictionaries
        threshold: Optional filtering threshold
        
    Returns:
        Dictionary of calculated metrics
    """
    # Implementation here
    pass
```

### Running Linters

```bash
# Check linting
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .
```

### TypeScript/JavaScript Code Style

- Use **ESLint** and **Prettier**
- Follow the existing code style in the project
- Use TypeScript types for all functions

### SQL Style

- Use lowercase for SQL keywords
- Indent subqueries properly
- Use descriptive table and column names

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_sdk.py

# Run tests with verbose output
pytest -v

# Run async tests
pytest tests -v -k "async"
```

### Writing Tests

- Write tests for **all new features**
- Aim for **high test coverage** (>80%)
- Include **unit tests** and **integration tests**
- Use **meaningful test names**
- Test **edge cases** and **error conditions**

```python
def test_evaluation_with_invalid_input():
    """Test that evaluation handles invalid input gracefully."""
    # Test implementation
    pass

@pytest.mark.asyncio
async def test_async_metric_calculation():
    """Test async metric calculation performance."""
    # Test implementation
    pass
```

## Documentation

### Documentation Standards

- Keep documentation **up-to-date**
- Use **clear and concise** language
- Include **examples** and **code snippets**
- Maintain **consistent formatting**

### Types of Documentation

1. **README files** - High-level project overview
2. **API documentation** - Function and class documentation
3. **User guides** - Step-by-step instructions
4. **Architecture docs** - System design and components
5. **Code comments** - Explain complex logic

### Writing Good Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

**Examples**:
```
feat(sdk): add LangChain callback handler
fix(api): resolve authentication error with invalid API keys
docs: update quickstart guide with new CLI commands
```

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Steps

1. **Update version** in relevant files
2. **Update changelog** with release notes
3. **Run all tests** to ensure stability
4. **Create release branch**
5. **Merge to main** and tag release
6. **Update documentation**
7. **Announce release**

## Questions?

If you have questions about contributing:

1. Check existing [Discussions](https://github.com/zgsddzwj/agent_ops/discussions)
2. Create a new discussion
3. Reach out to the maintainers

---

Thank you for contributing to AgentOps! 🚀