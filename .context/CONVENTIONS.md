# Conventions

- Use `uv` for dependency management
- Use `pytest` for testing
- Use `ruff` for linting and formatting
- Keep CLI execution silent except for a minimal JSON result on stdout; route incidental output to `cli.log`
- Prefer workflow-specific top-level commands with shared date validation and normalized JSON output
