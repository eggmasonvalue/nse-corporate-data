# Changelog
## [Unreleased]
- Added a `forced-sales` preset to the `insider-trading refine` command to explicitly capture and deduplicate externally driven supply dumps (e.g. invocation of pledge) which are highly inconsistent in raw NSE filings.
- Improved the insider trading percentage change calculation to use precise raw shares differences, resolving previous precision loss caused by NSE's rounded percentages.
- Expanded insider-trading `--mode` coverage to the broader NSE acquisition-mode enum, adding support for `Allotment`, `Beneficiary from Trusts`, `Block Deal`, `Buy Back`, `ESOS`, `Inheritance`, `Pledge Release`, and correctly spelled `Revocation of Pledge`.
- Documented follow-up insider-trading input risks in `.context/DESIGN.md`: `transaction type` may need a dedicated user-facing filter, and `type of instrument` may need to be exposed as a filter dimension.
- Removed redundant top-level `symbol` keys from full and shortened artifact rows; `symbol` now appears only in the metadata-aligned `api` or `record` arrays, while the shortener still accepts legacy full artifacts that carried `data[].symbol`.
- Documented the current root sample-data invariant that `qip_data.json` contains only `QIP` `issueType` values and `pref_data.json` contains only `Preferential`, with both files using the metadata-driven columnar `api` layout.
- Replaced raw NSE `metadata.api` labels in full PREF, QIP, and insider artifacts with canonical consumer-facing names.
- Refactored all shortened artifacts to preserve the raw-artifact structure with separate `record`, `industry`, and `marketData` blocks, and exposed the full `marketData` block in each shortener.
- Added `further-issues shorten --category qip`, producing a debloated `qip_short.json` that keeps issue economics, allottee detail, revision lineage, market data, and four-level industry context.
- Extended `further-issues shorten` with category-specific default input/output paths for `pref` and `qip`.
- Added ordered NSE series fallback (`EQ`, `BE`, `BZ`, `SM`, `ST`, `SZ`) for `getDetailedScripData()` when the default series returns an empty `equityResponse` shell.
- Replaced the canonical `CMP` field with a richer `marketData` block containing `currentPrice`, `sharesOutstanding`, `freeFloatMarketCap`, `priceToEarnings`, `fiftyTwoWeekHigh`, and `fiftyTwoWeekLow`.
- Switched canonical market enrichment from `nse.quote()` to `nse.getDetailedScripData()`.
- Renamed shortened-artifact price context from `CMP` to `currentPrice`.
- Refreshed `samples/pref_data.json`, `samples/qip_data.json`, `samples/insider_trading_data.json`, `samples/pref_short.json`, and `samples/insider_trading_short.json` from March 2026 / 18-Mar-2026 fetch windows.
- Added `further-issues shorten`, a pure local preferential-issue shortener that reads `pref_data.json` and writes `pref_short.json`.
- Added a declarative preferential short-output field registry in `further_issues.py`.
- Added a shared metadata-driven short-output helper in `shorten.py`.
- Preserved `revisedFlag` in the preferential short artifact so consumers can detect revised or duplicate filing lineage.
- Refactored the CLI into grouped workflows: `further-issues fetch|shorten` and `insider-trading fetch|shorten`.
- Added a pure local insider-trading shortening workflow that emits `insider_trading_short.json`.
- Added a declarative insider short-output field registry in `insider.py` so metadata can be changed in one place.
- Changed `currentPrice` extraction to use NSE priority `closePrice`, then `lastPrice`, then `previousClose`, while treating zero-valued fields as missing so fallbacks can apply.
- Limited insider-trading market-data lookups to `Market Purchase` and `Market Sale` rows to avoid unnecessary NSE calls.
- Added `Settings`-based configuration for insider trading, including `NSE_CORPORATE_DATA_ENABLE_INSIDER_TRADING_XBRL`.
- Disabled insider-trading XBRL processing by default while keeping it configurable.
- Added a fetcher-level per-symbol market-data cache to avoid repeated NSE requests within a run.
- Replaced raw CLI values with canonical machine-facing tokens: repeatable `--category pref|qip` for further issues and repeatable `--mode` tokens for insider trading.
- Renamed insider mode tokens `buy` and `sell` to `market-buy` and `market-sell` to avoid ambiguity with broader NSE buy/sell semantics.
- Renamed the project/package surface to `nse-corporate-data` / `nse_corporate_data`.
- Replaced the old single `fetch` command with nested workflow groups.
- Added a default `--to-date` of the local run date for both CLI workflows.
- Defaulted further-issues to both `pref` and `qip` when `--category` is omitted.
- Added insider trading ingestion using the NSE `corporates-pit` endpoint, XBRL download, industry enrichment, and market-data enrichment.
- Added tests covering CLI defaults, date-range validation, and generic parser behavior.
- Documented the temporary insider-trading XBRL parsing limitation caused by upstream NSE taxonomy issues.

## [0.3.0] - 2026-03-18
- Added `tenacity` dependency and implemented a retry mechanism for NSE API failures (`TimeoutError`, `ConnectionError`, and status codes 408, 429, 502, 503, 504).
- Added `CMP` to the metadata dictionary so that the Current Market Price entry is commensurate with best practices.
- Added four-level industry mapping (Macro, Sector, Industry, Basic Industry) for all stocks in the output, fetched from `eggmasonvalue/stock-industry-map-in`.
- Added Current Market Price (CMP) fetching for stock symbols in corporate filings using the `nse` dependency's `quote` method.
...
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
