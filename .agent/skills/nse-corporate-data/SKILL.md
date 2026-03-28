---
name: nse-corporate-data
description: Fetch, process, and analyze National Stock Exchange (NSE) corporate disclosures, specifically further issues (preferential allotments, QIPs) and insider trading data. Make sure to use this skill whenever the user asks to research Indian stocks, analyze insider trading, check for preferential issues or QIPs, or work with NSE corporate filings.
---

# NSE Corporate Data Skill

This skill enables you to autonomously fetch, process, and analyze corporate disclosures from the National Stock Exchange (NSE) of India using the local `nse-corporate-data` CLI tool.

## Workflow for Fulfilling Requests

When a user asks you to fetch or analyze NSE corporate data (e.g., "Check insider trading for last week", "Get recent QIPs"), follow this structured workflow:

### 1. Prepare Parameters
Determine the target date range. Dates MUST be formatted as `DD-MM-YYYY`. If the user provides informal dates (e.g., "last month", "since Monday"), calculate the exact dates yourself. If no end date is implied by the user, you can omit the `--to-date` argument (it defaults to today).

### 2. Fetch the Data
Execute the appropriate fetch command using `uv`.
*Note: The CLI is designed to be agent-friendly. It runs silently and only outputs a JSON summary (e.g., `{"files": [...]}`) to stdout. All detailed execution logs are diverted to `cli.log`.*

**For Further Issues (Preferential Allotments & QIPs):**
```bash
uv run nse-corporate-data further-issues fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--category pref] [--category qip] [--enrich market-data] [--enrich industry] [--enrich xbrl]
```
- Omit `--category` to fetch both `pref` and `qip`.
- Raw outputs: `pref_raw.json`, `qip_raw.json`.
- `--enrich` flags are optional. Omit any enrichment you don't need — unrequested enrichments are completely absent from the output to conserve tokens.

**For Insider Trading:**
```bash
uv run nse-corporate-data insider-trading fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--enrich market-data] [--enrich industry] [--enrich xbrl]
```
- Insider trading fetch is unconditional — all raw disclosure data is fetched regardless of transaction type.
- Raw output: `insider_raw.json`.
- `--enrich xbrl` is disabled by default due to NSE taxonomy inconsistencies; omit it unless specifically requested.

*Troubleshooting: If the fetch command outputs an `{"error": "..."}`, read `cli.log` to diagnose the issue.*

### 3. Refine the Data for Analysis
The raw fetched artifacts are deeply nested and large. **Always** run the refine command to produce compact, LLM-friendly artifacts before reading or analyzing the data.

**For Further Issues:**
```bash
uv run nse-corporate-data further-issues refine --category pref
uv run nse-corporate-data further-issues refine --category qip
```
- Produces `pref.json` and `qip.json` respectively.
- Defaults to `--category pref` if omitted.
- Preserves `revisedFlag` so you can detect and deduplicate revised or duplicate filings.

**For Insider Trading:**
```bash
uv run nse-corporate-data insider-trading refine [--preset PRESET]
```
- Produces `insider.json`.
- `--preset` defaults to `market`. Available presets:
  - `market` — all open-market buys and sells (recommended default)
  - `market-buy` — open-market purchases only
  - `market-sell` — open-market sales only
  - `buy` — all acquisition modes
  - `sell` — all disposal modes
  - `forced-sales` — externally driven supply dumps (pledge invocations), with built-in deduplication on `(symbol, personName, transactionQuantity, transactionStartDate)`

### 4. Analyze and Present
Read the resulting refined JSON (`pref.json`, `qip.json`, or `insider.json`). These files are optimized for your context window and contain metadata-aligned arrays with separate `record`, `industry`, and `marketData` blocks.

Synthesize the information intelligently based on the user's original request. Highlight key signals such as large transaction values, significant percentage changes in holdings, or notable market data context. Do not simply dump the raw JSON back to the user.

### Key Caveats
- NSE filings are inconsistent: insider trading data in particular has irregular enums, misspelled field values (e.g. "Revokation" vs "Revocation"), and mixed transaction/acquisition-mode combinations. The presets handle known edge cases.
- Use `revisedFlag` to identify and deduplicate revised filings in further-issue artifacts.
- For insider trading analysis, focus on equity share transactions. Warrants and convertible instruments appear inconsistently and should generally be excluded unless specifically requested.