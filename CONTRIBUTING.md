# Contributing

Thank you for your interest in contributing to Digital Surveyor!

## Getting Started

1. Fork the repository and clone your fork.
2. Copy `.env.example` to `.env` and add any required API keys.
3. Start the stack with `docker compose watch`.
4. Make your changes on a feature branch.

## Development

For detailed instructions on setting up your development environment, running the stack, linting, and testing, see the [README](README.md).

### Pre-commit Hooks

This project uses pre-commit hooks for code quality:

```bash
cd backend
uv run pre-commit install -f
uv run pre-commit run --all-files
```

Hooks run Ruff (Python linting/formatting), Biome (frontend linting), and mypy (type checking) automatically on every commit.

## Pull Requests

When submitting a pull request:

1. Make sure all tests pass before submitting.
2. Keep PRs focused on a single change.
3. Update or add tests if you're changing functionality.
4. Reference any related issues in your PR description.

## Reporting Issues

If you find a bug or have a feature request, please open a GitHub Issue with:

- A clear description of the problem or suggestion.
- Steps to reproduce (for bugs).
- Expected vs. actual behaviour.
- Any relevant logs or screenshots.

## Questions?

Feel free to open a GitHub Issue for questions about contributing.
