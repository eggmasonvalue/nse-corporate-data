# nse-corporate-data

CLI tool for collecting NSE corporate data, downloading linked XBRL documents, and flattening the result into JSON.

## What it does

The project currently supports:

- Further issue filings for preferential allotments (`PREF`)
- Further issue filings for qualified institutional placements (`QIP`)
- Preferential-issue short-form signal output derived from the full JSON (`further-issues shorten`)
- Insider trading disclosures (`insider-trading fetch`)
- Insider trading short-form signal output derived from the full JSON (`insider-trading shorten`)

For fetch workflows, the CLI:

1. Calls the relevant NSE API for a date range.
2. Downloads the linked XBRL document when one is present.
3. Attempts to parse the XBRL into a flat dictionary using `nse-xbrl-parser`.
4. Fetches four-level industry mapping (Macro, Sector, Industry, Basic Industry) from `eggmasonvalue/stock-industry-map-in`.
5. Fetches a compact market-data snapshot for stock symbols, currently limited to insider `acqMode` values `Market Purchase` and `Market Sale` for insider trading.
6. Writes normalized JSON output files for downstream processing.

For insider trading, the CLI also provides a pure local shortening step that reads the full insider artifact and emits a compact signal-focused JSON with only the most important fields for top-down analysis.

For further issues, the CLI currently provides a pure local shortening step for preferential allotments. It reads the full `pref_data.json` artifact and emits a compact JSON focused on amount raised, pricing, lock-in terms, revision lineage, and four-level industry context.

