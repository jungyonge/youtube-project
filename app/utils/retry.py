import httpx
from loguru import logger
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)


def _log_before_retry(retry_state: RetryCallState) -> None:
    fn_name = getattr(retry_state.fn, "__name__", "unknown")
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "Retry {}/{} for {}(): {}",
        attempt,
        retry_state.retry_object.stop.max_attempt_number,  # type: ignore[union-attr]
        fn_name,
        exc,
    )


retry_api_call = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=16),
    retry=retry_if_exception_type((
        TimeoutError,
        ConnectionError,
        httpx.HTTPStatusError,
        httpx.ConnectError,
        httpx.ReadTimeout,
    )),
    before_sleep=_log_before_retry,
    reraise=True,
)

retry_network = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((
        TimeoutError,
        ConnectionError,
        OSError,
        httpx.ConnectError,
        httpx.ReadTimeout,
    )),
    before_sleep=_log_before_retry,
    reraise=True,
)
