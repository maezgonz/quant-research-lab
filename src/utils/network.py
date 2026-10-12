import logging
import requests
from src.core.constants import DEFAULT_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)

_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=MAX_RETRIES,
            pool_connections=10,
            pool_maxsize=20,
        )
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    return _session


def request(method: str, url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    return get_session().request(method, url, **kwargs)


def get(url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    return get_session().get(url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    return get_session().post(url, **kwargs)


def get_insecure(url: str, **kwargs) -> requests.Response:
    """GET con SSL verification desactivado para APIs argentinas con certificados vencidos."""
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    kwargs["verify"] = False
    logger.warning("SSL verify=False: %s", url)
    return get_session().get(url, **kwargs)
