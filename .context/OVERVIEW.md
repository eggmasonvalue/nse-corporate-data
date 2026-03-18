# Overview

## Purpose
Collect and normalize NSE corporate data for downstream agent and automation workflows.

## Description
A CLI designed to fetch and normalize selected corporate-data disclosures from the National Stock Exchange (NSE) of India.

The implemented CLI currently supports two workflows:

- `further-issues`: preferential allotments (`PREF`), QIPs (`QIP`), or both
- `insider-trading`: insider trading disclosures

Each workflow fetches filing metadata from NSE, downloads linked XBRL documents, enriches rows with four-level industry mapping from `eggmasonvalue/stock-industry-map-in`, fetches Current Market Price (CMP) for stock symbols, and writes normalized JSON output. Robust retry mechanisms (via `tenacity`) ensure consistency during API flakes.

The project depends on `nse-xbrl-parser`, resolved by `uv` from the GitHub HTTPS repository at `https://github.com/eggmasonvalue/nse-xbrl-parser.git`.

## CLI Usage
The application provides a CLI (`uv run nse-corporate-data`) with dedicated subcommands for each workflow. The `further-issues` command accepts `--from-date`, optional `--to-date`, and optional `--categories`; `--to-date` defaults to the local run date and `--categories` defaults to `BOTH`. The `insider-trading` command accepts `--from-date` and optional `--to-date`. Execution runs silently, diverting all logging to `cli.log`, making it LLM-agent friendly. Outputs are saved as normalized JSON files.
