from typing import Any, Dict, List, Mapping, Sequence

from nse_corporate_data.refine import RefinedField, build_refined_output

DEFAULT_PREF_FULL_OUTPUT = "pref_raw.json"
DEFAULT_PREF_REFINED_OUTPUT = "pref.json"
DEFAULT_QIP_FULL_OUTPUT = "qip_raw.json"
DEFAULT_QIP_REFINED_OUTPUT = "qip.json"

PREF_API_LABELS = {
    "amountRaised": "amountRaised",
    "appId": "applicationId",
    "boardResDate": "boardResolutionDate",
    "corporateIdentityNum": "corporateIdentityNumber",
    "dateOfAllotmentOfShares": "allotmentDate",
    "dateOfListing": "listingDate",
    "dateOfSubmission": "submissionDate",
    "dateOfTradingApproval": "tradingApprovalDate",
    "isin": "isin",
    "issueType": "issueType",
    "nameOfTheCompany": "company",
    "nseSymbol": "symbol",
    "numberOfEquitySharesListed": "sharesListed",
    "offerPricePerSecurity": "offerPrice",
    "revisedFlag": "revisedFlag",
    "stage": "filingStage",
    "systemDate": "exchangeRecordDate",
    "totalNumOfSharesAllotted": "sharesAllotted",
    "xbrlFileSize": "xbrlFileSize",
    "xmlFileName": "xbrlUrl",
}

QIP_API_LABELS = {
    "appId": "applicationId",
    "boardResolutionDate": "boardResolutionDate",
    "companyName": "company",
    "corporateIdentityNumber": "corporateIdentityNumber",
    "dateOfListing": "listingDate",
    "dateOfSubmission": "submissionDate",
    "dateOfTradingApproval": "tradingApprovalDate",
    "distPerShrsAvailed": "discountPerShare",
    "dtOfAllotmentOfShares": "allotmentDate",
    "dtOfBIDClosing": "bidClosingDate",
    "dtOfBIDOpening": "bidOpeningDate",
    "finalAmountOfIssueSize": "issueSize",
    "isin": "isin",
    "issPricePerUnit": "issuePrice",
    "issue_type": "issueType",
    "minIssPricePerUnit": "minimumIssuePrice",
    "noOfAllottees": "allotteeCount",
    "noOfEquitySharesListed": "sharesListed",
    "noOfSharesAllotted": "sharesAllotted",
    "nsesymbol": "symbol",
    "relavantDt": "relevantDate",
    "revisedFlag": "revisedFlag",
    "stage": "filingStage",
    "xbrlFileSize": "xbrlFileSize",
    "xmlFileName": "xbrlUrl",
}

PREF_REFINED_FIELDS: Sequence[RefinedField] = (
    RefinedField("symbol", lambda context: context.get("symbol")),
    RefinedField("company", lambda context: context.get("company")),
    RefinedField(
        "allotmentDate",
        lambda context: context.get("allotmentDate"),
    ),
    RefinedField(
        "amountRaised",
        lambda context: context.get("amountRaised") or context.get("Amount raised"),
    ),
    RefinedField(
        "sharesAllotted",
        lambda context: (
            context.get("sharesAllotted")
            or context.get("Total number of shares allotted")
        ),
    ),
    RefinedField(
        "offerPrice",
        lambda context: (
            context.get("offerPrice") or context.get("Offer price per security")
        ),
    ),
    RefinedField(
        "lockInShares",
        lambda context: context.get("Number of lock in shares"),
    ),
    RefinedField(
        "lockInPeriod",
        lambda context: context.get("Period of lock in shares"),
    ),
    RefinedField("revisedFlag", lambda context: context.get("revisedFlag")),
)


def build_pref_refined_output(
    full_output: Mapping[str, Any],
    fields: Sequence[RefinedField] = PREF_REFINED_FIELDS,
) -> Dict[str, Any]:
    return build_refined_output(full_output, fields)


def _normalize_allottee_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _qip_participant_shares(context: Mapping[str, Any]) -> List[Any]:
    raw_values = _normalize_allottee_list(context.get("Number of shares allotted"))
    no_of_allottees = context.get("allotteeCount")

    try:
        expected_participants = (
            int(no_of_allottees) if no_of_allottees is not None else None
        )
    except (TypeError, ValueError):
        expected_participants = None

    if (
        expected_participants is not None
        and len(raw_values) == expected_participants + 1
    ):
        return raw_values[1:]
    return raw_values


QIP_REFINED_FIELDS: Sequence[RefinedField] = (
    RefinedField("symbol", lambda context: context.get("symbol")),
    RefinedField("company", lambda context: context.get("company")),
    RefinedField(
        "allotmentDate",
        lambda context: (
            context.get("allotmentDate") or context.get("Date of allotment of shares")
        ),
    ),
    RefinedField(
        "relevantDate",
        lambda context: context.get("relevantDate") or context.get("Relavant date"),
    ),
    RefinedField(
        "issueSize",
        lambda context: (
            context.get("issueSize") or context.get("Final amount of issue size")
        ),
    ),
    RefinedField(
        "issuePrice",
        lambda context: (
            context.get("issuePrice") or context.get("Issue price per unit")
        ),
    ),
    RefinedField(
        "minimumIssuePrice",
        lambda context: (
            context.get("minimumIssuePrice")
            or context.get("Minimum issue price per unit")
        ),
    ),
    RefinedField(
        "discountPerShare",
        lambda context: (
            context.get("discountPerShare")
            or context.get("Discount per shares availed")
        ),
    ),
    RefinedField(
        "sharesAllotted",
        lambda context: context.get("sharesAllotted"),
    ),
    RefinedField(
        "allotteeCount",
        lambda context: (
            context.get("allotteeCount") or context.get("Number of allottees")
        ),
    ),
    RefinedField("revisedFlag", lambda context: context.get("revisedFlag")),
    RefinedField(
        "allotteeNames",
        lambda context: _normalize_allottee_list(context.get("Name of allottees")),
    ),
    RefinedField(
        "allotteeCategories",
        lambda context: _normalize_allottee_list(context.get("Category of allotees")),
    ),
    RefinedField("allotteeSharesAllotted", _qip_participant_shares),
    RefinedField(
        "allotteePctOfIssue",
        lambda context: _normalize_allottee_list(
            context.get("Percentage of total issue size")
        ),
    ),
)


def build_qip_refined_output(
    full_output: Mapping[str, Any],
    fields: Sequence[RefinedField] = QIP_REFINED_FIELDS,
) -> Dict[str, Any]:
    return build_refined_output(full_output, fields)
