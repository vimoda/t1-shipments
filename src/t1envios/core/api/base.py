from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any

import httpx

from ..exceptions import ApiError, AuthError, RateLimitError

if TYPE_CHECKING:
    from ..auth.authenticator import Authenticator
    from ..config import Endpoints

log = logging.getLogger("t1envios.api")


class BaseResource:
    def __init__(
        self,
        http: httpx.Client,
        auth: "Authenticator",
        endpoints: "Endpoints",
        shop_id: str | None = None,
        commerce_id: str | None = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self._http = http
        self._auth = auth
        self._endpoints = endpoints
        self._shop_id = shop_id
        self._commerce_id = commerce_id
        self._retries = retries
        self._retry_delay = retry_delay

    def request(
        self,
        method: str,
        url: str,
        *,
        retry_on_401: bool = True,
        **kwargs: Any,
    ) -> Any:
        headers = kwargs.pop("headers", {})

        for attempt in range(max(self._retries, 1)):
            try:
                token = self._auth.ensure_valid()
                headers["Authorization"] = f"Bearer {token.access_token}"
                if self._shop_id:
                    headers["shop_id"] = self._shop_id

                log.debug("%s %s", method, url)
                if log.isEnabledFor(logging.DEBUG):
                    body = kwargs.get("json")
                    body_str = json.dumps(body, ensure_ascii=False) if body else ""
                    curl_headers = " \\\n".join(
                        f"  -H '{k}: {v}'" for k, v in headers.items()
                    )
                    curl = (
                        f"curl -s -X {method} '{url}'"
                        + (f" \\\n{curl_headers}" if curl_headers else "")
                        + (f" \\\n  -H 'Content-Type: application/json'" if body else "")
                        + (f" \\\n  -d '{body_str}'" if body_str else "")
                    )
                    log.debug("curl:\n%s", curl)
                req = self._http.build_request(method, url, headers=headers, **kwargs)
                resp = self._http.send(req)
                log.debug("→ %s", resp.status_code)
                if log.isEnabledFor(logging.DEBUG) and resp.content:
                    log.debug("← body: %s", resp.text[:2000])

                if resp.status_code == 401 and retry_on_401 and self._auth.auto_refresh:
                    log.warning("401 received, refreshing token and retrying")
                    token = self._auth.refresh()
                    headers["Authorization"] = f"Bearer {token.access_token}"
                    req = self._http.build_request(method, url, headers=headers, **kwargs)
                    resp = self._http.send(req)
                    log.debug("→ %s (after token refresh)", resp.status_code)

                if 500 <= resp.status_code < 600 and attempt < self._retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    log.warning("5xx (%s) on attempt %d, retrying in %.1fs", resp.status_code, attempt + 1, delay)
                    time.sleep(delay)
                    continue

                self._raise_for_status(resp)
                return resp.json() if resp.content else None

            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                if attempt < self._retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    log.warning("%s on attempt %d, retrying in %.1fs", type(exc).__name__, attempt + 1, delay)
                    time.sleep(delay)
                else:
                    raise

        raise RuntimeError("retry loop exhausted without returning")  # unreachable

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return

        if resp.status_code == 401:
            raise AuthError(f"Unauthorized [{resp.status_code}]: {resp.text}")

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        message = resp.text
        code = None
        try:
            body = resp.json()
            message = body.get("message") or body.get("error") or message
            code = body.get("code")
        except Exception:
            pass

        raise ApiError(status=resp.status_code, message=message, code=code, payload=resp.text)
