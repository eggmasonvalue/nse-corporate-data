import json
from datetime import datetime

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
        return [{"symbol": "ABC", "xbrl": "https://example.com/test.xml"}]

    def close(self):
        self.closed = True


def test_further_issues_defaults_to_both_and_today(monkeypatch, tmp_path):
    runner = CliRunner()
    saved = []
    fetchers = []

    def fetcher_factory():
        fetcher = DummyFetcher()
        fetchers.append(fetcher)
        return fetcher

    monkeypatch.setattr(cli_module, "NSEFetcher", fetcher_factory)
    monkeypatch.setattr(
        cli_module,
        "parse_filings_data",
        lambda **kwargs: {"metadata": {"api": [], "xbrl": [], "industry": [], "CMP": ["CMP"]}, "data": []},
    )
    monkeypatch.setattr(cli_module, "save_to_json", lambda data, output_path: saved.append(output_path))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            ["further-issues", "--from-date", "01-03-2026"],
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


def test_insider_trading_uses_default_to_date(monkeypatch, tmp_path):
    runner = CliRunner()
    saved = []
    fetchers = []

    def fetcher_factory():
        fetcher = DummyFetcher()
        fetchers.append(fetcher)
        return fetcher

    monkeypatch.setattr(cli_module, "NSEFetcher", fetcher_factory)
    monkeypatch.setattr(
        cli_module,
        "parse_filings_data",
        lambda **kwargs: {"metadata": {"api": [], "xbrl": [], "industry": [], "CMP": ["CMP"]}, "data": []},
    )
    monkeypatch.setattr(cli_module, "save_to_json", lambda data, output_path: saved.append(output_path))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            ["insider-trading", "--from-date", "18-09-2025"],
        )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"files": ["insider_trading_data.json"]}
    assert saved == ["insider_trading_data.json"]

    today = datetime.now().strftime("%d-%m-%Y")
    assert fetchers[0].calls == [
        ("insider_trading", "18-09-2025", today),
    ]
    assert fetchers[0].closed is True


def test_further_issues_rejects_inverted_date_range(monkeypatch, tmp_path):
    runner = CliRunner()
    saved = []

    monkeypatch.setattr(cli_module, "NSEFetcher", DummyFetcher)
    monkeypatch.setattr(
        cli_module,
        "parse_filings_data",
        lambda **kwargs: {"metadata": {"api": [], "xbrl": [], "industry": [], "CMP": ["CMP"]}, "data": []},
    )
    monkeypatch.setattr(cli_module, "save_to_json", lambda data, output_path: saved.append(output_path))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli_module.cli,
            [
                "further-issues",
                "--from-date",
                "18-03-2026",
                "--to-date",
                "17-03-2026",
            ],
        )

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["error"] == "Execution failed: from-date 18-03-2026 cannot be after to-date 17-03-2026"
    assert saved == []
