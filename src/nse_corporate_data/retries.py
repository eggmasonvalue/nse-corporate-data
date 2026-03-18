import logging
import re
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Retry configuration
TOTAL_RETRIES = 10
RETRY_MIN_DELAY = 1  # Minimum delay in seconds
RETRY_MAX_DELAY = 30  # Maximum delay in seconds
RETRY_MULTIPLIER = 2  # Multiplier for exponential backoff

# Status codes to retry
RETRY_STATUS_CODES = {408, 429, 502, 503, 504}


def should_retry_exception(exception: Exception) -> bool:
    """
    Predicate to determine if an exception should trigger a retry.
    """
    if isinstance(exception, TimeoutError):
        return True

    # Also handle standard exception messages containing status codes,
    # because sometimes httpx or requests wrap them differently.
    msg = str(exception)

    # Check for status codes in the message
    for code in RETRY_STATUS_CODES:
        if re.search(rf"\b{code}\b", msg):
            return True

    if isinstance(exception, ConnectionError):
        return False  # Covered by above check if status code matches

    return False


def get_retry_decorator():
    """
    Returns a configured tenacity retry decorator.
    """
    return retry(
        stop=stop_after_attempt(TOTAL_RETRIES),
        wait=wait_random_exponential(
            multiplier=RETRY_MULTIPLIER, min=RETRY_MIN_DELAY, max=RETRY_MAX_DELAY
        ),
        retry=retry_if_exception(should_retry_exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )


# Export a ready-to-use decorator
retry_exchange = get_retry_decorator()
