from pathlib import Path

import nse_corporate_data.parser as parser_module


class FakeFetcher:
    def __init__(self, xml_path: Path):
        self.xml_path = xml_path

    def download_xbrl_file(self, xbrl_url: str):
        return self.xml_path

    def get_industry_data(self):
        return {
            "metadata": ["Macro", "Sector", "Industry", "Basic Industry"],
            "data": {"ABC": ["M", "S", "I", "B"]},
        }

    def get_quote(self, symbol: str):
        return {"priceInfo": {"close": 123.45}}


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
                "xbrl": "https://example.com/it.xml",
            }
        ],
        fetcher=FakeFetcher(xml_path),
        symbol_keys=("symbol",),
        xbrl_keys=("xbrl",),
    )

    assert result["metadata"]["api"] == ["company", "symbol", "xbrl"]
    assert result["metadata"]["xbrl"] == ["Field A", "Field B"]
    assert result["data"] == [
        {
            "symbol": "ABC",
            "api": ["Example Corp", "ABC", "https://example.com/it.xml"],
            "xbrl": ["value-a", "value-b"],
            "industry": ["M", "S", "I", "B"],
            "CMP": 123.45,
        }
    ]


def test_parse_filings_data_logs_and_continues_on_xbrl_parse_failure(tmp_path, monkeypatch):
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
    )

    assert result["metadata"]["xbrl"] == []
    assert result["data"][0]["xbrl"] == []
