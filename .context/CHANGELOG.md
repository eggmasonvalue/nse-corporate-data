# Changelog

## [Unreleased]
- Added Current Market Price (CMP) fetching for stock symbols in corporate filings using the `nse` dependency's `quote` method.
- Improved CLI `fetch` command to return a minimal JSON object with essential results (`files` or `error`).
- Implemented stdout/stderr redirection to the log file during CLI execution to ensure clean JSON output while capturing external messages.
- Switched the `nse-xbrl-parser` dependency source from a local path checkout to the GitHub HTTPS repository URL.
- Replaced the placeholder README with usage, output, and structure documentation aligned to the current CLI behavior.

## [0.2.0] - 2026-03-12
- Modified CLI to overwrite `cli.log` on each run instead of appending.
- Integrated `nse` server dependency for bot-protected API requests.
- Added `nse-xbrl-parser` for processing corporate filing XBRL documents.
- Implemented Click CLI with `fetch` command to query PREF, QIP, or BOTH listing metadata between given dates.
- Output formats standardized as JSON logs with robust parameter validation to prevent hallucinated inputs.
- Initial project scaffold
