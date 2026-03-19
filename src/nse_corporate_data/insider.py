from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Mapping, Sequence

from nse_corporate_data.shorten import ShortField, build_short_output

INSIDER_MODE_TO_ACQ_MODE = {
    "unknown": ("-",),
    "allotment": ("Allotment",),
    "beneficiary-from-trusts": ("Beneficiary from Trusts",),
    "block-deal": ("Block Deal",),
    "bonus": ("Bonus",),
    "buy-back": ("Buy Back",),
    "conversion": ("Conversion of security",),
    "esop": ("ESOP",),
    "esos": ("ESOS",),
    "gift": ("Gift",),
    "inheritance": ("Inheritance",),
    "inter-se-transfer": ("Inter-se-Transfer",),
    "pledge-invoke": ("Invocation of pledge",),
    "market": ("Market Purchase", "Market Sale"),
    "market-buy": ("Market Purchase",),
    "market-sell": ("Market Sale",),
    "off-market": ("Off Market",),
    "others": ("Others",),
    "pledge-create": ("Pledge Creation",),
    "preferential-offer": ("Preferential Offer",),
    "public-right": ("Public Right",),
    "pledge-release": ("Pledge Release",),
    "pledge-revoke": ("Revocation of Pledge",),
    "scheme": ("Scheme of Amalgamation/Merger/Demerger/Arrangement",),
}

INSIDER_MODES = tuple(INSIDER_MODE_TO_ACQ_MODE.keys())
DEFAULT_INSIDER_MODES = ("market",)
DEFAULT_INSIDER_FULL_OUTPUT = "insider_trading_data.json"
DEFAULT_INSIDER_SHORT_OUTPUT = "insider_trading_short.json"

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
    before = _to_decimal(context.get("holdingBeforePct"))
    after = _to_decimal(context.get("holdingAfterPct"))
    if before is None or after is None:
        return None
    return _coerce_number(after - before)


INSIDER_SHORT_FIELDS: Sequence[ShortField] = (
    ShortField("symbol", lambda context: context.get("symbol")),
    ShortField("company", lambda context: context.get("company")),
    ShortField("transactionMode", lambda context: context.get("transactionMode")),
    ShortField("tradeDate", _trade_date),
    ShortField(
        "transactionValue",
        lambda context: _coerce_number(_to_decimal(context.get("transactionValue"))),
    ),
    ShortField("pricePerShare", _price_per_share),
    ShortField("holdingDeltaPct", _holding_delta_pct),
)


def filter_insider_filings_by_mode(
    filings: List[Dict[str, Any]], modes: tuple[str, ...]
) -> List[Dict[str, Any]]:
    if not modes:
        return filings

    allowed_modes = {
        acq_mode
        for mode in modes
        for acq_mode in INSIDER_MODE_TO_ACQ_MODE[mode]
    }
    return [item for item in filings if item.get("acqMode") in allowed_modes]


def build_insider_short_output(
    full_output: Mapping[str, Any],
    fields: Sequence[ShortField] = INSIDER_SHORT_FIELDS,
) -> Dict[str, Any]:
    return build_short_output(full_output, fields)
