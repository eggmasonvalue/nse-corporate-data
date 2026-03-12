import sys
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


# Redirect stdout and stderr to None or a black hole if strictly required,
# but logging to file is usually sufficient if we don't print anything.
# To be completely silent:
class DevNull:
    def write(self, msg):
        pass

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

    This command runs silently. Check cli.log for details, and the resulting JSON files for the output.
    """
    # Silencing standard output/error to ensure it is completely silent per user request
    sys.stdout = DevNull()
    sys.stderr = DevNull()

    try:
        dt_from = datetime.strptime(from_date, "%d-%m-%Y")
        dt_to = datetime.strptime(to_date, "%d-%m-%Y")
        if dt_from > dt_to:
            logger.error(f"from-date {from_date} cannot be after to-date {to_date}")
            return

        logger.info(
            f"Starting fetch command for {category} from {from_date} to {to_date}"
        )

        categories_to_fetch = (
            ["PREF", "QIP"] if category.upper() == "BOTH" else [category.upper()]
        )

        fetcher = NSEFetcher()
        try:
            for cat in categories_to_fetch:
                logger.info(f"Fetching data for {cat}")
                filings = fetcher.fetch_corporate_filings(cat, from_date, to_date)
                logger.info(f"Parsing {len(filings)} filings for {cat}")
                parsed_records = parse_filings_data(cat, filings, fetcher)

                output_filename = f"{cat.lower()}_data.json"
                save_to_json(parsed_records, output_filename)
                logger.info(f"Successfully saved {cat} data to {output_filename}")
        finally:
            fetcher.close()

    except Exception as e:
        logger.error(f"Execution failed: {e}")


if __name__ == "__main__":
    cli()
