import logging
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from nse import NSE

from .retries import retry_exchange, should_retry_exception

logger = logging.getLogger(__name__)
MARKET_DATA_METADATA = [
    "currentPrice",
    "sharesOutstanding",
    "freeFloatMarketCap",
    "priceToEarnings",
    "fiftyTwoWeekHigh",
    "fiftyTwoWeekLow",
]
VALID_SERIES: Sequence[str] = ("EQ", "BE", "BZ", "SM", "ST", "SZ")


class NSEFetcher:
    def __init__(self, download_folder: Optional[str] = None):
        if download_folder is None:
            self._temp_dir_obj = tempfile.TemporaryDirectory(
                prefix="nse_corporate_data_"
            )
            self._temp_dir = self._temp_dir_obj.name
            self.download_folder = Path(self._temp_dir)
        else:
            self._temp_dir_obj = None
            self._temp_dir = None
            self.download_folder = Path(download_folder)
            self.download_folder.mkdir(parents=True, exist_ok=True)

        self.nse = NSE(download_folder=str(self.download_folder), server=True)

        # Initialize cookies
        self._init_session()
        self._industry_data_cache: Optional[Dict[str, Any]] = None
        self._market_data_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def _init_session(self):
        try:
            self.nse._session.get("https://www.nseindia.com", timeout=10)
        except Exception as e:
            logger.error(f"Failed to initialize NSE session: {e}")

    @retry_exchange
    def fetch_corporate_filings(
        self, category: str, from_date: str, to_date: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch corporate filings for a given category (PREF or QIP) within a date range.
        Dates should be in DD-MM-YYYY format.
        """
        if category.upper() == "PREF":
            url = f"https://www.nseindia.com/api/corporate-further-issues-pref?index=FIPREFLS&from_date={from_date}&to_date={to_date}"
            referer = (
                "https://www.nseindia.com/companies-listing/corporate-filings-PREF"
            )
        elif category.upper() == "QIP":
            url = f"https://www.nseindia.com/api/corporate-further-issues-qip?index=FIQIPLS&from_date={from_date}&to_date={to_date}"
            referer = "https://www.nseindia.com/companies-listing/corporate-filings-QIP"
        else:
            raise ValueError(f"Unknown category: {category}")

        return self._fetch_json_rows(url, referer, f"{category} filings")

    @retry_exchange
    def fetch_insider_trading(
        self, from_date: str, to_date: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch insider trading disclosures within a date range.
        Dates should be in DD-MM-YYYY format.
        """
        url = f"https://www.nseindia.com/api/corporates-pit?index=equities&from_date={from_date}&to_date={to_date}"
        referer = "https://www.nseindia.com/companies-listing/corporate-filings-insider-trading"
        return self._fetch_json_rows(url, referer, "insider trading filings")

    def _fetch_json_rows(
        self, url: str, referer: str, label: str
    ) -> List[Dict[str, Any]]:
        headers = {"Referer": referer, "Accept": "*/*"}

        logger.info(f"Fetching {label} from {url}")
        try:
            response = self.nse._session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json().get("data", [])
            logger.info(f"Found {len(data)} items for {label}")
            return data
        except Exception as e:
            if should_retry_exception(e):
                raise e
            logger.error(f"Error fetching {label}: {e}")
            return []

    @retry_exchange
    def download_xbrl_file(self, xbrl_url: str) -> Optional[Path]:
        """
        Download the XBRL XML file from the given URL.
        """
        if not xbrl_url:
            return None

        filename = xbrl_url.split("/")[-1]
        save_path = self.download_folder / filename

        try:
            headers = {"Accept": "*/*"}
            full_url = (
                xbrl_url
                if xbrl_url.startswith("http")
                else f"https://www.nseindia.com{xbrl_url}"
            )
            logger.debug(f"Downloading XBRL from {full_url}")

            # Use stream semantics for httpx
            with self.nse._session.stream(
                "GET", full_url, headers=headers, timeout=30
            ) as response:
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            return save_path
        except Exception as e:
            if should_retry_exception(e):
                raise e
            logger.error(f"Failed to download XBRL file from {xbrl_url}: {e}")
            return None

    @retry_exchange
    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed market data for a given equity symbol."""
        if not symbol:
            return None
        if symbol in self._market_data_cache:
            return self._market_data_cache[symbol]
        last_error: Optional[Exception] = None
        for series in VALID_SERIES:
            try:
                market_data = self.nse.getDetailedScripData(symbol, series=series)
                if self._has_usable_market_data(market_data):
                    logger.debug(
                        "Fetched market data for %s using series %s", symbol, series
                    )
                    self._market_data_cache[symbol] = market_data
                    return market_data
                logger.info(
                    "Market data for %s returned empty for series %s; trying next series",
                    symbol,
                    series,
                )
            except Exception as e:
                if should_retry_exception(e):
                    raise e
                last_error = e
                logger.warning(
                    "Market data fetch for %s failed for series %s: %s",
                    symbol,
                    series,
                    e,
                )
        if last_error is not None:
            logger.error(f"Failed to fetch market data for {symbol}: {last_error}")
        else:
            logger.error(
                "Failed to fetch market data for %s: no usable response for any series",
                symbol,
            )
        self._market_data_cache[symbol] = None
        return None

    @staticmethod
    def _has_usable_market_data(market_data: Optional[Dict[str, Any]]) -> bool:
        if not market_data:
            return False
        equity_response = market_data.get("equityResponse")
        if not isinstance(equity_response, list) or not equity_response:
            return False

        for entry in equity_response:
            if not isinstance(entry, dict):
                continue
            for key in ("metaData", "tradeInfo", "priceInfo", "secInfo"):
                value = entry.get(key)
                if isinstance(value, dict) and value:
                    return True
        return False

    def get_industry_data(self) -> Dict[str, Any]:
        """
        Fetch industry data from the eggmasonvalue/stock-industry-map-in repository
        using ETag for lazy/conditional downloading.
        """
        if self._industry_data_cache:
            return self._industry_data_cache

        cache_dir = Path.home() / ".nse_corporate_data"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / "industry_cache.json"
        url = "https://raw.githubusercontent.com/eggmasonvalue/stock-industry-map-in/main/out/industry_data.json"

        headers = {}
        cached_data = {"metadata": [], "data": {}, "etag": None}

        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("etag"):
                        headers["If-None-Match"] = cached_data["etag"]
            except Exception as e:
                logger.warning(f"Failed to read industry cache: {e}")

        logger.info("Checking for industry data updates...")
        try:
            response = self.nse._session.get(url, headers=headers, timeout=15)

            if response.status_code == 304:
                logger.info("Industry data is up to date (304 Not Modified)")
                self._industry_data_cache = {
                    "metadata": cached_data.get("metadata", []),
                    "data": cached_data.get("data", {}),
                }
                return self._industry_data_cache

            response.raise_for_status()

            new_data = response.json()
            etag = response.headers.get("ETag")

            # Update local cache file
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "metadata": new_data.get("metadata", []),
                        "data": new_data.get("data", {}),
                        "etag": etag,
                    },
                    f,
                    indent=2,
                )

            logger.info("Industry data updated and cached.")
            self._industry_data_cache = new_data
            return self._industry_data_cache

        except Exception as e:
            logger.error(f"Failed to fetch/update industry data: {e}")
            # Fallback to cache if available
            if cached_data.get("data"):
                logger.info("Falling back to local industry cache.")
                return {
                    "metadata": cached_data.get("metadata", []),
                    "data": cached_data.get("data", {}),
                }
            return {"metadata": [], "data": {}}

    def close(self):
        self.nse.exit()
        if hasattr(self, "_temp_dir_obj") and self._temp_dir_obj:
            try:
                self._temp_dir_obj.cleanup()
                logger.debug(f"Deleted temporary directory: {self._temp_dir}")
            except Exception as e:
                logger.error(
                    f"Failed to delete temporary directory {self._temp_dir}: {e}"
                )
