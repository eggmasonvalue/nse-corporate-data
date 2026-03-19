from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Mapping, Sequence

from nse_corporate_data.shorten import ShortField, build_short_output

INSIDER_MODE_TO_ACQ_MODE = {
    "unknown": ("-",),
    "bonus": ("Bonus",),
    "conversion": ("Conversion of security",),
    "esop": ("ESOP",),
    "gift": ("Gift",),
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
    "pledge-revoke": ("Revokation of Pledge",),
    "scheme": ("Scheme of Amalgamation/Merger/Demerger/Arrangement",),
}

INSIDER_MODES = tuple(INSIDER_MODE_TO_ACQ_MODE.keys())
DEFAULT_INSIDER_MODES = ("market",)
DEFAULT_INSIDER_FULL_OUTPUT = "insider_trading_data.json"
DEFAULT_INSIDER_SHORT_OUTPUT = "insider_trading_short.json"

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
    from_date = context.get("acqfromDt")
    to_date = context.get("acqtoDt")
    if from_date and to_date and from_date != to_date:
        return f"{from_date} to {to_date}"
    return to_date or from_date


def _price_per_share(context: Mapping[str, Any]) -> int | float | None:
    transaction_value = _to_decimal(context.get("secVal"))
    quantity = _to_decimal(context.get("secAcq"))
    if transaction_value is None or quantity in (None, Decimal("0")):
        return None
    return _coerce_number(transaction_value / quantity)


def _holding_delta_pct(context: Mapping[str, Any]) -> int | float | None:
    before = _to_decimal(context.get("befAcqSharesPer"))
    after = _to_decimal(context.get("afterAcqSharesPer"))
    if before is None or after is None:
        return None
    return _coerce_number(after - before)


INSIDER_SHORT_FIELDS: Sequence[ShortField] = (
    ShortField("symbol", lambda context: context.get("symbol")),
    ShortField("company", lambda context: context.get("company")),
    ShortField("acqMode", lambda context: context.get("acqMode")),
    ShortField("tradeDate", _trade_date),
    ShortField(
        "transactionValue",
        lambda context: _coerce_number(_to_decimal(context.get("secVal"))),
    ),
    ShortField("pricePerShare", _price_per_share),
    ShortField("CMP", lambda context: context.get("CMP")),
    ShortField("holdingDeltaPct", _holding_delta_pct),
    ShortField("Macro", lambda context: context.get("Macro")),
    ShortField("Sector", lambda context: context.get("Sector")),
    ShortField("Industry", lambda context: context.get("Industry")),
    ShortField("Basic Industry", lambda context: context.get("Basic Industry")),
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
