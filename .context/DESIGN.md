# Design

## Features
- Implemented: Track Preferential Allotments
- Implemented: Track QIPs
- Implemented: Track insider trading disclosures
- Implemented: NSE Data Integration with XBRL download and parsing
- Implemented: Four-level industry mapping (Macro, Sector, Industry, Basic Industry) integration
- Implemented: Current Market Price (CMP) fetching for stock symbols
- Implemented: Tenacity-based retry mechanism for resilient API requests
- Implemented: CLI execution with structured JSON output; internal stdout/stderr redirected to log file
- Implemented: Coherent top-level CLI workflows (`further-issues`, `insider-trading`)
- Not implemented: Rights Issues workflow
- Known limitation: Insider trading XBRL parsing can fail until NSE fixes the published taxonomy/schema resolution

## Note:
use "revisedFlag" to deduplicate filings while developing on top of this
