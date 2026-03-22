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
uv run nse-corporate-data further-issues fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--category pref] [--category qip]
```
*(Omit `--category` to fetch both).*

**For Insider Trading:**
```bash
uv run nse-corporate-data insider-trading fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--mode market]
```
*(Note: `--mode market` is the default and covers market purchases and sales. You can repeat the `--mode` flag to include others like `block-deal`, `preferential-offer`, `buy-back`, `esop`, etc.)*

*Troubleshooting: If the fetch command outputs an `{"error": "..."}`, read the `cli.log` file to diagnose the issue.*

### 3. Shorten the Data for Analysis
The raw fetched artifacts (`pref_data.json`, `qip_data.json`, `insider_trading_data.json`) are deeply nested and large. **Always** run the shorten command to generate compact, LLM-friendly artifacts before you attempt to read or analyze the data.

**For Further Issues:**
```bash
uv run nse-corporate-data further-issues shorten --category pref
uv run nse-corporate-data further-issues shorten --category qip
```
*(Produces `pref_short.json` and `qip_short.json`)*

**For Insider Trading:**
```bash
uv run nse-corporate-data insider-trading shorten
```
*(Produces `insider_trading_short.json`)*

### 4. Analyze and Present
Read the resulting `*_short.json` file. These files are optimized for your context window and contain metadata-aligned arrays (e.g., separate `record`, `industry`, and `marketData` blocks).

Synthesize the information intelligently based on the user's original request. Highlight key signals such as large transaction values, significant percentage changes in holdings, or notable market data context. Do not simply dump the raw JSON back to the user.