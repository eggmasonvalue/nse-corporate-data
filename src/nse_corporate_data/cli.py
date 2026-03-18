import sys
import json
import logging
import click
from datetime import datetime
from typing import Any, Callable

from nse_corporate_data.fetcher import NSEFetcher
from nse_corporate_data.parser import parse_filings_data, save_to_json

# Configure silent execution by routing logs to a file
logging.basicConfig(
    filename="cli.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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


def execute_silently(work: Callable[[NSEFetcher], dict[str, Any]]) -> None:
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = LogWriter(logging.INFO)
    sys.stderr = LogWriter(logging.ERROR)

    result: dict[str, Any] = {}
    fetcher = None

    try:
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


@cli.command()
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
    "--categories",
    default="BOTH",
    show_default=True,
    type=click.Choice(["PREF", "QIP", "BOTH"], case_sensitive=False),
    help="Categories to fetch: PREF, QIP, or BOTH",
)
def further_issues(from_date, to_date, categories):
    """
    Fetch corporate filings for PREF, QIP, or BOTH categories within a date range and parse the XBRL contents.

    Returns a JSON object with the status and output details.
    """
    def work(fetcher: NSEFetcher) -> dict[str, Any]:
        validate_date_range(from_date, to_date)
        logger.info(
            f"Starting further-issues command for {categories} from {from_date} to {to_date}"
        )

        categories_to_fetch = (
            ["PREF", "QIP"] if categories.upper() == "BOTH" else [categories.upper()]
        )

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
            )

            output_filename = f"{cat.lower()}_data.json"
            save_to_json(parsed_records, output_filename)
            logger.info(f"Successfully saved {cat} data to {output_filename}")
            output_files.append(output_filename)

        return {"files": output_files}

    execute_silently(work)


@cli.command("insider-trading")
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
def insider_trading(from_date, to_date):
    """Fetch insider trading disclosures and normalize the result into JSON."""

    def work(fetcher: NSEFetcher) -> dict[str, Any]:
        validate_date_range(from_date, to_date)
        logger.info(
            f"Starting insider-trading command from {from_date} to {to_date}"
        )
        filings = fetcher.fetch_insider_trading(from_date, to_date)
        logger.info(f"Parsing {len(filings)} insider trading filings")
        parsed_records = parse_filings_data(
            filings=filings,
            fetcher=fetcher,
            symbol_keys=("symbol",),
            xbrl_keys=("xbrl",),
        )

        output_filename = "insider_trading_data.json"
        save_to_json(parsed_records, output_filename)
        logger.info(f"Successfully saved insider trading data to {output_filename}")
        return {"files": [output_filename]}

    execute_silently(work)


if __name__ == "__main__":
    cli()
