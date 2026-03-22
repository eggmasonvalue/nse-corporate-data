# Architecture

```mermaid
graph TD
    subgraph nse-corporate-data
        cli[cli.py]
        further[further_issues.py]
        fetcher[fetcher.py]
        insider[insider.py]
        parser[parser.py]
        refine[refine.py]
        
        cli --> fetcher
        cli --> further
        cli --> insider
        cli --> parser
        further --> refine
        insider --> refine
        fetcher --> nse[NSE APIs]
        fetcher --> industry[stock-industry-map-in GitHub]
        parser --> nsexbrl[nse_xbrl_parser]
        insider --> json[Refined JSON artifacts]
        further --> json[Refined JSON artifacts]
        parser --> json[JSON artifacts]
    end
```

`cli.py` exposes grouped workflows: `further-issues fetch`, `further-issues refine`, `insider-trading fetch`, and `insider-trading refine`. Both fetch commands optionally accept repeatable `--enrich` flags (`market-data`, `industry`, `xbrl`) to pull expensive data. `insider-trading fetch` pulls all raw data unconditionally. `fetcher.py` owns NSE session setup, JSON endpoint fetches, XBRL downloads, detailed scrip-data lookups, and cached industry-map retrieval; detailed market-data responses are cached per symbol to avoid repeated NSE hits within a run, and `getDetailedScripData` retries the valid series set (`EQ`, `BE`, `BZ`, `SM`, `ST`, `SZ`) when NSE returns an empty shell response for the default series. `parser.py` normalizes heterogeneous NSE payloads through configurable symbol/XBRL field mapping, rewrites full-artifact API labels into workflow-specific consumer-facing names, conditionally enriches each row based on the requested `--enrich` flags, completely omitting keys that are not requested, and emits rows as metadata-aligned array blocks without duplicating `symbol` as a separate row key. `refine.py` provides the shared metadata-driven local refinement helper, while `further_issues.py` and `insider.py` each define workflow-specific declarative field registries and builder functions. `insider.py` implements signal-focused presets (`market`, `buy`, `sell`) to filter rows before refinement. Refined artifacts now retain the raw-artifact block shape with separate `record`, `industry`, and `marketData` arrays instead of flattening those blocks together, and the refined row objects likewise omit a duplicate top-level `symbol`. `further-issues refine` switches between preferential and QIP registries based on `--category`, with category-specific default input/output paths. Both further-issue refined artifacts preserve `revisedFlag` so consumers can detect revised or duplicate filings.
