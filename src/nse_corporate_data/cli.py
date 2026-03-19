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
    DEFAULT_PREF_SHORT_OUTPUT,
    build_pref_short_output,
)
from nse_corporate_data.insider import (
    DEFAULT_INSIDER_FULL_OUTPUT,
    DEFAULT_INSIDER_MODES,
    DEFAULT_INSIDER_SHORT_OUTPUT,
    INSIDER_MODES,
    build_insider_short_output,
    filter_insider_filings_by_mode,
)
from nse_corporate_data.parser import parse_filings_data, save_to_json
from nse_corporate_data.settings import get_settings

# Configure silent execution by routing logs to a file
logging.basicConfig(
    filename="cli.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
FURTHER_ISSUE_CATEGORIES = ("pref", "qip")


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
def fetch_further_issues(from_date, to_date, categories):
    """
    Fetch corporate filings for selected further-issue categories within a date range and parse the XBRL contents.

    Returns a JSON object with the status and output details.
    """
    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        assert fetcher is not None
        validate_date_range(from_date, to_date)
        logger.info(
            f"Starting further-issues command for {categories} from {from_date} to {to_date}"
        )

        categories_to_fetch = [category.upper() for category in categories]

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
                enable_xbrl_processing=True,
            )

            output_filename = f"{cat.lower()}_data.json"
            save_to_json(parsed_records, output_filename)
            logger.info(f"Successfully saved {cat} data to {output_filename}")
            output_files.append(output_filename)

        return {"files": output_files}

    execute_silently(work)


@further_issues.command("shorten")
@click.option(
    "--input",
    "input_path",
    default=DEFAULT_PREF_FULL_OUTPUT,
    show_default=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to the full preferential-issue JSON artifact.",
)
@click.option(
    "--output",
    "output_path",
    default=DEFAULT_PREF_SHORT_OUTPUT,
    show_default=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path for the shortened preferential-issue JSON artifact.",
)
def shorten_further_issues(input_path: Path, output_path: Path):
    """Read a full preferential-issue artifact and emit a shortened JSON."""

    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        del fetcher
        logger.info(f"Shortening preferential-issue data from {input_path} to {output_path}")
        with input_path.open("r", encoding="utf-8") as handle:
            full_output = json.load(handle)
        shortened_output = build_pref_short_output(full_output)
        save_to_json(shortened_output, str(output_path))
        logger.info(
            f"Successfully saved shortened preferential issue data to {output_path}"
        )
        return {"files": [str(output_path)]}

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
    "--mode",
    "modes",
    multiple=True,
    default=DEFAULT_INSIDER_MODES,
    show_default=True,
    type=click.Choice(INSIDER_MODES, case_sensitive=False),
    help=(
        "Filter insider trading records by canonical mode token. "
        "Repeat the option to include multiple modes."
    ),
)
def fetch_insider_trading(from_date, to_date, modes):
    """Fetch insider trading disclosures and normalize the result into JSON."""
    settings = get_settings()

    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        assert fetcher is not None
        validate_date_range(from_date, to_date)
        logger.info(
            f"Starting insider-trading command from {from_date} to {to_date}"
        )
        filings = fetcher.fetch_insider_trading(from_date, to_date)
        filings = filter_insider_filings_by_mode(
            filings, tuple(mode.lower() for mode in modes)
        )
        logger.info(f"Parsing {len(filings)} insider trading filings")
        parsed_records = parse_filings_data(
            filings=filings,
            fetcher=fetcher,
            symbol_keys=("symbol",),
            xbrl_keys=("xbrl",),
            enable_xbrl_processing=settings.enable_insider_trading_xbrl,
        )

        output_filename = DEFAULT_INSIDER_FULL_OUTPUT
        save_to_json(parsed_records, output_filename)
        logger.info(f"Successfully saved insider trading data to {output_filename}")
        return {"files": [output_filename]}

    execute_silently(work)


@insider_trading.command("shorten")
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
    default=DEFAULT_INSIDER_SHORT_OUTPUT,
    show_default=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path for the shortened insider-trading JSON artifact.",
)
def shorten_insider_trading(input_path: Path, output_path: Path):
    """Read a full insider-trading artifact and emit a shortened signal-focused JSON."""

    def work(fetcher: Optional[NSEFetcher]) -> dict[str, Any]:
        del fetcher
        logger.info(f"Shortening insider-trading data from {input_path} to {output_path}")
        with input_path.open("r", encoding="utf-8") as handle:
            full_output = json.load(handle)
        shortened_output = build_insider_short_output(full_output)
        save_to_json(shortened_output, str(output_path))
        logger.info(
            f"Successfully saved shortened insider trading data to {output_path}"
        )
        return {"files": [str(output_path)]}

    execute_silently(work, with_fetcher=False)


if __name__ == "__main__":
    cli()
