# Architecture

```mermaid
graph TD
    subgraph further-issue-tracker
        cli[cli.py]
        fetcher[fetcher.py]
        parser[parser.py]
        
        cli --> fetcher
        cli --> parser
        fetcher --> nse[NSE API]
        fetcher --> industry[stock-industry-map-in GitHub]
        parser --> nsexbrl[nse_xbrl_parser]
        parser --> json[JSON artifacts]
    end
```
