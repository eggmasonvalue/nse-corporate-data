# Conventions

- Use `uv` for dependency management
- Use `pytest` for testing
- Use `ruff` for linting and formatting
- Keep CLI execution silent except for a minimal JSON result on stdout; route incidental output to `cli.log`
- Prefer grouped workflow commands such as `further-issues fetch` and `insider-trading fetch|shorten`
- Prefer configuration-backed behavior switches over hardcoded workflow special cases
- For shortened artifacts, keep the selected metadata fields in a single declarative registry so the output schema can be changed without editing CLI flow code
- Preserve source lineage flags such as `revisedFlag` in shortened artifacts when they materially affect deduplication or downstream interpretation
