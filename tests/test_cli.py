import json
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

import nse_corporate_data.cli as cli_module


class DummyFetcher:
    def __init__(self):
        self.calls = []
        self.closed = False

    def fetch_corporate_filings(self, category, from_date, to_date):
        self.calls.append(("further_issues", category, from_date, to_date))
        return [{"nsesymbol": "ABC", "xmlFileName": "https://example.com/test.xml"}]

    def fetch_insider_trading(self, from_date, to_date):
        self.calls.append(("insider_trading", from_date, to_date))
        return [
            {
                "symbol": "ABC",
                "company": "ABC Limited",
                "acqMode": "Market Purchase",
                "acqfromDt": "18-Mar-2026",
                "acqtoDt": "18-Mar-2026",
                "secVal": "1000",
                "secAcq": "10",
                "befAcqSharesPer": "1.00",
                "afterAcqSharesPer": "1.10",
                "xbrl": "https://example.com/test.xml",
            },
            {
                "symbol": "XYZ",
                "company": "XYZ Limited",
                "acqMode": "Market Sale",
                "acqfromDt": "18-Mar-2026",
                "acqtoDt": "18-Mar-2026",
                "secVal": "500",
                "secAcq": "5",
                "befAcqSharesPer": "2.00",
                "afterAcqSharesPer": "1.80",
                "xbrl": "https://example.com/test-2.xml",
            },
        ]

    def close(self):
        self.closed = True


EMPTY_PARSED = {
    "metadata": {
        "api": [],
        "xbrl": [],
        "industry": [],
        "marketData": [
            "currentPrice",
            "sharesOutstanding",
            "freeFloatMarketCap",
            "priceToEarnings",
            "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow",
        ],
    },
    "data": [],
}


def test_further_issues_fetch_defaults_to_both_and_today(monkeypatch, tmp_path):
    runner = CliRunner()
    saved = []
    fetchers = []

    def fetcher_factory():
        fetcher = DummyFetcher()
        fetchers.append(fetcher)
        return fetcher

    monkeypatch.setattr(cli_module, "NSEFetcher", fetcher_factory)
    monkeypatch.setattr(cli_module, "parse_filings_data", lambda **kwargs: EMPTY_PARSED)
    monkeypatch.setattr(
        cli_module, "save_to_json", lambda data, output_path: saved.append(output_path)
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            ["further-issues", "fetch", "--from-date", "01-03-2026"],
        )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["pref_raw.json", "qip_raw.json"]}
    assert saved == ["pref_raw.json", "qip_raw.json"]

    today = datetime.now().strftime("%d-%m-%Y")
    assert fetchers[0].calls == [
        ("further_issues", "PREF", "01-03-2026", today),
        ("further_issues", "QIP", "01-03-2026", today),
    ]
    assert fetchers[0].closed is True


def test_further_issues_fetch_filters_by_repeatable_category(monkeypatch, tmp_path):
    runner = CliRunner()
    fetchers = []

    def fetcher_factory():
        fetcher = DummyFetcher()
        fetchers.append(fetcher)
        return fetcher

    monkeypatch.setattr(cli_module, "NSEFetcher", fetcher_factory)
    monkeypatch.setattr(cli_module, "parse_filings_data", lambda **kwargs: EMPTY_PARSED)
    monkeypatch.setattr(cli_module, "save_to_json", lambda data, output_path: None)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            [
                "further-issues",
                "fetch",
                "--from-date",
                "01-03-2026",
                "--category",
                "pref",
            ],
        )

    assert result.exit_code == 0
    today = datetime.now().strftime("%d-%m-%Y")
    assert fetchers[0].calls == [
        ("further_issues", "PREF", "01-03-2026", today),
    ]


def test_further_issues_fetch_rejects_inverted_date_range(monkeypatch, tmp_path):
    runner = CliRunner()
    saved = []

    monkeypatch.setattr(cli_module, "NSEFetcher", DummyFetcher)
    monkeypatch.setattr(cli_module, "parse_filings_data", lambda **kwargs: EMPTY_PARSED)
    monkeypatch.setattr(
        cli_module, "save_to_json", lambda data, output_path: saved.append(output_path)
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            [
                "further-issues",
                "fetch",
                "--from-date",
                "18-03-2026",
                "--to-date",
                "17-03-2026",
            ],
        )

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert (
        output["error"]
        == "Execution failed: from-date 18-03-2026 cannot be after to-date 17-03-2026"
    )
    assert saved == []


