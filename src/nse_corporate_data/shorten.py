from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Sequence


@dataclass(frozen=True)
class ShortField:
    name: str
    extractor: Callable[[Mapping[str, Any]], Any]


def build_short_output(
    full_output: Mapping[str, Any],
    fields: Sequence[ShortField],
) -> Dict[str, Any]:
    metadata = full_output.get("metadata", {})
    api_fields = metadata.get("api", [])
    xbrl_fields = metadata.get("xbrl", [])
    industry_fields = metadata.get("industry", [])
    market_data_fields = metadata.get("marketData", [])

    results: Dict[str, Any] = {
        "metadata": [field.name for field in fields],
        "data": [],
    }

    for row in full_output.get("data", []):
        context = {
            "symbol": row.get("symbol"),
        }
        context.update(dict(zip(api_fields, row.get("api", []))))
        context.update(dict(zip(xbrl_fields, row.get("xbrl", []))))
        context.update(dict(zip(industry_fields, row.get("industry", []))))
        context.update(dict(zip(market_data_fields, row.get("marketData", []))))
        results["data"].append([field.extractor(context) for field in fields])

    return results
