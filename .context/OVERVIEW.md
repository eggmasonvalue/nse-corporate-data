# Overview

## Purpose
Collect and normalize NSE corporate data for downstream agent and automation workflows.

## Description
A CLI designed to fetch and normalize selected corporate-data disclosures from the National Stock Exchange (NSE) of India.

The implemented CLI currently supports two workflows:

- `further-issues fetch`: preferential allotments (`PREF`), QIPs (`QIP`), or both
- `further-issues refine`: compact preferential-issue JSON or debloated QIP JSON derived from the corresponding full artifact
- `insider-trading fetch`: insider trading disclosures
- `insider-trading refine`: compact signal-focused insider JSON derived from the full artifact

Each workflow fetches filing metadata from NSE, and can optionally enrich rows with four-level industry mapping, compact market-data snapshots, and downloaded XBRL documents via opt-in `--enrich` flags. Full-artifact `metadata.api` labels are normalized into consumer-facing names rather than exposing raw NSE field names, and row objects keep only metadata-governed arrays instead of duplicating `symbol` as a standalone top-level key. To conserve tokens for downstream agents, if an enrichment is not requested, its corresponding metadata and row data keys are completely omitted from the generated JSON artifacts. Robust retry mechanisms (via `tenacity`) ensure consistency during API flakes. Detailed scrip-data fetches walk valid NSE series values when the default series returns an empty shell response.

For insider trading, XBRL processing is completely optional and controlled by the `--enrich xbrl` flag.

The project depends on `nse-xbrl-parser`, resolved by `uv` from the GitHub HTTPS repository at `https://github.com/eggmasonvalue/nse-xbrl-parser.git`.

The optional market-data snapshot comes from NSE `getDetailedScripData` and includes consumer-facing fields such as `currentPrice`, `sharesOutstanding`, `freeFloatMarketCap`, `priceToEarnings`, `fiftyTwoWeekHigh`, and `fiftyTwoWeekLow`.

## CLI Usage
The application provides a nested CLI (`uv run nse-corporate-data`) with workflow groups. `further-issues fetch` accepts `--from-date`, optional `--to-date`, repeatable canonical `--category` values (`pref`, `qip`), and optional `--enrich` choices (`market-data`, `industry`, `xbrl`). `further-issues refine` is a pure local transform that defaults to `pref_data.json -> pref_refined.json`, and can switch to `qip_data.json -> qip_refined.json` via `--category qip`; both refined artifacts preserve `revisedFlag` so downstream consumers can reason about revised or duplicate filings, and both keep the raw-artifact shape with separate `record`, `industry`, and `marketData` blocks without a duplicate top-level `symbol` field per row. `insider-trading fetch` accepts `--from-date`, optional `--to-date`, and `--enrich` flags; it unconditionally fetches all raw modes without filtering. `insider-trading refine` is a pure local transform that reads `insider_trading_data.json` by default and writes `insider_trading_refined.json`; it accepts a `--preset` flag (`market`, `buy`, `sell`) to filter for high-signal stake changes. Execution runs silently, diverting all logging to `cli.log`, making it LLM-agent friendly. Outputs are saved as normalized JSON files.
