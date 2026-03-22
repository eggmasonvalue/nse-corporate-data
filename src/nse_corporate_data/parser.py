import json
import logging
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
from nse_xbrl_parser import parse_xbrl_file
from nse_corporate_data.fetcher import MARKET_DATA_METADATA

logger = logging.getLogger(__name__)
_MARKET_DATA_RELEVANT_ACQ_MODES = {"Market Purchase", "Market Sale"}


def _empty_results(enrichments: Sequence[str] = ()) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "api": [],
    }
    if "xbrl" in enrichments:
        metadata["xbrl"] = []
    if "industry" in enrichments:
        metadata["industry"] = []
    if "market-data" in enrichments:
        metadata["marketData"] = MARKET_DATA_METADATA

    return {
        "metadata": metadata,
        "data": [],
    }


def _resolve_first(item: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        value = item.get(key)
        if value:
            return value
    return None


def _first_nonzero(*values: Any) -> Optional[Any]:
    for value in values:
        if value not in (None, 0, 0.0, "0", "0.0"):
            return value
    return None


def _extract_market_data(detailed_data: Dict[str, Any]) -> List[Optional[Any]]:
    response = detailed_data.get("equityResponse", [])
    if not response:
        return [None] * len(MARKET_DATA_METADATA)

    item = response[0]
    meta_data = item.get("metaData") or {}
    trade_info = item.get("tradeInfo") or {}
    price_info = item.get("priceInfo") or {}
    sec_info = item.get("secInfo") or {}

    current_price = _first_nonzero(
        meta_data.get("closePrice"),
        trade_info.get("lastPrice"),
        meta_data.get("previousClose"),
    )

    return [
        current_price,
        trade_info.get("issuedSize"),
        trade_info.get("ffmc"),
        sec_info.get("pdSymbolPe"),
        price_info.get("yearHigh"),
        price_info.get("yearLow"),
    ]


def parse_filings_data(
    filings: List[Dict[str, Any]],
    fetcher: Any,
    symbol_keys: Iterable[str],
    xbrl_keys: Iterable[str],
    api_label_map: Optional[Mapping[str, str]] = None,
    enrichments: Sequence[str] = (),
) -> Dict[str, Any]:
    """
    Given a list of JSON payload items from NSE, extract metadata into a dict
    with "metadata" headers and normalized row data.
    """
    if not filings:
        return _empty_results(enrichments)

    # Dynamically extract all unique API keys from NSE JSON payloads
    unique_api_keys = set()
    for item in filings:
        unique_api_keys.update(item.keys())

    sorted_api_keys = sorted(list(unique_api_keys))

    api_label_map = api_label_map or {}
    api_metadata = [api_label_map.get(key, key) for key in sorted_api_keys]

    # PASS 1: Fetch and parse all XBRL dicts, collect all unique XBRL keys
    records = []
    unique_xbrl_keys = set()

    for item in filings:
        base_row = [item.get(key) for key in sorted_api_keys]

        symbol = _resolve_first(item, symbol_keys)
        if not symbol:
            symbol = "UNKNOWN"

        xbrl_url = _resolve_first(item, xbrl_keys)
        parsed_xbrl = {}

        if "xbrl" in enrichments and xbrl_url:
            xml_path = fetcher.download_xbrl_file(xbrl_url)
            if xml_path and xml_path.exists():
                try:
                    logger.debug(f"Parsing XBRL file: {xml_path}")
                    xbrl_data = parse_xbrl_file(str(xml_path))
                    if xbrl_data and isinstance(xbrl_data, dict):
                        parsed_xbrl = xbrl_data
                        unique_xbrl_keys.update(parsed_xbrl.keys())
                except Exception as e:
                    logger.error(f"Failed to parse XBRL file {xml_path}: {e}")

        records.append(
            {
                "symbol": symbol,
                "base_row": base_row,
                "xbrl_dict": parsed_xbrl,
                "source_item": item,
            }
        )

    # PASS 2: Construct metadata and flattened data arrays
    sorted_xbrl_keys = sorted(list(unique_xbrl_keys))

    industry_metadata = []
    industry_map = {}
    if "industry" in enrichments:
        industry_data = fetcher.get_industry_data()
        industry_metadata = industry_data.get("metadata", [])
        industry_map = industry_data.get("data", {})

    metadata_dict = {"api": api_metadata}
    if "xbrl" in enrichments:
        metadata_dict["xbrl"] = sorted_xbrl_keys
    if "industry" in enrichments:
        metadata_dict["industry"] = industry_metadata
    if "market-data" in enrichments:
        metadata_dict["marketData"] = MARKET_DATA_METADATA

    results = {
        "metadata": metadata_dict,
        "data": [],
    }

    for rec in records:
        symbol = rec["symbol"]

        row_dict = {"api": rec["base_row"]}

        if "xbrl" in enrichments:
            row_dict["xbrl"] = [rec["xbrl_dict"].get(k) for k in sorted_xbrl_keys]

        if "market-data" in enrichments:
            market_data_values = [None] * len(MARKET_DATA_METADATA)
            if symbol != "UNKNOWN":
                detailed_data = fetcher.get_market_data(symbol)
                if detailed_data:
                    market_data_values = _extract_market_data(detailed_data)
            row_dict["marketData"] = market_data_values

        if "industry" in enrichments:
            row_dict["industry"] = industry_map.get(symbol, [])

        results["data"].append(row_dict)

    return results


def save_to_json(data: Dict[str, Any], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    count = len(data.get("data", []))
    logger.info(f"Saved {count} records to {output_path}")
