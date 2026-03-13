import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from nse import NSE

logger = logging.getLogger(__name__)


class NSEFetcher:
    def __init__(self, download_folder: str = "/tmp"):
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self.nse = NSE(download_folder=str(self.download_folder), server=True)

        # Initialize cookies
        self._init_session()

    def _init_session(self):
        try:
            self.nse._session.get("https://www.nseindia.com", timeout=10)
        except Exception as e:
            logger.error(f"Failed to initialize NSE session: {e}")

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

        headers = {"Referer": referer, "Accept": "*/*"}

        logger.info(f"Fetching {category} filings from {from_date} to {to_date}")
        try:
            response = self.nse._session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json().get("data", [])
            logger.info(f"Found {len(data)} items for {category}")
            return data
        except Exception as e:
            logger.error(f"Error fetching {category} filings: {e}")
            return []

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
            logger.error(f"Failed to download XBRL file from {xbrl_url}: {e}")
            return None

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the current quote for a given equity symbol.
        """
        if not symbol:
            return None
        try:
            return self.nse.quote(symbol)
        except Exception as e:
            logger.error(f"Failed to fetch quote for {symbol}: {e}")
            return None

    def close(self):
        self.nse.exit()
