import sys
import json
import logging
from pathlib import Path
import click
from datetime import datetime
from typing import Any, Callable, Optional

from nse_corporate_data.fetcher import NSEFetcher
from nse_corporate_data.further_issues import (
    DEFAULT_PREF_FULL_OUTPUT,
    DEFAULT_PREF_REFINED_OUTPUT,
    build_pref_refined_output,
    DEFAULT_QIP_FULL_OUTPUT,
    DEFAULT_QIP_REFINED_OUTPUT,
    build_qip_refined_output,
    PREF_API_LABELS,
    QIP_API_LABELS,
)
from nse_corporate_data.insider import (
    DEFAULT_INSIDER_FULL_OUTPUT,
    DEFAULT_INSIDER_REFINED_OUTPUT,
    INSIDER_API_LABELS,
    INSIDER_PRESETS,
    build_insider_refined_output,
    filter_insider_filings_by_preset,
)
from nse_corporate_data.parser import parse_filings_data, save_to_json

# Configure silent execution by routing logs to a file
logging.basicConfig(
    filename="cli.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
FURTHER_ISSUE_CATEGORIES = ("pref", "qip")
ENRICHMENT_CHOICES = ("market-data", "industry", "xbrl")


class LogWriter:
    """Redirects writes to the logger."""

    def __init__(self, level):
        self.level = level

    def write(self, msg):
        for line in msg.rstrip().splitlines():
            if line.strip():
                logger.log(self.level, line.strip())

    def flush(self):
        pass


def validate_date(ctx, param, value):
    if value is None:
        return None
    try:
        _ = datetime.strptime(value, "%d-%m-%Y")
        return value
    except ValueError:
        raise click.BadParameter("Date must be in DD-MM-YYYY format.")


def current_date_str() -> str:
    return datetime.now().strftime("%d-%m-%Y")


def validate_date_range(from_date: str, to_date: str) -> None:
    dt_from = datetime.strptime(from_date, "%d-%m-%Y")
    dt_to = datetime.strptime(to_date, "%d-%m-%Y")
    if dt_from > dt_to:
        raise ValueError(f"from-date {from_date} cannot be after to-date {to_date}")


def execute_silently(
    work: Callable[[Optional[NSEFetcher]], dict[str, Any]],
    *,
    with_fetcher: bool = True,
) -> None:
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = LogWriter(logging.INFO)
    sys.stderr = LogWriter(logging.ERROR)

    result: dict[str, Any] = {}
    fetcher: Optional[NSEFetcher] = None

    try:
        if with_fetcher:
            fetcher = NSEFetcher()
        result = work(fetcher)
    except Exception as e:
        error_msg = f"Execution failed: {e}"
        logger.error(error_msg)
        result = {"error": error_msg}
    finally:
        if fetcher:
            try:
                fetcher.close()
            except Exception:
                pass
        sys.stdout = original_stdout
        sys.stderr = original_stderr

    click.echo(json.dumps(result))


@click.group()
def cli():
    """NSE corporate data CLI."""
    pass


@cli.group("further-issues")
def further_issues():
    """Further-issue filings workflows."""
    pass


@further_issues.command("fetch")
@click.option(
    "--from-date",
    required=True,
    callback=validate_date,
    help="Start date in DD-MM-YYYY format",
)
@click.option(
    "--to-date",
    default=current_date_str,
    show_default="current date",
    callback=validate_date,
    help="End date in DD-MM-YYYY format",
)
@click.option(
    "--category",
    "categories",
    multiple=True,
    default=FURTHER_ISSUE_CATEGORIES,
    show_default=True,
    type=click.Choice(FURTHER_ISSUE_CATEGORIES, case_sensitive=False),
    help="Issue categories to fetch. Repeat the option to include multiple categories.",
)
@click.option(
    "--enrich",
    "enrich",
    multiple=True,
    type=click.Choice(ENRICHMENT_CHOICES, case_sensitive=False),
    help="Optional API enrichments. Repeat the option to include multiple enrichments.",
)
def fetch_further_issues(from_date, to_date, categories, enrich):
    """
    Fetch corporate filings for selected further-issue categories within a date range.

    Returns a JSON object with the status and output details.
    """

    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        assert fetcher is not None
        validate_date_range(from_date, to_date)
        logger.info(
            f"Starting further-issues command for {categories} from {from_date} to {to_date}"
        )

        categories_to_fetch = [category.upper() for category in categories]
        label_maps = {
            "PREF": PREF_API_LABELS,
            "QIP": QIP_API_LABELS,
        }

        output_files = []
        for cat in categories_to_fetch:
            logger.info(f"Fetching data for {cat}")
            filings = fetcher.fetch_corporate_filings(cat, from_date, to_date)
            logger.info(f"Parsing {len(filings)} filings for {cat}")

            parsed_records = parse_filings_data(
                filings=filings,
                fetcher=fetcher,
                symbol_keys=("nseSymbol", "nsesymbol"),
                xbrl_keys=("xmlFileName",),
                api_label_map=label_maps[cat],
                enrichments=enrich,
            )

            output_filename = f"{cat.lower()}_raw.json"
            save_to_json(parsed_records, output_filename)
            logger.info(f"Successfully saved {cat} data to {output_filename}")
            output_files.append(output_filename)

        return {"files": output_files}

    execute_silently(work)


@further_issues.command("refine")
@click.option(
    "--category",
    "category",
    default="pref",
    show_default=True,
    type=click.Choice(FURTHER_ISSUE_CATEGORIES, case_sensitive=False),
    help="Further-issue category to refine.",
)
@click.option(
    "--input",
    "input_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to the full further-issue JSON artifact.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path for the refined further-issue JSON artifact.",
)
def refine_further_issues(
    category: str,
    input_path: Optional[Path],
    output_path: Optional[Path],
):
    """Read a full further-issue artifact and emit a refined JSON."""

    normalized_category = category.lower()
    builders = {
        "pref": (
            build_pref_refined_output,
            Path(DEFAULT_PREF_FULL_OUTPUT),
            Path(DEFAULT_PREF_REFINED_OUTPUT),
            "preferential-issue",
        ),
        "qip": (
            build_qip_refined_output,
            Path(DEFAULT_QIP_FULL_OUTPUT),
            Path(DEFAULT_QIP_REFINED_OUTPUT),
            "QIP",
        ),
    }
    build_refined_output_fn, default_input_path, default_output_path, label = builders[
        normalized_category
    ]
    resolved_input_path = input_path or default_input_path
    resolved_output_path = output_path or default_output_path

    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        del fetcher
        logger.info(
            f"Refining {label} data from {resolved_input_path} to {resolved_output_path}"
        )
        with resolved_input_path.open("r", encoding="utf-8") as handle:
            full_output = json.load(handle)
        refined_output = build_refined_output_fn(full_output)
        save_to_json(refined_output, str(resolved_output_path))
        logger.info(
            f"Successfully saved refined {label} data to {resolved_output_path}"
        )
        return {"files": [str(resolved_output_path)]}

    execute_silently(work, with_fetcher=False)


@cli.group("insider-trading")
def insider_trading():
    """Insider-trading workflows."""
    pass


@insider_trading.command("fetch")
@click.option(
    "--from-date",
    required=True,
    callback=validate_date,
    help="Start date in DD-MM-YYYY format",
)
@click.option(
    "--to-date",
    default=current_date_str,
    show_default="current date",
    callback=validate_date,
    help="End date in DD-MM-YYYY format",
)
@click.option(
    "--enrich",
    "enrich",
    multiple=True,
    type=click.Choice(ENRICHMENT_CHOICES, case_sensitive=False),
    help="Optional API enrichments. Repeat the option to include multiple enrichments.",
)
def fetch_insider_trading(from_date, to_date, enrich):
    """Fetch all insider trading disclosures and normalize the result into JSON."""

    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        assert fetcher is not None
        validate_date_range(from_date, to_date)
        logger.info(f"Starting insider-trading fetch from {from_date} to {to_date}")
        filings = fetcher.fetch_insider_trading(from_date, to_date)

        logger.info(f"Parsing {len(filings)} insider trading filings")
        parsed_records = parse_filings_data(
            filings=filings,
            fetcher=fetcher,
            symbol_keys=("symbol",),
            xbrl_keys=("xbrl",),
            api_label_map=INSIDER_API_LABELS,
            enrichments=enrich,
        )

        output_filename = DEFAULT_INSIDER_FULL_OUTPUT
        save_to_json(parsed_records, output_filename)
        logger.info(f"Successfully saved insider trading data to {output_filename}")
        return {"files": [output_filename]}

    execute_silently(work)


@insider_trading.command("refine")
@click.option(
    "--input",
    "input_path",
    default=DEFAULT_INSIDER_FULL_OUTPUT,
    show_default=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to the full insider-trading JSON artifact.",
)
@click.option(
    "--output",
    "output_path",
    default=DEFAULT_INSIDER_REFINED_OUTPUT,
    show_default=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path for the refined insider-trading JSON artifact.",
)
@click.option(
    "--preset",
    default="market",
    show_default=True,
    type=click.Choice(INSIDER_PRESETS, case_sensitive=False),
    help="Filter records by a signal-focused preset.",
)
def refine_insider_trading(input_path: Path, output_path: Path, preset: str):
    """Read a full insider-trading artifact and emit a refined signal-focused JSON based on a preset."""

    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        del fetcher
        logger.info(
            f"Refining insider-trading data from {input_path} to {output_path} with preset {preset}"
        )
        with input_path.open("r", encoding="utf-8") as handle:
            full_output = json.load(handle)

        filtered_output = filter_insider_filings_by_preset(full_output, preset)
        refined_output = build_insider_refined_output(filtered_output)
        save_to_json(refined_output, str(output_path))

        logger.info(f"Successfully saved refined insider trading data to {output_path}")
        return {"files": [str(output_path)]}

    execute_silently(work, with_fetcher=False)


if __name__ == "__main__":
    cli()
