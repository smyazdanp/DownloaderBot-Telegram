# Contributing to Telegram Downloader Bot

First off, thank you for considering contributing to this project! 👍

The following is a set of guidelines for contributing to the Telegram Downloader Bot. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How Can I Contribute?](#how-can-i-contribute)
4. [Development Setup](#development-setup)
5. [Style Guidelines](#style-guidelines)
6. [Commit Messages](#commit-messages)
7. [Pull Requests](#pull-requests)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [your.email@example.com].

## Getting Started

- Make sure you have a [GitHub account](https://github.com/signup/free)
- Fork the repository on GitHub
- Clone your fork locally
- Set up the development environment

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include logs and error messages**
- **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Write or update tests** if applicable
5. **Ensure all tests pass**
6. **Commit your changes** (see commit message guidelines)
7. **Push to your fork** (`git push origin feature/amazing-feature`)
8. **Create a Pull Request**

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, virtualenv, etc.)

### Setup Steps

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/telegram-downloader-bot.git
   cd telegram-downloader-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Create .env file**
   ```bash
   cp .env.example .env
   # Edit .env with your test bot token
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=telegram_bot

# Run specific test file
pytest tests/test_download.py

# Run with verbose output
pytest -v
```

## Style Guidelines

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- Line length: 100 characters
- Use double quotes for strings
- Use type hints where appropriate
- Document all functions and classes

### Code Formatting

We use `black` for code formatting:

```bash
# Format all files
black .

# Check formatting without changing files
black --check .
```

### Linting

We use `flake8` and `pylint` for linting:

```bash
# Run flake8
flake8 .

# Run pylint
pylint telegram_bot.py
```

### Type Checking

We use `mypy` for type checking:

```bash
mypy telegram_bot.py
```

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Examples

```
feat(download): add resume support for interrupted downloads

- Implement partial content download using Range headers
- Store download progress in temporary files
- Add automatic retry logic with exponential backoff

Closes #123
```

```
fix(admin): correct VIP status toggle in admin panel

The VIP status was not being properly saved to the database
due to incorrect boolean conversion.
```

## Pull Requests

### Before Submitting

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update the README** if necessary
5. **Run code formatting and linting**

### Pull Request Process

1. **Fill in the pull request template**
2. **Link related issues**
3. **Request review from maintainers**
4. **Address review comments**
5. **Ensure CI checks pass**

### Pull Request Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] I have tested this code locally
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published

## Related Issues
Closes #(issue number)

## Screenshots (if applicable)
Add screenshots to help explain your changes.
```

## Questions?

Feel free to ask questions in:
- [GitHub Discussions](https://github.com/yourusername/telegram-downloader-bot/discussions)
- [Telegram Support Group](https://t.me/yourbotsupport)
- [Issues](https://github.com/yourusername/telegram-downloader-bot/issues)

Thank you for contributing! 🎉