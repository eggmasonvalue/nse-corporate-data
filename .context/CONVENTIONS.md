# Conventions

- Use `uv` for dependency management
- Use `pytest` for testing
- Use `ruff` for linting and formatting
- Keep CLI execution silent except for a minimal JSON result on stdout; route incidental output to `cli.log`
- Prefer grouped workflow commands such as `further-issues fetch|refine` and `insider-trading fetch|refine`
- Prefer configuration-backed behavior switches over hardcoded workflow special cases
- For refined artifacts, keep the selected metadata fields in a single declarative registry so the output schema can be changed without editing CLI flow code
- Prefer canonical consumer-facing API labels in published JSON metadata instead of raw NSE field names
- Do not duplicate fields such as `symbol` outside the metadata-governed row arrays; if a value exists in `metadata.api` or `metadata.record`, it should not also appear as a standalone sibling key in each row
- Keep refined artifacts structurally aligned with the raw artifacts by preserving separate `record`, `industry`, and `marketData` blocks
- When enriching data, if an enrichment (like `market-data` or `industry`) is not explicitly requested, its corresponding key MUST be completely omitted from the JSON output to conserve tokens.
- When one command can refine multiple artifact families, switch registries through a small CLI selector and keep category-specific default input/output paths together with the registry owner
- Preserve source lineage flags such as `revisedFlag` in refined artifacts when they materially affect deduplication or downstream interpretation
