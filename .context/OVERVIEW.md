# Overview

## Purpose
Track preferential allotments, rights issues, and QIPs (Qualified Institutional Placements) of NSE-listed companies.

## Description
A tool designed to monitor and track further issues of companies listed on the National Stock Exchange (NSE) of India.

The implemented CLI currently supports preferential allotments (`PREF`) and QIPs (`QIP`) by fetching filing metadata from NSE, downloading linked XBRL documents, and writing normalized JSON output.

The project depends on `nse-xbrl-parser`, resolved by `uv` from the GitHub HTTPS repository at `https://github.com/eggmasonvalue/nse-xbrl-parser.git`.

## CLI Usage
The application provides a CLI (`uv run further-issue-tracker fetch`) to fetch and parse XBRL information. The CLI supports querying data by date range (`--from-date`, `--to-date`) and by listing category (`--category PREF`, `QIP` or `BOTH`). Execution runs silently, diverting all logging to `cli.log`, making it LLM-agent friendly. Outputs are saved in JSON formulation.
