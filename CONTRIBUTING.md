# Contributing to AgentTrace

Thank you for your interest in contributing to AgentTrace! We welcome contributions from the community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/agenttrace.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest` (Python) or `npm test` (Node.js)
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Setup

```bash
# Install Python dependencies
cd packages/sdk-python
pip install -e ".[dev]"

# Install Node.js dependencies
cd apps/dashboard
npm install

# Setup pre-commit hooks
pre-commit install
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Format with `black`
- Lint with `ruff`

### TypeScript/JavaScript

- Follow Airbnb style guide
- Use ESLint and Prettier
- Use TypeScript for all new code

## Testing

### Python

```bash
cd packages/sdk-python
pytest tests/
```

### TypeScript

```bash
cd apps/dashboard
npm test
```

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new features
- Update documentation as needed
- Ensure all tests pass
- Follow the code style guidelines
- Write clear commit messages

## Commit Message Format

```
type(scope): subject

body

footer
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(sdk): add support for custom metadata

Add ability to attach custom metadata to traces for better
filtering and analysis.

Closes #123
```

## Reporting Bugs

Use GitHub Issues and include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python/Node version, etc.)

## Feature Requests

We welcome feature requests! Please:
- Check existing issues first
- Describe the feature and use case
- Explain why it would be valuable

## Code Review Process

1. Maintainers will review PRs
2. Address feedback and comments
3. Once approved, your PR will be merged

## Questions?

Feel free to open an issue for questions or join our community discussions.

Thank you for contributing!
