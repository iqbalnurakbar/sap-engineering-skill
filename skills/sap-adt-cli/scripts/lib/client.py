from typing import Optional

import requests
import urllib3
from requests.auth import HTTPBasicAuth

from .config import SapConfig, get_config

_session: Optional[requests.Session] = None
_csrf_token: Optional[str] = None
_session_cookies: Optional[dict] = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def _auth_headers(config: SapConfig) -> dict:
    # Send the SAP client as both the X-SAP-Client header and the sap-client
    # URL parameter. Some SAP setups (Web Dispatcher, ICF configuration)
    # only honor the URL parameter, in which case sending only the header
    # results in HTTP 403 SADT_RESOURCE 003 without any AUTHORITY-CHECK
    # trace on the backend. Sending both is safe and portable.
    return {"X-SAP-Client": config.client}


def _client_query_params(config: SapConfig, existing: Optional[dict] = None) -> dict:
    params = dict(existing) if existing else {}
    params.setdefault("sap-client", config.client)
    return params


def _fetch_csrf_token(url: str, config: SapConfig) -> str:
    global _session_cookies
    resp = _get_session().get(
        url,
        auth=HTTPBasicAuth(config.username, config.password),
        headers={**_auth_headers(config), "x-csrf-token": "fetch"},
        params=_client_query_params(config),
        verify=config.verify_ssl,
        timeout=30,
    )
    token = resp.headers.get("x-csrf-token")
    if not token:
        raise RuntimeError("No CSRF token received from SAP server")
    if resp.cookies:
        _session_cookies = dict(resp.cookies)
    return token


def make_adt_request(
    url: str,
    method: str = "GET",
    timeout: int = 30,
    data=None,
    params: Optional[dict] = None,
    extra_headers: Optional[dict] = None,
) -> requests.Response:
    global _csrf_token, _session_cookies

    config = get_config()
    headers = _auth_headers(config)
    if extra_headers:
        headers.update(extra_headers)

    if not config.verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if method in ("POST", "PUT") and not _csrf_token:
        _csrf_token = _fetch_csrf_token(url, config)

    if method in ("POST", "PUT") and _csrf_token:
        headers["x-csrf-token"] = _csrf_token

    def _do() -> requests.Response:
        return _get_session().request(
            method=method,
            url=url,
            auth=HTTPBasicAuth(config.username, config.password),
            headers=headers,
            verify=config.verify_ssl,
            timeout=timeout,
            data=data,
            params=_client_query_params(config, params),
            cookies=_session_cookies or {},
        )

    resp = _do()

    if resp.status_code == 403 and "CSRF" in (resp.text or ""):
        _csrf_token = _fetch_csrf_token(url, config)
        headers["x-csrf-token"] = _csrf_token
        resp = _do()

    resp.raise_for_status()
    return resp
