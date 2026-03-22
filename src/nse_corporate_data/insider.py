from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Mapping, Sequence

from nse_corporate_data.refine import RefinedField, build_refined_output

BUY_PRESET_MODES = [
    "Market Purchase",
    "Preferential Offer",
    "Allotment",
    "Block Deal",
    "Conversion of security",
    "ESOP",
    "ESOS",
    "Public Right",
    "Off Market",
]

SELL_PRESET_MODES = [
    "Market Sale",
    "Block Deal",
    "Off Market",
    "ESOP",
    "ESOS",
    "Market Purchase",
]
# Note: "Invocation of pledge" is omitted from sell preset due to inconsistent data quality

INSIDER_PRESETS = ("market", "market-buy", "market-sell", "buy", "sell", "forced-sales")
DEFAULT_INSIDER_FULL_OUTPUT = "insider_raw.json"
DEFAULT_INSIDER_REFINED_OUTPUT = "insider.json"

INSIDER_API_LABELS = {
    "acqMode": "transactionMode",
    "acqName": "personName",
    "acqfromDt": "transactionStartDate",
    "acqtoDt": "transactionEndDate",
    "afterAcqSharesNo": "holdingAfterShares",
    "afterAcqSharesPer": "holdingAfterPct",
    "anex": "annexure",
    "befAcqSharesNo": "holdingBeforeShares",
    "befAcqSharesPer": "holdingBeforePct",
    "buyQuantity": "reportedBuyQuantity",
    "buyValue": "reportedBuyValue",
    "company": "company",
    "date": "filingDateTime",
    "derivativeType": "derivativeType",
    "did": "disclosureId",
    "exchange": "exchange",
    "intimDt": "intimationDate",
    "personCategory": "personCategory",
    "pid": "personId",
    "remarks": "remarks",
    "secAcq": "transactionQuantity",
    "secType": "securityType",
    "secVal": "transactionValue",
    "securitiesTypePost": "postTransactionSecurityType",
    "sellValue": "reportedSellValue",
    "sellquantity": "reportedSellQuantity",
    "symbol": "symbol",
    "tdpDerivativeContractType": "derivativeContractType",
    "tdpTransactionType": "transactionDirection",
    "tkdAcqm": "additionalTransactionDetail",
    "xbrl": "xbrlUrl",
    "xbrlFileSize": "xbrlFileSize",
}


def _to_decimal(value: Any) -> Decimal | None:
    if value in (None, "", "-", "None"):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _coerce_number(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    if value == value.to_integral():
        return int(value)
    return float(value)


def _trade_date(context: Mapping[str, Any]) -> str | None:
    from_date = context.get("transactionStartDate")
    to_date = context.get("transactionEndDate")
    if from_date and to_date and from_date != to_date:
        return f"{from_date} to {to_date}"
    return to_date or from_date


def _price_per_share(context: Mapping[str, Any]) -> int | float | None:
    transaction_value = _to_decimal(context.get("transactionValue"))
    quantity = _to_decimal(context.get("transactionQuantity"))
    if transaction_value is None or quantity in (None, Decimal("0")):
        return None
    return _coerce_number(transaction_value / quantity)


def _holding_delta_pct(context: Mapping[str, Any]) -> int | float | None:
    before_shares = _to_decimal(context.get("holdingBeforeShares"))
    after_shares = _to_decimal(context.get("holdingAfterShares"))
    shares_out = _to_decimal(context.get("sharesOutstanding"))

    if before_shares is not None and after_shares is not None and shares_out:
        return _coerce_number(
            (after_shares - before_shares) / shares_out * Decimal("100")
        )

    before = _to_decimal(context.get("holdingBeforePct"))
    after = _to_decimal(context.get("holdingAfterPct"))
    if before is None or after is None:
        return None
    return _coerce_number(after - before)


INSIDER_REFINED_FIELDS: Sequence[RefinedField] = (
    RefinedField("symbol", lambda context: context.get("symbol")),
    RefinedField("company", lambda context: context.get("company")),
    RefinedField("transactionMode", lambda context: context.get("transactionMode")),
    RefinedField("tradeDate", _trade_date),
    RefinedField(
        "transactionValue",
        lambda context: _coerce_number(_to_decimal(context.get("transactionValue"))),
    ),
    RefinedField("pricePerShare", _price_per_share),
    RefinedField("holdingDeltaPct", _holding_delta_pct),
)


def filter_insider_filings_by_preset(
    data: Dict[str, Any], preset: str
) -> Dict[str, Any]:
    filtered_data = []
    metadata = data.get("metadata", {})
    api_fields = metadata.get("api", [])
    seen_transactions = set()

    for row in data.get("data", []):
        context = dict(zip(api_fields, row.get("api", [])))
        acq_mode = context.get("transactionMode")
        direction = context.get("transactionDirection")
        sec_type = context.get("postTransactionSecurityType")

        if preset == "market":
            if acq_mode in ["Market Purchase", "Market Sale"]:
                filtered_data.append(row)
        elif preset == "market-buy":
            if acq_mode == "Market Purchase":
                filtered_data.append(row)
        elif preset == "market-sell":
            if acq_mode == "Market Sale":
                filtered_data.append(row)
        elif preset == "buy":
            if (
                direction == "Buy"
                and sec_type == "Equity Shares"
                and acq_mode in BUY_PRESET_MODES
            ):
                filtered_data.append(row)
        elif preset == "sell":
            if (
                direction == "Sell"
                and sec_type == "Equity Shares"
                and acq_mode in SELL_PRESET_MODES
            ):
                filtered_data.append(row)
        elif preset == "forced-sales":
            dir_lower = str(direction).lower()
            mode_lower = str(acq_mode).lower()
            if "pledge invoke" in dir_lower or "invocation" in mode_lower:
                symbol = context.get("symbol")
                person = context.get("personName")
                qty = context.get("transactionQuantity")
                date = context.get("transactionStartDate")

                key = (symbol, person, qty, date)
                if key not in seen_transactions:
                    filtered_data.append(row)
                    seen_transactions.add(key)

    return {"metadata": metadata, "data": filtered_data}


def build_insider_refined_output(
    full_output: Mapping[str, Any],
    fields: Sequence[RefinedField] = INSIDER_REFINED_FIELDS,
) -> Dict[str, Any]:
    return build_refined_output(full_output, fields)
