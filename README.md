# further-issue-tracker

CLI tool for collecting NSE further-issue filing data, downloading linked XBRL documents, and flattening the result into JSON.

## What it does

The project currently fetches and parses:

- Preferential allotment filings (`PREF`)
- Qualified Institutional Placement filings (`QIP`)

For each filing, the CLI:

1. Calls the relevant NSE corporate filings API for a date range.
2. Downloads the linked XBRL document when one is present.
3. Parses the XBRL into a flat dictionary using `nse-xbrl-parser`.
4. Writes normalized JSON output files for downstream processing.

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

Run the CLI with:

```bash
uv run further-issue-tracker fetch --from-date DD-MM-YYYY --to-date DD-MM-YYYY --category PREF|QIP|BOTH
```

Example:

```bash
uv run further-issue-tracker fetch --from-date 01-03-2026 --to-date 12-03-2026 --category BOTH
```

### Arguments

- `--from-date`: start date in `DD-MM-YYYY`
- `--to-date`: end date in `DD-MM-YYYY`
- `--category`: `PREF`, `QIP`, or `BOTH`

## Outputs

The command is intentionally silent on stdout/stderr. Inspect these files after a run:

- `cli.log`: execution log, overwritten on each run
- `pref_data.json`: output for `PREF`
- `qip_data.json`: output for `QIP`

When `--category BOTH` is used, both JSON files are produced.

Output shape:

```json
{
  "metadata": {
    "api": ["..."],
    "xbrl": ["..."]
  },
  "data": {
    "SYMBOL": {
      "api": ["..."],
      "xbrl": ["..."]
    }
  }
}
```

- `metadata.api`: sorted keys observed in the NSE API payload
- `metadata.xbrl`: sorted keys observed across parsed XBRL documents
- `data[SYMBOL].api`: row values aligned to `metadata.api`
- `data[SYMBOL].xbrl`: row values aligned to `metadata.xbrl`

## Project Structure

- `src/further_issue_tracker/cli.py`: Click CLI entrypoint and input validation
- `src/further_issue_tracker/fetcher.py`: NSE session management, filing fetches, XBRL downloads
- `src/further_issue_tracker/parser.py`: XBRL parsing and JSON serialization

## Testing

Run:

```bash
uv run pytest
```

Current automated coverage is minimal; there is only a placeholder test in `tests/`.
