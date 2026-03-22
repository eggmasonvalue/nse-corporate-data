# Design

## Features
- Implemented: Track Preferential Allotments
- Implemented: Track QIPs
- Implemented: Track insider trading disclosures
- Implemented: Improved insider trading percentage change calculation using raw shares differences for exact precision
- Implemented: NSE Data Integration with XBRL download and parsing
- Implemented: Four-level industry mapping (Macro, Sector, Industry, Basic Industry) integration
- Implemented: Compact market-data snapshot fetching for stock symbols via `getDetailedScripData`
- Implemented: Per-symbol market-data caching to avoid repeated NSE requests inside a run
- Implemented: Ordered fallback across valid NSE series values when `getDetailedScripData` returns an empty shell response for the default series
- Implemented: `currentPrice` priority of `closePrice`, then `lastPrice`, then `previousClose`
- Implemented: Tenacity-based retry mechanism for resilient API requests
- Implemented: CLI execution with structured JSON output; internal stdout/stderr redirected to log file
- Implemented: Grouped CLI workflows (`further-issues fetch|refine`, `insider-trading fetch|refine`)
- Implemented: Unfiltered raw data fetching with opt-in API enrichments via `--enrich` flag (`market-data`, `industry`, `xbrl`). Unrequested enrichments are cleanly omitted to save tokens.
- Implemented: Presets (`market`, `buy`, `sell`) for `insider-trading refine` to filter for high-signal stake changes.
- Implemented: Declarative preferential refined-output schema with `revisedFlag`, lock-in fields, pricing, size, current price, and four-level industry data
- Implemented: Declarative QIP refined-output schema with issue economics, investor participation details, revision lineage, market data, and four-level industry data
- Implemented: Declarative insider refined-output schema with compact signal-focused metadata and four-level industry fields
- Implemented: Canonical consumer-facing API labels for PREF, QIP, and insider full artifacts
- Implemented: Refined artifacts now preserve the raw-artifact block structure with separate `record`, `industry`, and `marketData` arrays
- Implemented: `further-issues refine --category qip` for debloated QIP output
- Implemented: Confirmed root full-artifact samples are columnar and use a single `issueType` per dataset: `qip_data.json` is all `QIP` and `pref_data.json` is all `Preferential`
- Implemented: Removed redundant top-level `symbol` keys from full and refined row objects; `symbol` now exists only inside metadata-aligned row arrays
- Not implemented: Rights Issues workflow
- Implemented: Replaced the single `CMP` field in canonical outputs with a richer `marketData` snapshot derived from `getDetailedScripData`
- Known limitation: Insider trading XBRL parsing can fail until NSE fixes the published taxonomy/schema resolution; the workflow now defaults to skipping insider XBRL unless explicitly enabled

## Note:
- use "revisedFlag" to deduplicate filings while developing on top of this
- For further-issues, warrants will not be a problem since we look for Listing Stage and we don't have publicly traded warrants.
Warrants are not an issue for pref and qip since we're looking only at "Listing stage"
- For insider trading,
  - In acqMode, for "pledge-revoke", "Revocation of Pledge" is what's described the NSE taxonomy however some filers somehow mess the enum dropdown(inexplicably) leading to "Revokation of Pledge" being found as well
  - NSE is a hot mess wrt enforcing standards in XBRL filings. We don't know if the NSE's internal parser that outputs the values in the .json we are hitting with the endpoint is at fault or if the actual XBRL filings are but it's a mess.
  - "Invocation of pledge" is currently omitted from the sell preset due to inconsistent filings, and will be added later when data quality improves.
  - some notes regarding what is and is not present in the insider trading webpage currently but may be added to it in the future which will determine how we handle things:
    - type of security (pre) and type of security(post) are the same i.e. when a warrant or any convertible is converted into equity shares, it results in two transactions- a warrant sell and an equity buy - quantity determined based on conversion ratios etc. Practically, there are edge cases where blanks and hyphens are interchanged.
    - warrant buy modes are preferential offers, off market or hyphen(which means blanks are also likely)
    - "securityType" and "postTransactionSecurityType" are the same
    - at any point, NSE can enforce warrant buys properly. It seems inconsistent currently. sometimes, the filers seem to file for acquisition of warrants and sometimes they don't. maybe it was a newer rule enforced. so, it's better to ignore acquisition of warrants or converts or other types of securities for analysis. **this is solely to analyze when underlying equity shares are acquired by various means**
