# nse-corporate-data

CLI tool for collecting NSE corporate data, downloading linked XBRL documents, and flattening the result into JSON.

## What it does

The project currently fetches and parses:

- Further issue filings for preferential allotments (`PREF`)
- Further issue filings for qualified institutional placements (`QIP`)
- Insider trading disclosures (`insider-trading`)

For each workflow, the CLI:

1. Calls the relevant NSE API for a date range.
2. Downloads the linked XBRL document when one is present.
3. Attempts to parse the XBRL into a flat dictionary using `nse-xbrl-parser`.
4. Fetches four-level industry mapping (Macro, Sector, Industry, Basic Industry) from `eggmasonvalue/stock-industry-map-in`.
5. Fetches Current Market Price (CMP) for stock symbols.
6. Writes normalized JSON output files for downstream processing.

## Requirements

- Python 3.12+
- `uv`

## Installation

Install dependencies with:

```bash
uv sync
```

`uv` resolves `nse-xbrl-parser` directly from `https://github.com/eggmasonvalue/nse-xbrl-parser.git`.

## Usage

### Further issues

```bash
uv run nse-corporate-data further-issues --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--categories PREF|QIP|BOTH]
```

Example:

```bash
uv run nse-corporate-data further-issues --from-date 01-03-2026
```

Defaults:

- `--to-date`: current local date when the command runs
- `--categories`: `BOTH`

### Insider trading

```bash
uv run nse-corporate-data insider-trading --from-date DD-MM-YYYY [--to-date DD-MM-YYYY]
```

Example:

```bash
uv run nse-corporate-data insider-trading --from-date 18-09-2025
```

## Outputs

The commands are intentionally silent on stdout/stderr except for a minimal JSON result:

- success: `{"files":[...]}`
- failure: `{"error":"..."}`

Execution details are written to:

- `cli.log`: execution log, overwritten on each run

Data files:

- `pref_data.json`
- `qip_data.json`
- `insider_trading_data.json`

Output shape:

```json
{
  "metadata": {
    "api": ["..."],
    "xbrl": ["..."],
    "industry": ["Macro", "Sector", "Industry", "Basic Industry"],
    "CMP": ["CMP"]
  },
  "data": [
    {
      "symbol": "SYMBOL",
      "api": ["..."],
      "xbrl": ["..."],
      "industry": ["...", "...", "...", "..."],
      "CMP": 123.45
    }
  ]
}
```

- `metadata.api`: sorted keys observed in the NSE API payload
- `metadata.xbrl`: sorted keys observed across parsed XBRL documents
- `metadata.industry`: labels for the four-level industry classification
- `metadata.CMP`: label for the CMP column
- `data[].symbol`: resolved NSE symbol for the row
- `data[].api`: row values aligned to `metadata.api`
- `data[].xbrl`: row values aligned to `metadata.xbrl`
- `data[].industry`: classification values aligned to `metadata.industry`
- `data[].CMP`: current market price (last close) for the symbol

## Insider trading XBRL note

The insider trading workflow downloads the linked XML and attempts to parse it with `nse-xbrl-parser`, but current NSE insider-trading taxonomy resolution is broken upstream. When parsing fails for that reason, the command still succeeds and writes API, industry, and CMP data with empty XBRL fields.

## Project Structure

- `src/nse_corporate_data/cli.py`: Click CLI entrypoint and input validation
- `src/nse_corporate_data/fetcher.py`: NSE session management, filing fetches, XBRL downloads
- `src/nse_corporate_data/parser.py`: XBRL parsing and JSON serialization

## Testing

Run:

```bash
uv run pytest
```
