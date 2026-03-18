import sys
import json
import logging
import click
from datetime import datetime
from further_issue_tracker.fetcher import NSEFetcher
from further_issue_tracker.parser import parse_filings_data, save_to_json

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
    try:
        # Validate format DD-MM-YYYY
        _ = datetime.strptime(value, "%d-%m-%Y")
        return value
    except ValueError:
        raise click.BadParameter("Date must be in DD-MM-YYYY format.")


@click.group()
def cli():
    """Further Issue Tracker CLI."""
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
    required=True,
    callback=validate_date,
    help="End date in DD-MM-YYYY format",
)
@click.option(
    "--category",
    required=True,
    type=click.Choice(["PREF", "QIP", "BOTH"], case_sensitive=False),
    help="Category to fetch: PREF, QIP, or BOTH",
)
def fetch(from_date, to_date, category):
    """
    Fetch corporate filings for PREF, QIP, or BOTH categories within a date range and parse the XBRL contents.

    Returns a JSON object with the status and output details.
    """
    # Redirecting standard output/error to the log file instead of discarding it
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = LogWriter(logging.INFO)
    sys.stderr = LogWriter(logging.ERROR)

    result = {}
    fetcher = None

    try:
        dt_from = datetime.strptime(from_date, "%d-%m-%Y")
        dt_to = datetime.strptime(to_date, "%d-%m-%Y")
        if dt_from > dt_to:
            result["error"] = f"from-date {from_date} cannot be after to-date {to_date}"
            return

        logger.info(
            f"Starting fetch command for {category} from {from_date} to {to_date}"
        )

        categories_to_fetch = (
            ["PREF", "QIP"] if category.upper() == "BOTH" else [category.upper()]
        )

        output_files = []
        fetcher = NSEFetcher()
        for cat in categories_to_fetch:
            logger.info(f"Fetching data for {cat}")
            filings = fetcher.fetch_corporate_filings(cat, from_date, to_date)
            logger.info(f"Parsing {len(filings)} filings for {cat}")
            parsed_records = parse_filings_data(cat, filings, fetcher)

            output_filename = f"{cat.lower()}_data.json"
            save_to_json(parsed_records, output_filename)
            logger.info(f"Successfully saved {cat} data to {output_filename}")
            output_files.append(output_filename)

        result["files"] = output_files

    except Exception as e:
        error_msg = f"Execution failed: {e}"
        logger.error(error_msg)
        result["error"] = error_msg

    finally:
        if fetcher:
            try:
                fetcher.close()
            except Exception:
                pass
        sys.stdout = original_stdout
        sys.stderr = original_stderr

    click.echo(json.dumps(result))


if __name__ == "__main__":
    cli()
