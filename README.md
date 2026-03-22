# nse-corporate-data

CLI tool for collecting NSE corporate data, downloading linked XBRL documents, and flattening the result into JSON.

## What it does

The project currently supports:

- Further-issue filings for preferential allotments (`PREF`)
- Further-issue filings for qualified institutional placements (`QIP`)
- Preferential-issue refined signal output derived from the full JSON (`further-issues refine`)
- QIP refined debloated output derived from the full JSON (`further-issues refine --category qip`)
- Insider trading disclosures (`insider-trading fetch`)
- Insider trading refined signal output derived from the full JSON (`insider-trading refine`)

For fetch workflows, the CLI:

1. Calls the relevant NSE API for a date range.
2. Downloads the linked XBRL document when one is present.
3. Attempts to parse the XBRL into a flat dictionary using `nse-xbrl-parser`.
4. Fetches four-level industry mapping (Macro, Sector, Industry, Basic Industry) from `eggmasonvalue/stock-industry-map-in`.
5. Fetches a compact market-data snapshot for stock symbols, currently limited to insider `acqMode` values `Market Purchase` and `Market Sale` for insider trading. Insider mode filtering itself supports the broader NSE acquisition-mode enum. Detailed scrip-data fetches retry across valid NSE series values (`EQ`, `BE`, `BZ`, `SM`, `ST`, `SZ`) when the initial response is structurally empty.
6. Writes normalized JSON output files for downstream processing.

For insider trading, the CLI also provides a pure local refinement step that reads the full insider artifact and emits a compact signal-focused JSON with only the most important fields for top-down analysis.

For further issues, the CLI provides pure local refinement steps for both preferential allotments and QIPs. The preferential refiner reads `pref_raw.json` and emits a compact JSON focused on amount raised, pricing, lock-in terms, revision lineage, and four-level industry context. The QIP refiner reads `qip_raw.json` and emits a debloated issue-plus-allottee view that preserves pricing, size, revision lineage, investor participation detail, four-level industry context, and market data.

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
uv run nse-corporate-data further-issues fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--category pref|qip...] [--enrich market-data|industry|xbrl...]
```

Example:

```bash
uv run nse-corporate-data further-issues fetch --from-date 01-03-2026 --enrich market-data --enrich industry
```

Defaults:

- `--to-date`: current local date when the command runs
- `--category`: both `pref` and `qip`
- `--enrich`: none

### Further issue refine

```bash
uv run nse-corporate-data further-issues refine [--category pref|qip] [--input FILE] [--output FILE]
```

Example:

```bash
uv run nse-corporate-data further-issues refine
uv run nse-corporate-data further-issues refine --category qip
```

Defaults:

- `--category`: `pref`
- `--input`: `pref_raw.json` for `pref`, `qip_raw.json` for `qip`
- `--output`: `pref.json` for `pref`, `qip.json` for `qip`

### Insider trading fetch

```bash
uv run nse-corporate-data insider-trading fetch --from-date DD-MM-YYYY [--to-date DD-MM-YYYY] [--enrich market-data|industry|xbrl...]
```

Example:

```bash
uv run nse-corporate-data insider-trading fetch --from-date 18-09-2025 --enrich industry
```

Defaults:

- `--to-date`: current local date when the command runs
- `--enrich`: none

### Insider trading refine

```bash
uv run nse-corporate-data insider-trading refine [--input FILE] [--output FILE] [--preset PRESET]
```

Example:

```bash
uv run nse-corporate-data insider-trading refine
uv run nse-corporate-data insider-trading refine --preset market-buy
```

Supported insider presets:

- `market`: Market Purchase and Market Sale
- `market-buy`: Market Purchase only
- `market-sell`: Market Sale only
- `buy`: Signal-focused buys including allotments and preferential offers
- `sell`: Signal-focused sells
- `forced-sales`: Pledged/invoked sales

Defaults:

- `--input`: `insider_raw.json`
- `--output`: `insider.json`
- `--preset`: `market`

### Configuration

- `NSE_CORPORATE_DATA_ENABLE_INSIDER_TRADING_XBRL=false` by default

## Outputs

The commands are intentionally silent on stdout/stderr except for a minimal JSON result:

- success: `{"files":[...]}`
- failure: `{"error":"..."}`

Execution details are written to:

- `cli.log`: execution log, overwritten on each run

Data files:

- `pref_raw.json`
- `pref.json`
- `qip_raw.json`
- `qip.json`
- `insider_raw.json`
- `insider.json`

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
      "api": ["..."],
      "xbrl": ["..."],
      "industry": ["...", "...", "...", "..."],
      "marketData": [123.45, 1000000, 123456789.0, "18.5", 150.0, 80.0]
    }
  ]
}
```

