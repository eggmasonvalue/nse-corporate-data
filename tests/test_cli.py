import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

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
    assert json.loads(result.output) == {"files": ["pref_data.json", "qip_data.json"]}
    assert saved == ["pref_data.json", "qip_data.json"]

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
            ["further-issues", "fetch", "--from-date", "01-03-2026", "--category", "pref"],
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


def test_further_issues_shorten_writes_expected_metadata(monkeypatch, tmp_path):
    runner = CliRunner()

    def fail_fetcher():
        raise AssertionError("shorten should not instantiate NSEFetcher")

    monkeypatch.setattr(cli_module, "NSEFetcher", fail_fetcher)

    full_output = {
        "metadata": {
            "api": [
                "amountRaised",
                "dateOfAllotmentOfShares",
                "nameOfTheCompany",
                "offerPricePerSecurity",
                "revisedFlag",
                "totalNumOfSharesAllotted",
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
                "symbol": "ABC",
                "api": [
                    "1000",
                    "18-MAR-2026",
                    "ABC Limited",
                    "95",
                    "REV-1",
                    "10",
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
        input_path = Path("pref_data.json")
        input_path.write_text(json.dumps(full_output), encoding="utf-8")
        result = runner.invoke(
            cli_module.cli,
            ["further-issues", "shorten"],
        )
        shortened = json.loads(Path("pref_short.json").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["pref_short.json"]}
    assert shortened["metadata"] == [
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
        "Basic Industry",
    ]
    assert shortened["data"] == [
        [
            "ABC",
            "ABC Limited",
            "18-MAR-2026",
            "1000",
            "10",
            "95",
            110,
            "4",
            "Equity shares for 6 months",
            "REV-1",
            "Industrials",
            "Capital Goods",
            "Electrical Equipment",
            "Other Electrical Equipment",
        ]
    ]


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
    monkeypatch.setattr(
        cli_module,
        "get_settings",
        lambda: SimpleNamespace(enable_insider_trading_xbrl=False),
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            ["insider-trading", "fetch", "--from-date", "18-09-2025"],
        )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["insider_trading_data.json"]}
    assert saved == ["insider_trading_data.json"]

    today = datetime.now().strftime("%d-%m-%Y")
    assert fetchers[0].calls == [
        ("insider_trading", "18-09-2025", today),
    ]
    assert parse_calls[0]["enable_xbrl_processing"] is False
    assert [row["symbol"] for row in parse_calls[0]["filings"]] == ["ABC", "XYZ"]
    assert fetchers[0].closed is True


def test_insider_trading_fetch_filters_by_mode(monkeypatch, tmp_path):
    runner = CliRunner()
    parse_calls = []

    monkeypatch.setattr(cli_module, "NSEFetcher", DummyFetcher)
    monkeypatch.setattr(
        cli_module,
        "parse_filings_data",
        lambda **kwargs: parse_calls.append(kwargs) or EMPTY_PARSED,
    )
    monkeypatch.setattr(cli_module, "save_to_json", lambda data, output_path: None)
    monkeypatch.setattr(
        cli_module,
        "get_settings",
        lambda: SimpleNamespace(enable_insider_trading_xbrl=False),
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            [
                "insider-trading",
                "fetch",
                "--from-date",
                "18-09-2025",
                "--mode",
                "market-buy",
                "--mode",
                "gift",
            ],
        )

    assert result.exit_code == 0
    assert [row["symbol"] for row in parse_calls[0]["filings"]] == ["ABC"]


def test_insider_trading_fetch_help_lists_mode_choices(tmp_path):
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli_module.cli, ["insider-trading", "fetch", "--help"])

    assert result.exit_code == 0
    assert "market-buy" in result.output
    assert "market-sell" in result.output
    assert "preferential-offer" in result.output
    assert "--mode" in result.output


def test_insider_trading_fetch_filters_by_single_mode(monkeypatch, tmp_path):
    runner = CliRunner()
    parse_calls = []

    monkeypatch.setattr(cli_module, "NSEFetcher", DummyFetcher)
    monkeypatch.setattr(
        cli_module,
        "parse_filings_data",
        lambda **kwargs: parse_calls.append(kwargs) or EMPTY_PARSED,
    )
    monkeypatch.setattr(cli_module, "save_to_json", lambda data, output_path: None)
    monkeypatch.setattr(
        cli_module,
        "get_settings",
        lambda: SimpleNamespace(enable_insider_trading_xbrl=False),
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            [
                "insider-trading",
                "fetch",
                "--from-date",
                "18-09-2025",
                "--mode",
                "market-buy",
            ],
        )

    assert result.exit_code == 0
    assert [row["symbol"] for row in parse_calls[0]["filings"]] == ["ABC"]


def test_insider_trading_shorten_writes_expected_metadata(monkeypatch, tmp_path):
    runner = CliRunner()

    def fail_fetcher():
        raise AssertionError("shorten should not instantiate NSEFetcher")

    monkeypatch.setattr(cli_module, "NSEFetcher", fail_fetcher)

    full_output = {
        "metadata": {
            "api": [
                "acqMode",
                "acqfromDt",
                "acqtoDt",
                "afterAcqSharesPer",
                "befAcqSharesPer",
                "company",
                "secAcq",
                "secVal",
            ],
            "xbrl": [],
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
                "symbol": "ABC",
                "api": [
                    "Market Purchase",
                    "18-Mar-2026",
                    "18-Mar-2026",
                    "1.30",
                    "1.00",
                    "ABC Limited",
                    "10",
                    "1000",
                ],
                "xbrl": [],
                "industry": ["Industrials", "Capital Goods", "Electrical Equipment", "Other Electrical Equipment"],
                "marketData": [95, 1000, 25000, "18.5", 150, 80],
            }
        ],
    }

    with runner.isolated_filesystem(temp_dir=tmp_path):
        input_path = Path("insider_trading_data.json")
        input_path.write_text(json.dumps(full_output), encoding="utf-8")
        result = runner.invoke(
            cli_module.cli,
            ["insider-trading", "shorten"],
        )
        shortened = json.loads(Path("insider_trading_short.json").read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["insider_trading_short.json"]}
    assert shortened["metadata"] == [
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
        "Basic Industry",
    ]
    assert shortened["data"] == [
        [
            "ABC",
            "ABC Limited",
            "Market Purchase",
            "18-Mar-2026",
            1000,
            100,
            95,
            0.3,
            "Industrials",
            "Capital Goods",
            "Electrical Equipment",
            "Other Electrical Equipment",
        ]
    ]
