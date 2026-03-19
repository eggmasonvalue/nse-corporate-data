# Design

## Features
- Implemented: Track Preferential Allotments
- Implemented: Track QIPs
- Implemented: Track insider trading disclosures
- Implemented: NSE Data Integration with XBRL download and parsing
- Implemented: Four-level industry mapping (Macro, Sector, Industry, Basic Industry) integration
- Implemented: Compact market-data snapshot fetching for stock symbols via `getDetailedScripData`
- Implemented: Per-symbol market-data caching to avoid repeated NSE requests inside a run
- Implemented: Ordered fallback across valid NSE series values when `getDetailedScripData` returns an empty shell response for the default series
- Implemented: Insider-trading market-data fetch limited to `Market Purchase` and `Market Sale` rows
- Implemented: Insider-trading `--mode` coverage expanded to the broader NSE acquisition-mode enum, including allotment, trust-beneficiary, block-deal, buy-back, ESOS, inheritance, pledge-release, and revocation-of-pledge flows
- Implemented: `currentPrice` priority of `closePrice`, then `lastPrice`, then `previousClose`
- Implemented: Tenacity-based retry mechanism for resilient API requests
- Implemented: CLI execution with structured JSON output; internal stdout/stderr redirected to log file
- Implemented: Grouped CLI workflows (`further-issues fetch|shorten`, `insider-trading fetch|shorten`)
- Implemented: Canonical machine-facing `--category` and `--mode` CLI tokens with internal mapping to NSE values
- Implemented: Declarative preferential short-output schema with `revisedFlag`, lock-in fields, pricing, size, current price, and four-level industry data
- Implemented: Declarative QIP short-output schema with issue economics, investor participation details, revision lineage, market data, and four-level industry data
- Implemented: Declarative insider short-output schema with compact signal-focused metadata and four-level industry fields
- Implemented: Canonical consumer-facing API labels for PREF, QIP, and insider full artifacts
- Implemented: Shortened artifacts now preserve the raw-artifact block structure with separate `record`, `industry`, and `marketData` arrays
- Implemented: `further-issues shorten --category qip` for debloated QIP output
- Implemented: Confirmed root full-artifact samples are columnar and use a single `issueType` per dataset: `qip_data.json` is all `QIP` and `pref_data.json` is all `Preferential`
- Implemented: Removed redundant top-level `symbol` keys from full and shortened row objects; `symbol` now exists only inside metadata-aligned row arrays
- Not implemented: Rights Issues workflow
- Implemented: Replaced the single `CMP` field in canonical outputs with a richer `marketData` snapshot derived from `getDetailedScripData`
- Known limitation: Insider trading XBRL parsing can fail until NSE fixes the published taxonomy/schema resolution; the workflow now defaults to skipping insider XBRL unless explicitly enabled

## Note:
- use "revisedFlag" to deduplicate filings while developing on top of this
- For insider trading, for market purchases and sales, warrants will not be a problem. however, for categories like "Preferential Offer" or "Conversion of security", it might be. The shortening math will not hold.
Warrants are not an issue for pref and qip since we're looking only at "Listing stage"
- For insider trading,
  - we may have to refactor the user-facing input to accept `transaction type` separately because it is a broader enum: `Buy`, `Sell`, `Pledge`, `Pledge Invoke`, `Pledge Revoke`.
  - `type of instrument` may need to become a filter dimension as well. Current NSE values observed for this enum are: `Equity`, `Warrant`, `Debenture`, `Convertible Debenture`, `Bond`, `Derivative`, `Government Security`, `Preference Shares`, `Convertible Preference Shares`, `Any other instrument`.
  - In acqMode, for "pledge-revoke", "Revocation of Pledge" is what's described the NSE taxonomy however some filers somehow mess the enum dropdown(inexplicably) leading to "Revokation of Pledge" being found as well
