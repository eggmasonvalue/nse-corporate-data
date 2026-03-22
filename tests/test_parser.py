from pathlib import Path

import nse_corporate_data.parser as parser_module


class FakeFetcher:
    def __init__(self, xml_path: Path):
        self.xml_path = xml_path
        self.download_calls = []
        self.market_data_calls = []

    def download_xbrl_file(self, xbrl_url: str):
        self.download_calls.append(xbrl_url)
        return self.xml_path

    def get_industry_data(self):
        return {
            "metadata": ["Macro", "Sector", "Industry", "Basic Industry"],
            "data": {"ABC": ["M", "S", "I", "B"]},
        }

    def get_market_data(self, symbol: str):
        self.market_data_calls.append(symbol)
        return {
            "equityResponse": [
                {
                    "metaData": {
                        "closePrice": 0,
                        "previousClose": 120.0,
                    },
                    "tradeInfo": {
                        "lastPrice": 123.45,
                        "issuedSize": 1000,
                        "ffmc": 25000.0,
                    },
                    "priceInfo": {
                        "yearHigh": 150.0,
                        "yearLow": 80.0,
                    },
                    "secInfo": {
                        "pdSymbolPe": "18.5",
                    },
                }
            ]
        }


def test_parse_filings_data_supports_custom_symbol_and_xbrl_keys(tmp_path, monkeypatch):
    xml_path = tmp_path / "it.xml"
    xml_path.write_text("<xbrl />", encoding="utf-8")

    monkeypatch.setattr(
        parser_module,
        "parse_xbrl_file",
        lambda path: {"Field B": "value-b", "Field A": "value-a"},
    )

    result = parser_module.parse_filings_data(
        filings=[
            {
                "symbol": "ABC",
                "company": "Example Corp",
                "acqMode": "Market Purchase",
                "xbrl": "https://example.com/it.xml",
            }
        ],
        fetcher=FakeFetcher(xml_path),
        symbol_keys=("symbol",),
        xbrl_keys=("xbrl",),
        api_label_map={
            "acqMode": "transactionMode",
            "company": "company",
            "symbol": "symbol",
            "xbrl": "xbrlUrl",
        },
        enrichments=("xbrl",),
    )

    assert result["metadata"]["api"] == [
        "transactionMode",
        "company",
        "symbol",
        "xbrlUrl",
    ]
    assert result["metadata"]["xbrl"] == ["Field A", "Field B"]
    assert result["data"] == [
        {
            "api": [
                "Market Purchase",
                "Example Corp",
                "ABC",
                "https://example.com/it.xml",
            ],
            "xbrl": ["value-a", "value-b"],
        }
    ]


def test_parse_filings_data_logs_and_continues_on_xbrl_parse_failure(
    tmp_path, monkeypatch
):
    xml_path = tmp_path / "it.xml"
    xml_path.write_text("<xbrl />", encoding="utf-8")

    def raise_parse_error(path):
        raise FileNotFoundError("unsupported taxonomy")

    monkeypatch.setattr(parser_module, "parse_xbrl_file", raise_parse_error)

    result = parser_module.parse_filings_data(
        filings=[
            {
                "symbol": "ABC",
                "company": "Example Corp",
                "xbrl": "https://example.com/it.xml",
            }
        ],
        fetcher=FakeFetcher(xml_path),
        symbol_keys=("symbol",),
        xbrl_keys=("xbrl",),
        api_label_map={"company": "company", "symbol": "symbol", "xbrl": "xbrlUrl"},
        enrichments=("xbrl",),
    )

    assert result["metadata"]["xbrl"] == []
    assert result["data"][0]["xbrl"] == []


def test_parse_filings_data_skips_xbrl_download_when_disabled(tmp_path, monkeypatch):
    xml_path = tmp_path / "it.xml"
    xml_path.write_text("<xbrl />", encoding="utf-8")
    fetcher = FakeFetcher(xml_path)

    def parse_should_not_run(path):
        raise AssertionError("XBRL parsing should be disabled")

    monkeypatch.setattr(parser_module, "parse_xbrl_file", parse_should_not_run)

    result = parser_module.parse_filings_data(
        filings=[
            {
                "symbol": "ABC",
                "company": "Example Corp",
                "xbrl": "https://example.com/it.xml",
            }
        ],
        fetcher=fetcher,
        symbol_keys=("symbol",),
        xbrl_keys=("xbrl",),
        api_label_map={"company": "company", "symbol": "symbol", "xbrl": "xbrlUrl"},
        enrichments=(),
    )

    assert fetcher.download_calls == []
    assert "xbrl" not in result["metadata"]


def test_extract_market_data_uses_price_fallback_when_close_is_zero():
    assert parser_module._extract_market_data(
        {
            "equityResponse": [
                {
                    "metaData": {"closePrice": 0, "previousClose": 40.0},
                    "tradeInfo": {"lastPrice": 42.75, "issuedSize": 10, "ffmc": 100.0},
                    "priceInfo": {"yearHigh": 50.0, "yearLow": 30.0},
                    "secInfo": {"pdSymbolPe": "12.3"},
                }
            ]
        }
    ) == [42.75, 10, 100.0, "12.3", 50.0, 30.0]


def test_parse_filings_data_skips_market_data_when_not_enriched(monkeypatch):
    fetcher = FakeFetcher(Path("."))

    monkeypatch.setattr(parser_module, "parse_xbrl_file", lambda path: {})

    result = parser_module.parse_filings_data(
        filings=[
            {
                "symbol": "ABC",
                "company": "Example Corp",
                "acqMode": "Gift",
            }
        ],
        fetcher=fetcher,
        symbol_keys=("symbol",),
        xbrl_keys=("xbrl",),
        api_label_map={
            "company": "company",
            "symbol": "symbol",
            "acqMode": "transactionMode",
        },
        enrichments=(),
    )

    assert fetcher.market_data_calls == []
    assert "marketData" not in result["metadata"]
    assert "marketData" not in result["data"][0]


def test_parse_filings_data_includes_market_data_when_enriched(monkeypatch):
    fetcher = FakeFetcher(Path("."))

    monkeypatch.setattr(parser_module, "parse_xbrl_file", lambda path: {})

    result = parser_module.parse_filings_data(
        filings=[
            {
                "symbol": "ABC",
                "company": "Example Corp",
                "acqMode": "Gift",
            }
        ],
        fetcher=fetcher,
        symbol_keys=("symbol",),
        xbrl_keys=("xbrl",),
        api_label_map={
            "company": "company",
            "symbol": "symbol",
            "acqMode": "transactionMode",
        },
        enrichments=("market-data",),
    )

    assert fetcher.market_data_calls == ["ABC"]
    assert "marketData" in result["metadata"]
    assert "marketData" in result["data"][0]
