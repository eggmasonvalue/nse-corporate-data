# Design

## Features
- Implemented: Track Preferential Allotments
- Implemented: Track QIPs
- Implemented: Track insider trading disclosures
- Implemented: NSE Data Integration with XBRL download and parsing
- Implemented: Four-level industry mapping (Macro, Sector, Industry, Basic Industry) integration
- Implemented: Compact market-data snapshot fetching for stock symbols via `getDetailedScripData`
- Implemented: Per-symbol market-data caching to avoid repeated NSE requests inside a run
- Implemented: Insider-trading market-data fetch limited to `Market Purchase` and `Market Sale` rows
- Implemented: `currentPrice` priority of `closePrice`, then `lastPrice`, then `previousClose`
- Implemented: Tenacity-based retry mechanism for resilient API requests
- Implemented: CLI execution with structured JSON output; internal stdout/stderr redirected to log file
- Implemented: Grouped CLI workflows (`further-issues fetch|shorten`, `insider-trading fetch|shorten`)
- Implemented: Canonical machine-facing `--category` and `--mode` CLI tokens with internal mapping to NSE values
- Implemented: Declarative preferential short-output schema with `revisedFlag`, lock-in fields, pricing, size, current price, and four-level industry data
- Implemented: Declarative insider short-output schema with compact signal-focused metadata and four-level industry fields
- Not implemented: Rights Issues workflow
- Not implemented: QIP short-output helper
- Implemented: Replaced the single `CMP` field in canonical outputs with a richer `marketData` snapshot derived from `getDetailedScripData`
- Known limitation: Insider trading XBRL parsing can fail until NSE fixes the published taxonomy/schema resolution; the workflow now defaults to skipping insider XBRL unless explicitly enabled

## Note:
use "revisedFlag" to deduplicate filings while developing on top of this