- `metadata.api`: canonical consumer-facing labels aligned to the NSE API payload values
- `metadata.xbrl`: sorted keys observed across parsed XBRL documents
- `metadata.industry`: labels for the four-level industry classification
- `metadata.marketData`: labels for the compact market-data block
- `data[].api`: row values aligned to `metadata.api`
- `data[].xbrl`: row values aligned to `metadata.xbrl`
- `data[].industry`: classification values aligned to `metadata.industry`
- `data[].marketData`: row values aligned to `metadata.marketData`
- `symbol` is carried inside the metadata-aligned row arrays rather than duplicated as a standalone top-level key inside each `data[]` object
- `currentPrice`: uses `closePrice`, then `lastPrice`, then `previousClose`, while treating zero-valued fields as missing
- `marketData` fetches first try NSE series `EQ`; when NSE returns an empty `equityResponse` shell, the fetcher retries the remaining valid series in order until a usable payload is found
- `sharesOutstanding`: total shares outstanding from `issuedSize`
- `freeFloatMarketCap`: free-float market capitalization
- `priceToEarnings`: symbol PE ratio from NSE detailed scrip data
- `fiftyTwoWeekHigh` / `fiftyTwoWeekLow`: 52-week range context

Refined insider-trading output shape:

```json
{
  "metadata": {
    "record": [
      "symbol",
      "company",
      "transactionMode",
      "tradeDate",
      "transactionValue",
      "pricePerShare",
      "holdingDeltaPct"
    ],
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
      "record": ["SYMBOL", "Company", "Market Purchase", "18-Mar-2026", 1000, 100, 0.3],
      "industry": ["...", "...", "...", "..."],
      "marketData": [95, 1000000, 123456789.0, "18.5", 150, 80]
    }
  ]
}
```

The insider refined artifact is driven by a declarative field list in `src/nse_corporate_data/insider.py`, so adding or removing metadata only requires editing that one registry.

Refined preferential-issue output shape:

```json
{
  "metadata": {
    "record": [
      "symbol",
      "company",
      "allotmentDate",
      "amountRaised",
      "sharesAllotted",
      "offerPrice",
      "lockInShares",
      "lockInPeriod",
      "revisedFlag"
    ],
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
      "record": ["SYMBOL", "Company", "18-MAR-2026", "1000", "10", "95", "4", "Equity shares for 6 months", null],
      "industry": ["...", "...", "...", "..."],
      "marketData": [110, 1000000, 123456789.0, "18.5", 150, 80]
    }
  ]
}
```

`revisedFlag` is intentionally preserved. When it is non-null, the filing may have a revised or duplicate lineage that downstream consumers may need to collapse explicitly.

Refined QIP output shape:

```json
{
  "metadata": {
    "record": [
      "symbol",
      "company",
      "allotmentDate",
      "relevantDate",
      "issueSize",
      "issuePrice",
      "minimumIssuePrice",
      "discountPerShare",
      "sharesAllotted",
      "allotteeCount",
      "revisedFlag",
      "allotteeNames",
      "allotteeCategories",
      "allotteeSharesAllotted",
      "allotteePctOfIssue"
    ],
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
      "record": [
        "SYMBOL",
        "Company",
        "10-MAR-2026",
        "02-MAR-2026",
        "750000000",
        "265",
        "274.83",
        "9.83",
        "2830188",
        "6",
        null,
        ["Investor A", "Investor B"],
        ["Foreign Portfolio Investor", "Alternative Investment Fund"],
        ["660000", "2170188"],
        ["0.2332", "0.7668"]
      ],
      "industry": ["...", "...", "...", "..."],
      "marketData": [305, 124997388, 9199184669.82, "44.81", 321, 137]
    }
  ]
}
```

The QIP refined artifact is driven by a declarative field list in `src/nse_corporate_data/further_issues.py`, so debloating or reintroducing metadata is a one-registry edit.

## Insider trading XBRL note

The insider trading workflow can download and parse linked XML through `nse-xbrl-parser`, but this is disabled by default. If enabled, current NSE insider-trading taxonomy resolution may still fail upstream; when that happens, the command continues and writes API, industry, and market-data fields with empty XBRL fields.

## Project Structure

- `src/nse_corporate_data/cli.py`: Click CLI entrypoint and input validation
- `src/nse_corporate_data/further_issues.py`: preferential-issue and QIP refined-output schemas
- `src/nse_corporate_data/fetcher.py`: NSE session management, filing fetches, XBRL downloads
- `src/nse_corporate_data/insider.py`: insider-mode mapping and refined insider-output schema
- `src/nse_corporate_data/parser.py`: XBRL parsing and JSON serialization
- `src/nse_corporate_data/refine.py`: shared helpers for metadata-driven local JSON refinement

## Testing

Run:

```bash
uv run pytest
```
