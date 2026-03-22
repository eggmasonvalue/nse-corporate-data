import os
from pathlib import Path
from types import SimpleNamespace
from nse_corporate_data.fetcher import NSEFetcher


def test_fetcher_creates_and_deletes_temp_dir():
    # Arrange & Act
    fetcher = NSEFetcher()

    # Assert
    assert fetcher._temp_dir is not None
    assert os.path.exists(fetcher._temp_dir)
    assert Path(fetcher._temp_dir).is_dir()

    # Act
    temp_dir_path = fetcher._temp_dir
    fetcher.close()

    # Assert
    assert not os.path.exists(temp_dir_path)


def test_fetcher_uses_provided_download_folder(tmp_path):
    # Arrange
    custom_dir = str(tmp_path / "custom_downloads")

    # Act
    fetcher = NSEFetcher(download_folder=custom_dir)

    # Assert
    assert fetcher._temp_dir is None
    assert fetcher.download_folder == Path(custom_dir)
    assert fetcher.download_folder.exists()

    # Act
    fetcher.close()

    # Assert
    # The provided directory shouldn't be deleted by the fetcher
    assert os.path.exists(custom_dir)


def test_get_market_data_uses_fetcher_cache():
    # Arrange
    calls = []
    fetcher = NSEFetcher.__new__(NSEFetcher)
    fetcher._market_data_cache = {}
    fetcher.nse = SimpleNamespace(
        getDetailedScripData=lambda symbol, series="EQ": (
            calls.append((symbol, series))
            or {"equityResponse": [{"tradeInfo": {"lastPrice": 123.45}}]}
        )
    )

    # Act
    first = fetcher.get_market_data("ABC")
    second = fetcher.get_market_data("ABC")

    # Assert
    assert first == {"equityResponse": [{"tradeInfo": {"lastPrice": 123.45}}]}
    assert second == {"equityResponse": [{"tradeInfo": {"lastPrice": 123.45}}]}
    assert calls == [("ABC", "EQ")]


def test_get_market_data_retries_next_series_when_response_is_empty():
    # Arrange
    calls = []

    def get_detailed_scrip_data(symbol, series="EQ"):
        calls.append((symbol, series))
        if series == "EQ":
            return {
                "equityResponse": [
                    {
                        "orderBook": None,
                        "metaData": None,
                        "tradeInfo": None,
                        "priceInfo": None,
                        "secInfo": None,
                        "lastUpdateTime": None,
                    }
                ]
            }
        if series == "BE":
            return {
                "equityResponse": [
                    {
                        "metaData": {"symbol": symbol, "series": series},
                        "tradeInfo": {"lastPrice": 2285.1},
                        "priceInfo": {"yearHigh": 3894.7},
                        "secInfo": {"basicIndustry": "IT Enabled Services"},
                    }
                ]
            }
        raise AssertionError(f"Unexpected series call: {series}")

    fetcher = NSEFetcher.__new__(NSEFetcher)
    fetcher._market_data_cache = {}
    fetcher.nse = SimpleNamespace(getDetailedScripData=get_detailed_scrip_data)

    # Act
    result = fetcher.get_market_data("E2E")

    # Assert
    assert result == {
        "equityResponse": [
            {
                "metaData": {"symbol": "E2E", "series": "BE"},
                "tradeInfo": {"lastPrice": 2285.1},
                "priceInfo": {"yearHigh": 3894.7},
                "secInfo": {"basicIndustry": "IT Enabled Services"},
            }
        ]
    }
    assert calls == [("E2E", "EQ"), ("E2E", "BE")]
