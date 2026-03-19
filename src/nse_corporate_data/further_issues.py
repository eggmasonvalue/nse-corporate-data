from typing import Any, Dict, Mapping, Sequence

from nse_corporate_data.shorten import ShortField, build_short_output

DEFAULT_PREF_FULL_OUTPUT = "pref_data.json"
DEFAULT_PREF_SHORT_OUTPUT = "pref_short.json"

PREF_SHORT_FIELDS: Sequence[ShortField] = (
    ShortField("symbol", lambda context: context.get("symbol")),
    ShortField("company", lambda context: context.get("nameOfTheCompany")),
    ShortField(
        "allotmentDate",
        lambda context: context.get("dateOfAllotmentOfShares"),
    ),
    ShortField(
        "amountRaised",
        lambda context: context.get("amountRaised") or context.get("Amount raised"),
    ),
    ShortField(
        "sharesAllotted",
        lambda context: context.get("totalNumOfSharesAllotted")
        or context.get("Total number of shares allotted"),
    ),
    ShortField(
        "offerPrice",
        lambda context: context.get("offerPricePerSecurity")
        or context.get("Offer price per security"),
    ),
    ShortField("currentPrice", lambda context: context.get("currentPrice")),
    ShortField(
        "lockInShares",
        lambda context: context.get("Number of lock in shares"),
    ),
    ShortField(
        "lockInPeriod",
        lambda context: context.get("Period of lock in shares"),
    ),
    ShortField("revisedFlag", lambda context: context.get("revisedFlag")),
    ShortField("Macro", lambda context: context.get("Macro")),
    ShortField("Sector", lambda context: context.get("Sector")),
    ShortField("Industry", lambda context: context.get("Industry")),
    ShortField("Basic Industry", lambda context: context.get("Basic Industry")),
)


def build_pref_short_output(
    full_output: Mapping[str, Any],
    fields: Sequence[ShortField] = PREF_SHORT_FIELDS,
) -> Dict[str, Any]:
    return build_short_output(full_output, fields)
