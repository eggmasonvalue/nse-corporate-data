# Overview

## Purpose
Collect and normalize NSE corporate data for downstream agent and automation workflows.

## Description
A CLI designed to fetch and normalize selected corporate-data disclosures from the National Stock Exchange (NSE) of India.

The implemented CLI currently supports two workflows:

- `further-issues fetch`: preferential allotments (`PREF`), QIPs (`QIP`), or both
- `further-issues shorten`: compact preferential-issue JSON or debloated QIP JSON derived from the corresponding full artifact
- `insider-trading fetch`: insider trading disclosures
- `insider-trading shorten`: compact signal-focused insider JSON derived from the full artifact

Each workflow fetches filing metadata from NSE, downloads linked XBRL documents, enriches rows with four-level industry mapping from `eggmasonvalue/stock-industry-map-in`, fetches a compact market-data snapshot for stock symbols, and writes normalized JSON output. Full-artifact `metadata.api` labels are normalized into consumer-facing names rather than exposing raw NSE field names, and row objects keep only metadata-governed arrays instead of duplicating `symbol` as a standalone top-level key. For insider trading, market-data fetches are limited to `Market Purchase` and `Market Sale` rows. Robust retry mechanisms (via `tenacity`) ensure consistency during API flakes. Detailed scrip-data fetches now walk valid NSE series values when the default series returns an empty shell response.

For insider trading, XBRL processing is optional and controlled by configuration; it is disabled by default because the API payload is currently sufficient.

The project depends on `nse-xbrl-parser`, resolved by `uv` from the GitHub HTTPS repository at `https://github.com/eggmasonvalue/nse-xbrl-parser.git`.

The market-data snapshot now comes from NSE `getDetailedScripData` and includes consumer-facing fields such as `currentPrice`, `sharesOutstanding`, `freeFloatMarketCap`, `priceToEarnings`, `fiftyTwoWeekHigh`, and `fiftyTwoWeekLow`.

## CLI Usage
The application provides a nested CLI (`uv run nse-corporate-data`) with workflow groups. `further-issues fetch` accepts `--from-date`, optional `--to-date`, and repeatable canonical `--category` values (`pref`, `qip`); omitting `--category` means both. `further-issues shorten` is a pure local transform that defaults to `pref_data.json -> pref_short.json`, and can switch to `qip_data.json -> qip_short.json` via `--category qip`; both shortened artifacts preserve `revisedFlag` so downstream consumers can reason about revised or duplicate filings, and both keep the raw-artifact shape with separate `record`, `industry`, and `marketData` blocks without a duplicate top-level `symbol` field per row. `insider-trading fetch` accepts `--from-date`, optional `--to-date`, and repeatable canonical `--mode` tokens; it defaults to `market`, which expands to `Market Purchase` and `Market Sale`, while the token registry now covers the broader NSE acquisition-mode enum beyond just market trades. `insider-trading shorten` is a pure local transform that reads `insider_trading_data.json` by default and writes `insider_trading_short.json`, again preserving the raw-artifact block structure. Execution runs silently, diverting all logging to `cli.log`, making it LLM-agent friendly. Outputs are saved as normalized JSON files.