def test_further_issues_refine_writes_expected_metadata(monkeypatch, tmp_path):
    runner = CliRunner()

    def fail_fetcher():
        raise AssertionError("refine should not instantiate NSEFetcher")

    monkeypatch.setattr(cli_module, "NSEFetcher", fail_fetcher)

    full_output = {
        "metadata": {
            "api": [
                "amountRaised",
                "allotmentDate",
                "company",
                "offerPrice",
                "revisedFlag",
                "sharesAllotted",
                "symbol",
            ],
            "xbrl": [
                "Number of lock in shares",
                "Period of lock in shares",
            ],
            "industry": ["Macro", "Sector", "Industry", "Basic Industry"],
            "marketData": [
                "currentPrice",
                "sharesOutstanding",
                "freeFloatMarketCap",
                "priceToEarnings",
                "fiftyTwoWeekHigh",
                "fiftyTwoWeekLow",
            ],
        },
        "data": [
            {
                "api": [
                    "1000",
                    "18-MAR-2026",
                    "ABC Limited",
                    "95",
                    "REV-1",
                    "10",
                    "ABC",
                ],
                "xbrl": ["4", "Equity shares for 6 months"],
                "industry": [
                    "Industrials",
                    "Capital Goods",
                    "Electrical Equipment",
                    "Other Electrical Equipment",
                ],
                "marketData": [110, 1000, 25000, "18.5", 150, 80],
            }
        ],
    }

    with runner.isolated_filesystem(temp_dir=tmp_path):
        input_path = Path("pref_raw.json")
        input_path.write_text(json.dumps(full_output), encoding="utf-8")
        result = runner.invoke(
            cli_module.cli,
            ["further-issues", "refine"],
        )
        refined = json.loads(Path("pref.json").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["pref.json"]}
    assert refined["metadata"] == {
        "record": [
            "symbol",
            "company",
            "allotmentDate",
            "amountRaised",
            "sharesAllotted",
            "offerPrice",
            "lockInShares",
            "lockInPeriod",
            "revisedFlag",
        ],
        "industry": ["Macro", "Sector", "Industry", "Basic Industry"],
        "marketData": [
            "currentPrice",
            "sharesOutstanding",
            "freeFloatMarketCap",
            "priceToEarnings",
            "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow",
        ],
        "xbrl": [
            "Number of lock in shares",
            "Period of lock in shares",
        ],
    }
    assert refined["data"] == [
        {
            "record": [
                "ABC",
                "ABC Limited",
                "18-MAR-2026",
                "1000",
                "10",
                "95",
                "4",
                "Equity shares for 6 months",
                "REV-1",
            ],
            "industry": [
                "Industrials",
                "Capital Goods",
                "Electrical Equipment",
                "Other Electrical Equipment",
            ],
            "marketData": [110, 1000, 25000, "18.5", 150, 80],
            "xbrl": ["4", "Equity shares for 6 months"],
        }
    ]


def test_qip_refine_writes_expected_metadata(monkeypatch, tmp_path):
    runner = CliRunner()

    def fail_fetcher():
        raise AssertionError("refine should not instantiate NSEFetcher")

    monkeypatch.setattr(cli_module, "NSEFetcher", fail_fetcher)

    full_output = {
        "metadata": {
            "api": [
                "company",
                "discountPerShare",
                "allotmentDate",
                "issueSize",
                "issuePrice",
                "minimumIssuePrice",
                "allotteeCount",
                "sharesAllotted",
                "relevantDate",
                "revisedFlag",
                "symbol",
            ],
            "xbrl": [
                "Category of allotees",
                "Name of allottees",
                "Number of shares allotted",
                "Percentage of total issue size",
            ],
            "industry": ["Macro", "Sector", "Industry", "Basic Industry"],
            "marketData": [
                "currentPrice",
                "sharesOutstanding",
                "freeFloatMarketCap",
                "priceToEarnings",
                "fiftyTwoWeekHigh",
                "fiftyTwoWeekLow",
            ],
        },
        "data": [
            {
                "api": [
                    "QIP Example Limited",
                    "9.83",
                    "10-MAR-2026",
                    "750000000",
                    "265",
                    "274.83",
                    "2",
                    "2830188",
                    "02-MAR-2026",
                    None,
                    "QIPX",
                ],
                "xbrl": [
                    ["Foreign Portfolio Investor", "Alternative Investment Fund"],
                    ["Investor A", "Investor B"],
                    ["2830188", "660000", "2170188"],
                    ["0.2332", "0.7668"],
                ],
                "industry": [
                    "Consumer Discretionary",
                    "Realty",
                    "Realty",
                    "Residential, Commercial Projects",
                ],
                "marketData": [305, 124997388, 9199184669.82, "44.81", 321, 137],
            }
        ],
    }

    with runner.isolated_filesystem(temp_dir=tmp_path):
        input_path = Path("qip_raw.json")
        input_path.write_text(json.dumps(full_output), encoding="utf-8")
        result = runner.invoke(
            cli_module.cli,
            ["further-issues", "refine", "--category", "qip"],
        )
        refined = json.loads(Path("qip.json").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["qip.json"]}
    assert "xbrl" in refined["metadata"]