For insider trading specifically, XBRL processing is configurable and disabled by default because the API payload is already rich enough for the current use case.

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
uv run nse-corporate-data further-issues fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--category pref|qip...]
```

Example:

```bash
uv run nse-corporate-data further-issues fetch --from-date 01-03-2026
```

Defaults:

- `--to-date`: current local date when the command runs
- `--category`: both `pref` and `qip`

### Preferential issue shorten

```bash
uv run nse-corporate-data further-issues shorten [--input pref_data.json] [--output pref_short.json]
```

Example:

```bash
uv run nse-corporate-data further-issues shorten
```

Defaults:

- `--input`: `pref_data.json`
- `--output`: `pref_short.json`

### Insider trading fetch

```bash
uv run nse-corporate-data insider-trading fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--mode TOKEN...]
```

Example:

```bash
uv run nse-corporate-data insider-trading fetch --from-date 18-09-2025
```

Supported insider mode tokens:

- `market`: `Market Purchase` and `Market Sale`
- `market-buy`: `Market Purchase`
- `market-sell`: `Market Sale`
- `gift`: `Gift`
- `bonus`: `Bonus`
- `conversion`: `Conversion of security`
- `esop`: `ESOP`
- `off-market`: `Off Market`
- `inter-se-transfer`: `Inter-se-Transfer`
- `pledge-create`: `Pledge Creation`
- `pledge-invoke`: `Invocation of pledge`
- `pledge-revoke`: `Revokation of Pledge`
- `preferential-offer`: `Preferential Offer`
- `public-right`: `Public Right`
- `scheme`: `Scheme of Amalgamation/Merger/Demerger/Arrangement`
- `others`: `Others`
- `unknown`: `-`

Defaults:

- `--mode`: `market`
- Repeat `--mode` to include multiple tokens explicitly

### Insider trading shorten

```bash
uv run nse-corporate-data insider-trading shorten [--input insider_trading_data.json] [--output insider_trading_short.json]
```

Example:

```bash
uv run nse-corporate-data insider-trading shorten
```

Defaults:

- `--input`: `insider_trading_data.json`
- `--output`: `insider_trading_short.json`

### Configuration

- `NSE_CORPORATE_DATA_ENABLE_INSIDER_TRADING_XBRL=false` by default

## Outputs

The commands are intentionally silent on stdout/stderr except for a minimal JSON result:

- success: `{"files":[...]}`
- failure: `{"error":"..."}`

Execution details are written to:

- `cli.log`: execution log, overwritten on each run

Data files:

- `pref_data.json`
- `pref_short.json`
- `qip_data.json`
- `insider_trading_data.json`
- `insider_trading_short.json`

Output shape:

```json
{
  "metadata": {
    "api": ["..."],
    "xbrl": ["..."],
    "industry": ["Macro", "Sector", "Industry", "Basic Industry"],
    "marketData": [
      "currentPrice",
      "sharesOutstanding",
      "freeFloatMarketCap",
      "priceToEarnings",
      "fiftyTwoWeekHigh",
      "fiftyTwoWeekLow"
    ]
  },
  "data": [
    {
      "symbol": "SYMBOL",
      "api": ["..."],
      "xbrl": ["..."],
      "industry": ["...", "...", "...", "..."],
      "marketData": [123.45, 1000000, 123456789.0, "18.5", 150.0, 80.0]
    }
  ]
}
```

- `metadata.api`: sorted keys observed in the NSE API payload
- `metadata.xbrl`: sorted keys observed across parsed XBRL documents
- `metadata.industry`: labels for the four-level industry classification
- `metadata.marketData`: labels for the compact market-data block
- `data[].symbol`: resolved NSE symbol for the row
- `data[].api`: row values aligned to `metadata.api`
- `data[].xbrl`: row values aligned to `metadata.xbrl`
- `data[].industry`: classification values aligned to `metadata.industry`
- `data[].marketData`: row values aligned to `metadata.marketData`
- `currentPrice`: uses `closePrice`, then `lastPrice`, then `previousClose`, while treating zero-valued fields as missing
- `sharesOutstanding`: total shares outstanding from `issuedSize`
- `freeFloatMarketCap`: free-float market capitalization
- `priceToEarnings`: symbol PE ratio from NSE detailed scrip data
- `fiftyTwoWeekHigh` / `fiftyTwoWeekLow`: 52-week range context

Short insider-trading output shape:

```json
{
  "metadata": [
    "symbol",
    "company",
    "acqMode",
    "tradeDate",
    "transactionValue",
    "pricePerShare",
    "currentPrice",
    "holdingDeltaPct",
    "Macro",
    "Sector",
    "Industry",
    "Basic Industry"
  ],
  "data": [
    ["SYMBOL", "Company", "Market Purchase", "18-Mar-2026", 1000, 100, 95, 0.3, "...", "...", "...", "..."]
  ]
}
```

The insider short artifact is driven by a declarative field list in `src/nse_corporate_data/insider.py`, so adding or removing metadata only requires editing that one registry.

Short preferential-issue output shape:

```json
{
  "metadata": [
    "symbol",
    "company",
    "allotmentDate",
    "amountRaised",
    "sharesAllotted",
    "offerPrice",
    "currentPrice",
    "lockInShares",
    "lockInPeriod",
    "revisedFlag",
    "Macro",
    "Sector",
    "Industry",
    "Basic Industry"
  ],
  "data": [
    ["SYMBOL", "Company", "18-MAR-2026", "1000", "10", "95", 110, "4", "Equity shares for 6 months", null, "...", "...", "...", "..."]
  ]
}
```

`revisedFlag` is intentionally preserved. When it is non-null, the filing may have a revised or duplicate lineage that downstream consumers may need to collapse explicitly.

## Insider trading XBRL note

The insider trading workflow can download and parse linked XML through `nse-xbrl-parser`, but this is disabled by default. If enabled, current NSE insider-trading taxonomy resolution may still fail upstream; when that happens, the command continues and writes API, industry, and market-data fields with empty XBRL fields.

## Project Structure

- `src/nse_corporate_data/cli.py`: Click CLI entrypoint and input validation
- `src/nse_corporate_data/further_issues.py`: preferential-issue short-output schema
- `src/nse_corporate_data/fetcher.py`: NSE session management, filing fetches, XBRL downloads
- `src/nse_corporate_data/insider.py`: insider-mode mapping and shortened insider-output schema
- `src/nse_corporate_data/parser.py`: XBRL parsing and JSON serialization
- `src/nse_corporate_data/shorten.py`: shared helpers for metadata-driven local JSON shortening

## Testing

Run:

```bash
uv run pytest
```
