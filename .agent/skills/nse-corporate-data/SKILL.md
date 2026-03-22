---
name: nse-corporate-data
description: Fetch, process, and analyze National Stock Exchange (NSE) corporate disclosures, specifically further issues (preferential allotments, QIPs) and insider trading data. This skill is ESSENTIAL for any research on Indian stocks, analyzing insider trading activity, tracking institutional fundraising (QIPs), or investigating preferential allotments. Use this skill PROACTIVELY when the user mentions Indian equity markets, specific NSE-listed symbols, or corporate governance signals.
---

# NSE Corporate Data Skill

This skill enables you to autonomously fetch, process, and analyze corporate disclosures from the National Stock Exchange (NSE) of India using the `nse-corporate-data` CLI tool.

## Core Capabilities
1.  **Insider Trading**: Track purchases, sales, and pledge invocations by promoters and directors.
2.  **Further Issues**: Monitor Qualified Institutional Placements (QIPs) and Preferential Allotments.
3.  **Enrichment**: Automatically pull market caps, industries, and detailed XBRL-parsed data.

## Workflow for Fulfilling Requests

### 1. Identify Parameters
*   **Date Range**: Format dates as `DD-MM-YYYY`. 
    *   Calculate exact dates for informal requests (e.g., "last 30 days").
    *   `--from-date` is REQUIRED.
    *   `--to-date` defaults to today if omitted.
*   **Enrichment**: Decide if you need extra context. Use `--enrich` to add `market-data` (market cap/price), `industry`, or `xbrl` (detailed fields from filing).

### 2. Fetch the Data
Run the fetch command via `uv`. The tool runs silently, outputting a JSON summary to stdout and detailed logs to `cli.log`.

**Insider Trading:**
```bash
uv run nse-corporate-data insider-trading fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--enrich market-data] [--enrich industry] [--enrich xbrl]
```

**Further Issues (Preferential & QIP):**
```bash
uv run nse-corporate-data further-issues fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--category pref] [--category qip] [--enrich xbrl]
```

*Note: If an error occurs, read `cli.log` for details.*

### 3. Refine for Analysis
The raw artifacts (`insider_raw.json`, `pref_raw.json`, `qip_raw.json`) are often too large for context. **ALWAYS** run the `refine` command to create a compact, LLM-optimized JSON.

**Refine Insider Trading (with Presets):**
```bash
uv run nse-corporate-data insider-trading refine [--preset market|market-buy|market-sell|buy|sell|forced-sales]
```
*   `market`: (Default) Open market buys/sells.
*   `forced-sales`: Pledge invocations (strong negative signal).
*   `buy`/`sell`: Comprehensive list including ESOPs, allotments, etc.

**Refine Further Issues:**
```bash
uv run nse-corporate-data further-issues refine --category pref
uv run nse-corporate-data further-issues refine --category qip
```

### 4. Analyze and Present
Read the refined artifacts (`insider.json`, `pref.json`, `qip.json`). These are structured to highlight the most important fields (e.g., `transactionValue`, `holdingDeltaPct`, `allotmentDate`).

**Analysis Guidelines:**
*   **Insider Trading**: Look for clusters of buying/selling, large transaction values (relative to market cap if available), or "forced-sales" (pledge invocations).
*   **Further Issues**: Check the issue price vs. current market price and the list of allottees (for QIPs) to identify institutional interest.
*   **Synthesis**: Do not dump raw JSON. Provide a structured summary with clear signals.