def test_insider_trading_fetch_uses_default_to_date(monkeypatch, tmp_path):
    runner = CliRunner()
    saved = []
    fetchers = []
    parse_calls = []

    def fetcher_factory():
        fetcher = DummyFetcher()
        fetchers.append(fetcher)
        return fetcher

    monkeypatch.setattr(cli_module, "NSEFetcher", fetcher_factory)
    monkeypatch.setattr(
        cli_module,
        "parse_filings_data",
        lambda **kwargs: parse_calls.append(kwargs) or EMPTY_PARSED,
    )
    monkeypatch.setattr(
        cli_module, "save_to_json", lambda data, output_path: saved.append(output_path)
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            ["insider-trading", "fetch", "--from-date", "18-09-2025"],
        )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["insider_raw.json"]}
    assert saved == ["insider_raw.json"]

    today = datetime.now().strftime("%d-%m-%Y")
    assert fetchers[0].calls == [
        ("insider_trading", "18-09-2025", today),
    ]
    assert parse_calls[0]["enrichments"] == ()
    assert [row["symbol"] for row in parse_calls[0]["filings"]] == ["ABC", "XYZ"]
    assert fetchers[0].closed is True


def test_insider_trading_refine_writes_expected_metadata(monkeypatch, tmp_path):
    runner = CliRunner()

    def fail_fetcher():
        raise AssertionError("refine should not instantiate NSEFetcher")

    monkeypatch.setattr(cli_module, "NSEFetcher", fail_fetcher)

    full_output = {
        "metadata": {
            "api": [
                "transactionMode",
                "transactionStartDate",
                "transactionEndDate",
                "holdingAfterPct",
                "holdingBeforePct",
                "company",
                "transactionQuantity",
                "transactionValue",
                "symbol",
                "transactionDirection",
                "postTransactionSecurityType",
            ],
            "industry": ["Macro", "Sector", "Industry", "Basic Industry"],
            "marketData": [
                "currentPrice",
                "sharesOutstanding",
                "freeFloatMarketCap",
                "priceToEarnings",
                "fiftyTwoWeekHigh",
                "fiftyTwoWeekLow",
            ],
        },
        "data": [
            {
                "api": [
                    "Market Purchase",
                    "18-Mar-2026",
                    "18-Mar-2026",
                    "1.30",
                    "1.00",
                    "ABC Limited",
                    "10",
                    "1000",
                    "ABC",
                    "Buy",
                    "Equity Shares",
                ],
                "industry": [
                    "Industrials",
                    "Capital Goods",
                    "Electrical Equipment",
                    "Other Electrical Equipment",
                ],
                "marketData": [95, 1000, 25000, "18.5", 150, 80],
            }
        ],
    }

    with runner.isolated_filesystem(temp_dir=tmp_path):
        input_path = Path("insider_raw.json")
        input_path.write_text(json.dumps(full_output), encoding="utf-8")
        result = runner.invoke(
            cli_module.cli,
            ["insider-trading", "refine", "--preset", "market"],
        )
        refined = json.loads(Path("insider.json").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["insider.json"]}
    assert refined["metadata"] == {
        "record": [
            "symbol",
            "company",
            "transactionMode",
            "tradeDate",
            "transactionValue",
            "pricePerShare",
            "holdingDeltaPct",
        ],
        "industry": ["Macro", "Sector", "Industry", "Basic Industry"],
        "marketData": [
            "currentPrice",
            "sharesOutstanding",
            "freeFloatMarketCap",
            "priceToEarnings",
            "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow",
        ],
    }
    assert refined["data"] == [
        {
            "record": [
                "ABC",
                "ABC Limited",
                "Market Purchase",
                "18-Mar-2026",
                1000,
                100,
                0.3,
            ],
            "industry": [
                "Industrials",
                "Capital Goods",
                "Electrical Equipment",
                "Other Electrical Equipment",
            ],
            "marketData": [95, 1000, 25000, "18.5", 150, 80],
        }
    ]
